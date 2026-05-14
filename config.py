"""Clinical ITSM Agent — Configuration."""

import os
from pydantic_settings import BaseSettings


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

    # Observability
    applicationinsights_connection_string: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
