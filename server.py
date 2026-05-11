"""CCAD ITSD Agent — FastAPI server."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from agent import create_agent
from config import settings

_agent = None
_sessions: dict[str, object] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage agent lifecycle (MCP connections)."""
    global _agent
    _agent = create_agent()
    async with _agent:
        yield
    _agent = None


app = FastAPI(
    title="CCAD ITSD Agent",
    version="0.1.0",
    lifespan=lifespan,
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
