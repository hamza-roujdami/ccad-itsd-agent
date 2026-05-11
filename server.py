"""CCAD ITSD Agent — FastAPI server.

Endpoints:
  POST /chat          — Simple JSON chat (for testing / API consumers)
  POST /ag-ui         — AG-UI protocol (SSE streaming, for CopilotKit / web UI)
  GET  /health        — Health check
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import create_agent
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint
from config import settings

_agent = None
_sessions: dict[str, object] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage agent lifecycle (MCP connections)."""
    global _agent
    _agent = create_agent()
    async with _agent:
        # Register AG-UI endpoint once agent + MCP are ready
        add_agent_framework_fastapi_endpoint(app, _agent, "/ag-ui")
        yield
    _agent = None


app = FastAPI(
    title="CCAD ITSD Agent",
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

    return ChatResponse(reply=result.text, session_id=session_id)


def _new_session_id() -> str:
    import uuid
    return str(uuid.uuid4())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=True)
