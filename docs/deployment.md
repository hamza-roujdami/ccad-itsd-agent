# Deployment Guide

## Prerequisites

- Azure CLI (`az login`)
- Python 3.11+
- Node.js 18+ (for frontend)
- Access to Azure subscription with:
  - Azure AI Foundry (GPT-4o deployment)
  - Azure AI Search
  - Azure Cosmos DB
  - Azure Key Vault
  - Azure App Insights

## 1. Deploy Azure Infrastructure

```bash
az deployment group create \
  --resource-group rg-clinical-itsm-dev \
  --template-file infra/main.bicep \
  --parameters infra/main.bicepparam
```

This provisions: AI Foundry + GPT-4o, AI Search, Cosmos DB (serverless), Key Vault, App Insights.

### Get outputs for .env

```bash
az deployment group show \
  --resource-group rg-clinical-itsm-dev \
  --name main \
  --query properties.outputs -o json
```

## 2. Configure Environment

```bash
cp .env.example .env
# Fill in values from Bicep outputs:
#   FOUNDRY_PROJECT_ENDPOINT
#   AZURE_SEARCH_ENDPOINT
#   COSMOS_ENDPOINT
#   APPLICATIONINSIGHTS_CONNECTION_STRING
```

## 3. Index the Knowledge Base

```bash
cd src && ../.venv/bin/python3 -m kb.index_kb
```

## 4. Run Locally

### Terminal 1 — Mock MCP server

```bash
cd src && ../.venv/bin/python3 -m mock_mcp.server
```

### Terminal 2 — Agent API

```bash
cd src && ../.venv/bin/python3 -c "import uvicorn; uvicorn.run('server:app', host='0.0.0.0', port=8000, reload=False)"
```

### Terminal 3 — Chat UI

```bash
cd frontend && npm install && REACT_APP_API_URL=http://localhost:8000 npm start
```

Open http://localhost:3000

## 5. Run Eval Tests

```bash
# Requires: agent server on :8000 + mock MCP on :8001
.venv/bin/python3 -m pytest tests/test_eval.py -v
```

## 6. Connect to Production MCP

Set in `.env`:
```env
MCP_SERVER_URL=https://apim-uaen-uatai-001.azure-api.net/manage-engine-mcp/mcp
APIM_SUBSCRIPTION_KEY=your-key
```

Restart the agent server. It will connect to the real ManageEngine MCP via APIM.

## 7. Enable Monitoring

Set in `.env`:
```env
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=https://xxx
```

View traces: Azure Portal → App Insights → Agents (Preview)

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Yes | — | Azure AI Foundry endpoint |
| `FOUNDRY_MODEL` | No | `gpt-4o` | Model deployment name |
| `AZURE_SEARCH_ENDPOINT` | Yes | — | Azure AI Search endpoint |
| `AZURE_SEARCH_INDEX_NAME` | No | `itsd-kb` | Search index name |
| `MCP_SERVER_URL` | No | `http://localhost:8001/mcp` | ManageEngine MCP endpoint |
| `APIM_SUBSCRIPTION_KEY` | No | — | APIM key for production MCP |
| `COSMOS_ENDPOINT` | No | — | Cosmos DB endpoint (empty = file-based history) |
| `COSMOS_DATABASE` | No | `agent-framework` | Cosmos DB database name |
| `COSMOS_CONTAINER` | No | `chat-history` | Cosmos DB container name |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | No | — | App Insights (empty = no telemetry) |
| `ACS_CONNECTION_STRING` | No | — | Azure Communication Services (voice channel) |
| `ACS_CALLBACK_BASE_URL` | No | — | Public URL for ACS webhooks |
| `ACS_COGNITIVE_SERVICES_ENDPOINT` | No | — | AI Services for STT/TTS |
