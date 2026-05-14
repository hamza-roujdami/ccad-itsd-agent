"""Clinical ITSM Agent — FastAPI server.

Endpoints:
  POST /chat          — JSON chat (for testing / API consumers)
  GET  /health        — Health check
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import create_agent
from config import settings

logger = logging.getLogger(__name__)

_agent = None
_history_provider = None
_sessions: dict[str, object] = {}


def _create_history_provider():
    """Create history provider: Cosmos DB if configured, else FileHistoryProvider."""
    if settings.cosmos_endpoint:
        from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
        from agent_framework_azure_cosmos import CosmosHistoryProvider
        logger.info("Using CosmosHistoryProvider (%s)", settings.cosmos_endpoint)
        return CosmosHistoryProvider(
            endpoint=settings.cosmos_endpoint,
            credential=AsyncDefaultAzureCredential(),
            database_name=settings.cosmos_database,
            container_name=settings.cosmos_container,
        )
    else:
        from agent_framework import FileHistoryProvider
        logger.info("Using FileHistoryProvider (./conversations)")
        return FileHistoryProvider(storage_path="./conversations")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage agent lifecycle (MCP connections)."""
    global _agent, _history_provider
    _history_provider = _create_history_provider()
    _agent = create_agent(history_provider=_history_provider)
    async with _agent:
        yield
    _agent = None


app = FastAPI(
    title="Clinical ITSM Agent",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for web UI clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tools_used: list[str] = []


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the ITSD agent."""
    # Get or create session for multi-turn
    session_id = req.session_id or _new_session_id()
    if session_id not in _sessions:
        _sessions[session_id] = _agent.create_session()

    session = _sessions[session_id]

    result = await _agent.run(req.message, session=session)

    # Extract tool names from result messages
    tools_used = []
    try:
        for msg in result.messages:
            if msg.contents:
                for c in msg.contents:
                    if hasattr(c, 'type') and c.type == 'function_call' and hasattr(c, 'name') and c.name:
                        name = c.name
                        if name == "search_kb":
                            tools_used.append("Clinical Knowledge Base")
                        elif name.startswith("ManageEngine_") or name in (
                            "createRequest", "requestDetailsById", "updateRequest", "addNote",
                            "viewAllRequests", "viewAllPriorities", "viewAllStatuses",
                            "viewAllCategories", "viewAllSupportGroups", "viewAllModes",
                            "viewAllImpacts", "viewAllUrgencies", "viewAllSolutions",
                            "viewAllRequestFilters", "getServiceTemplates", "getUserDetails"):
                            tools_used.append("Clinical ManageEngine")
                        else:
                            tools_used.append(name)
    except Exception:
        pass

    return ChatResponse(reply=result.text, session_id=session_id, tools_used=list(dict.fromkeys(tools_used)))


def _new_session_id() -> str:
    import uuid
    return str(uuid.uuid4())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=True)
