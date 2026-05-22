"""Clinical ITSM Agent — Configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings

# .env lives at project root (one level up from src/)
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # Azure AI Foundry
    foundry_project_endpoint: str = ""
    foundry_model: str = "gpt-4o"

    # Azure AI Search (KB)
    azure_search_endpoint: str = ""
    azure_search_index_name: str = "itsd-kb"

    # ManageEngine MCP Server
    mcp_server_url: str = "http://localhost:8001/mcp"  # local mock by default

    # APIM (for production MCP access)
    apim_subscription_key: str = ""

    # Cosmos DB (conversation history)
    cosmos_endpoint: str = ""
    cosmos_database: str = "agent-framework"
    cosmos_container: str = "chat-history"

    # Azure Communication Services (telephony)
    acs_connection_string: str = ""
    acs_callback_base_url: str = ""  # Public URL for ACS webhooks (e.g. dev tunnel)
    acs_cognitive_services_endpoint: str = ""  # AI Services endpoint for STT/TTS in calls

    # Observability
    applicationinsights_connection_string: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
