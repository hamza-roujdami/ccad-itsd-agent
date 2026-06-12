# Backend Dockerfile for the Clinical ITSM Agent.
# Build context = repo root (needs src/ and skills/).
# Single image runs either the FastAPI server (default) or the mock MCP server
# (command overridden in Container Apps sidecar).

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install runtime dependencies (mirrors pyproject.toml [project].dependencies
# plus Azure Monitor exporter for App Insights telemetry).
RUN pip install --upgrade pip && pip install \
    "agent-framework-core>=1.3.0" \
    "agent-framework-foundry>=1.3.0" \
    "agent-framework-azure-ai-search>=1.0.0b1" \
    "mcp>=1.24.0" \
    "fastapi>=0.115" \
    "uvicorn>=0.30" \
    "pydantic>=2.0" \
    "pydantic-settings>=2.0" \
    "azure-identity>=1.17" \
    "aiohttp>=3.9" \
    "python-dotenv>=1.0" \
    "azure-communication-callautomation>=1.4.0" \
    "azure-monitor-opentelemetry-exporter>=1.0.0b30"

# Application code. skills/ now lives inside src/, so a single COPY brings the
# agent code and its skills. agent.py resolves skills via Path(__file__).parent/"skills".
COPY src ./src

WORKDIR /app/src

EXPOSE 8000

# Default: FastAPI server.
# NOTE: the mock MCP server now lives in tests/fixtures/mock_mcp (dev-only) and is
# NOT included in this image. For the optional ACA mock sidecar, copy it in or
# point MCP_SERVER_URL at the real ManageEngine MCP endpoint.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
