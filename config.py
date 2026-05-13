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

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
