# Clinical ITSM Agent

An AI-powered IT Service Management agent for **clinical / hospital environments**. Built with the [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) (Python), GPT-4o (via Azure AI Foundry), and ManageEngine ServiceDesk Plus via MCP.

## What it does

The agent acts as the **first line of IT support** for clinicians, nurses, and staff:

1. **Understands the issue** — parses natural language IT requests and asks clarifying questions
2. **Searches the knowledge base first** — looks up troubleshooting guides and FAQs before creating tickets
3. **Creates and manages tickets intelligently** — classifies priority, category, and resolver group using the hospital's ITSM taxonomy
4. **Escalates with full context** — when self-service fails, creates a ticket with conversation summary so human resolvers can pick up seamlessly
5. **Routes non-IT requests** — directs HR, Facilities, and Operations questions to the right contact

## Architecture

```mermaid
graph LR
    classDef channel fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef platform fill:#FFF8E1,stroke:#F9A825,stroke-width:2px,color:#795548
    classDef agent fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef azure fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B
    classDef tool fill:#FCE4EC,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef llm fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px,color:#4A148C

    Users["👥 Users<br/>(Clinicians, Nurses,<br/>Doctors, IT Staff)"]

    subgraph Channels["User Channels"]
        direction TB
        Phone["📞 Phone Call<br/>(Azure Communication Services)"]
        Teams["💬 Microsoft Teams"]
        WhatsApp["📱 WhatsApp (Twilio)"]
        WebUI["🌐 Web UI (React SPA)"]
    end

    subgraph Platform["Azure Container Apps"]
        direction TB
        FastAPI["⚡ FastAPI Gateway<br/>(Uvicorn)"]
    end

    subgraph AgentLayer["Agent Orchestrator (MAF)"]
        direction TB
        Orchestrator["🤖 ITSD Supervisor Agent<br/>(Microsoft Agent Framework)"]
    end

    subgraph LLMLayer["LLM Provider"]
        direction TB
        APIM_AI["☁️ Azure APIM<br/>(AI Gateway)"]
        GPT4o["🧠 GPT-4o<br/>(Azure AI Foundry)"]
    end

    subgraph Tools["Agent Tools & Services"]
        direction TB
        SearchKB["🔍 search_kb<br/>(Native Tool)"]
        AssessPri["⚖️ assess_priority<br/>(Priority Verification)"]
        MCPTools["🔧 ManageEngine MCP Tools<br/>(17 tools)"]
    end

    subgraph BackendSvcs["Backend Services"]
        direction TB
        AIS["📚 Azure AI Search<br/>(IT Knowledge Base)"]
        APIM_ME["☁️ Azure APIM<br/>(ME Gateway)"]
        ME["🎫 ManageEngine<br/>ServiceDesk Plus"]
    end

    subgraph Infra["Observability & Security"]
        direction TB
        Monitor["📊 Azure Monitor<br/>& App Insights"]
        KV["🔐 Azure Key Vault"]
        ManagedID["🆔 Managed Identity"]
    end

    Users --> Channels
    Phone --> FastAPI
    Teams --> FastAPI
    WhatsApp --> FastAPI
    WebUI --> FastAPI
    FastAPI --> Orchestrator
    Orchestrator --> APIM_AI
    APIM_AI --> GPT4o
    Orchestrator --> SearchKB
    Orchestrator --> AssessPri
    Orchestrator --> MCPTools
    SearchKB --> AIS
    MCPTools --> APIM_ME
    APIM_ME --> ME
    FastAPI -.-> Monitor
    Orchestrator -.-> Monitor
    Orchestrator -.-> KV
    Orchestrator -.-> ManagedID

    class Phone,Teams,WhatsApp,WebUI channel
    class FastAPI platform
    class Orchestrator agent
    class APIM_AI,GPT4o llm
    class SearchKB,AssessPri,MCPTools,AIS,APIM_ME,ME tool
    class Monitor,KV,ManagedID azure
```

### Agent Internals — Skills, Tools & MCP

```mermaid
graph TB
    classDef prompt fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef tool fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef skill fill:#FFF8E1,stroke:#F9A825,stroke-width:2px,color:#795548
    classDef resource fill:#FFF3E0,stroke:#E65100,stroke-width:1px,color:#BF360C
    classDef external fill:#FCE4EC,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef history fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px,color:#4A148C

    User["💬 User Message"]

    subgraph Agent["Clinical ITSM Agent (MAF)"]
        direction TB
        Prompt["📋 System Prompt<br/>(slim ~400 tokens)<br/>6-step workflow"]
        LLM["🧠 GPT-4o<br/>(Azure AI Foundry)"]
    end

    subgraph ToolsLayer["Native Tools"]
        direction TB
        SearchKB["🔍 search_kb<br/>Azure AI Search<br/>(33 KB articles)"]
        AssessPri["⚖️ assess_priority<br/>Multi-signal scoring<br/>(user × matrix × text)"]
    end

    subgraph SkillsLayer["Skills (on-demand via SkillsProvider)"]
        direction TB

        subgraph S1["ticket-creation"]
            direction TB
            SK1["📄 SKILL.md<br/>Ticket workflow +<br/>mandatory fields"]
            R1["📎 categories.md"]
            R2["📎 resolver-groups.md"]
            R3["📎 business-rules.md"]
        end

        subgraph S2["clinical-triage"]
            direction TB
            SK2["📄 SKILL.md<br/>Decision tree:<br/>Equipment / Epic /<br/>Non-Epic Apps"]
        end

        subgraph S3["ticket-management"]
            direction TB
            SK3["📄 SKILL.md<br/>Status, notes,<br/>updates, listing"]
        end

        subgraph S4["non-it-routing"]
            direction TB
            SK4["📄 SKILL.md<br/>HR / Facilities /<br/>Operations contacts"]
        end
    end

    subgraph MCPLayer["MCP Tools (ManageEngine)"]
        direction TB
        MCP["🔧 MCPStreamableHTTPTool<br/>(17 tools via APIM)"]
        CR["createRequest"]
        RD["requestDetailsById"]
        AN["addNote"]
        UR["updateRequest"]
        VR["viewAllRequests"]
        VC["viewAllCategories"]
    end

    subgraph HistoryLayer["Conversation History"]
        direction TB
        HP["📚 HistoryProvider<br/>CosmosDB (prod)<br/>FileHistory (dev)"]
    end

    User --> Prompt
    Prompt --> LLM
    LLM --> SearchKB
    LLM --> AssessPri
    LLM -->|"load_skill"| S1
    LLM -->|"load_skill"| S2
    LLM -->|"load_skill"| S3
    LLM -->|"load_skill"| S4
    SK1 -->|"read_skill_resource"| R1
    SK1 -->|"read_skill_resource"| R2
    SK1 -->|"read_skill_resource"| R3
    LLM --> MCP
    MCP --> CR
    MCP --> RD
    MCP --> AN
    MCP --> UR
    MCP --> VR
    MCP --> VC
    LLM -.-> HP

    class Prompt prompt
    class SearchKB,AssessPri tool
    class SK1,SK2,SK3,SK4 skill
    class R1,R2,R3 resource
    class MCP,CR,RD,AN,UR,VR,VC external
    class HP history
```

### Data Flow

1. User contacts via any channel (Phone, Teams, WhatsApp, Web UI) → hits **FastAPI gateway** on Azure Container Apps
2. Gateway routes to the **ITSD Supervisor Agent** (Microsoft Agent Framework)
3. Agent calls **GPT-4o** through **Azure AI Foundry** for reasoning
4. Agent uses `search_kb` → **Azure AI Search** to find KB articles first (KB-first triage)
5. Only if KB fails → Agent loads the `ticket-creation` **skill** on-demand (categories, groups, business rules)
6. Agent calls `assess_priority` for deterministic multi-signal priority scoring (user input × impact/urgency matrix × text analysis)
7. Agent uses MCP tools → **APIM** → **ManageEngine ServiceDesk Plus** to create/manage tickets with verified priority
8. All calls instrumented via **Azure Monitor & App Insights**

> **Skills (progressive disclosure):** Business rules, categories, and resolver groups are loaded on-demand via MAF `SkillsProvider` — only when the agent needs to create or manage tickets. KB-only queries skip loading skills entirely, saving ~800 tokens per request.

## Tech stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) (Python) v1.6.0 |
| MAF: Agent | `Agent` — single-agent with tools and context providers |
| MAF: MCP Client | `MCPStreamableHTTPTool` — connects to ManageEngine MCP server via HTTP |
| MAF: Skills | `SkillsProvider` — progressive disclosure of business rules via `SKILL.md` files |
| MAF: LLM Client | `FoundryChatClient` — connects to GPT-4o via Azure AI Foundry |
| MAF: History | `CosmosHistoryProvider` (prod) / `FileHistoryProvider` (dev) — persistent conversation history |
| MAF: DevUI | `agent_framework.devui` — local debug UI with tool-call visibility |
| LLM | GPT-4o via Azure AI Foundry |
| Knowledge Base | Azure AI Search (semantic search, 33 KB articles) |
| Ticketing | ManageEngine ServiceDesk Plus via MCP (APIM gateway, 17 tools) |
| Conversation Store | Azure Cosmos DB NoSQL (serverless) — falls back to local JSON files |
| API | FastAPI + Uvicorn |
| Observability | OpenTelemetry via MAF `configure_otel_providers()` → Azure App Insights |
| Eval | pytest test suite covering all agent flows |
| Auth | Azure Identity (`DefaultAzureCredential`) |
| Infra | Bicep (`infra/`) |

## Quick start

### Prerequisites

- Python 3.11+
- Azure CLI logged in (`az login`) with access to:
  - LLM endpoint (Azure AI Foundry with GPT-4o)
  - Azure AI Search (with `itsd-kb` index populated)

### Setup

```bash
git clone https://github.com/hamza-roujdami/ccad-itsd-agent.git
cd ccad-itsd-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,mock]"
```

### Configure

Copy `.env.example` to `.env` and fill in your Azure endpoints:

```bash
cp .env.example .env
```

```env
FOUNDRY_PROJECT_ENDPOINT=https://<your-ai-services>.cognitiveservices.azure.com/
FOUNDRY_MODEL=gpt-4o
AZURE_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
AZURE_SEARCH_INDEX_NAME=itsd-kb
MCP_SERVER_URL=http://localhost:8001/mcp
```

### Index the knowledge base

Populate the Azure AI Search index with the 33 KB articles:

```bash
cd src && python3 -m kb.index_kb
```

### Run (local development)

Terminal 1 — start the mock MCP server (ManageEngine substitute):

```bash
python3 -m tests.fixtures.mock_mcp.server
```

Terminal 2 — start the agent API:

```bash
cd src && python3 -c "import uvicorn; uvicorn.run('server:app', host='0.0.0.0', port=8000)"
```

**Or use MAF DevUI** (recommended for testing — shows tool calls, streaming, agent metadata):

```bash
cd src && python3 devui_app.py
# Opens http://localhost:8080
```

Terminal 3 — start the React chat UI (optional, alternative to DevUI):

```bash
cd frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

Open **http://localhost:3000** (React UI) or **http://localhost:8080** (DevUI).

### Test via UI

The chat UI shows which tool was used for each response:

- **Clinical Knowledge Base** — answered from KB articles (no ticket created)
- **Clinical ManageEngine** — ticket created/read/updated via ManageEngine MCP
- **Clinical_ITSM_AGENT** — no tools used (greetings, clarifying questions, non-IT routing)

Try these prompts:

```
How do I reset my password?                    → KB answer, no ticket
My laptop screen is cracked                    → asks clarifying questions
Epic is down for the whole department          → creates urgent ticket
How do I apply for annual leave?               → redirects to HR
Can you check the status of ticket 32203?      → reads ticket from ManageEngine
```

### Test via curl

```bash
# Health check
curl http://localhost:8000/health

# Chat — KB question (no ticket created)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'

# Chat — Issue requiring ticket
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Epic Hyperspace is down for the entire cardiology department"}'
```

## API

### `POST /chat`

```json
{
  "message": "My printer is not working",
  "session_id": "optional-for-multi-turn"
}
```

Response:
```json
{
  "reply": "I found some troubleshooting steps...",
  "session_id": "uuid"
}
```

### `GET /health`

Returns `{"status": "ok"}`.

## Monitoring & Observability

The agent emits OpenTelemetry traces (GenAI semantic conventions) to **Azure Application Insights**.

### Setup

Set the connection string in `.env`:

```env
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=https://xxx
```

The server auto-configures Azure Monitor exporters (traces, metrics, logs) on startup.

### What you see in App Insights

Navigate to **Azure Portal → App Insights → Agents (Preview)**:

- **Agent Runs** — total invocations, success rate, response time trends
- **Tool Calls** — which tools were called (`search_kb`, `assess_priority`, `createRequest`, `load_skill`), call count, latency, errors
- **Models** — GPT-4o token usage, avg duration, call count
- **Gen AI Errors** — failed LLM or tool calls
- **Transaction Search** — drill into individual agent runs with end-to-end trace view
- **Grafana dashboards** — pre-built Agent Framework dashboards available via "Explore in Grafana"

### Running eval tests

```bash
# Requires: agent server on :8000 + mock MCP on :8001
python -m pytest tests/test_eval.py -v
```

Automated tests covering KB resolution, non-IT routing, priority verification, ticket creation, ticket management, and multi-turn conversations.

## KB content

33 articles covering: Cisco Phone, Printing, Epic, Passwords, VPN, VDI, MFA, MS Teams, Intune, PowerMic, Email, Monitors, and more. See [`src/kb/README.md`](src/kb/README.md).

## Voice Architecture

End-to-end call flow from PSTN through the clinical voice network to the AI agent and back.

```mermaid
flowchart LR
    classDef pstn fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef azure fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B
    classDef agent fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef tool fill:#FCE4EC,stroke:#C62828,stroke-width:2px,color:#B71C1C

    subgraph PSTN["PSTN & Voice Network"]
        direction TB
        Caller["📞 User / Caregiver"]
        CUCM["Cisco CUCM"]
        SBC["Ribbon SBC v12.3"]
        Caller <--> CUCM <--> SBC
    end

    subgraph ACSLayer["Azure Communication Services"]
        direction TB
        ACS["☁️ ACS"]
        CallAuto["🎙️ Call Automation"]
        ACS <--> CallAuto
    end

    subgraph Speech["Azure Speech"]
        direction TB
        STT["🗣️→📝 Speech-to-Text"]
        TTS["📝→🔊 Text-to-Speech"]
    end

    subgraph AgentLayer["ITSD Agent"]
        direction TB
        Agent["🤖 Agent Backend"]
        KB["🔍 Knowledge Base"]
        MCP["🔧 ManageEngine MCP"]
        Agent --> KB
        Agent --> MCP
    end

    SBC <-->|"SIP"| ACS
    CallAuto -->|"audio stream"| STT
    STT -->|"transcript"| Agent
    Agent -->|"response text"| TTS
    TTS -->|"audio"| CallAuto

    class Caller,CUCM,SBC pstn
    class ACS,CallAuto azure
    class STT,TTS azure
    class Agent agent
    class KB,MCP tool
```

> **Loop**: caller speaks → STT transcribes → agent reasons (KB lookup or MCP action) → TTS synthesizes → caller hears response. Repeats until conversation ends.

## Project structure

```
clinical-itsm-agent/
├── README.md
├── pyproject.toml
├── .env.example
├── Dockerfile
│
├── src/                   ← Python package (the agent backend)
│   ├── agent.py           ← Agent definition (slim prompt, tools, skills, MCP)
│   ├── server.py          ← FastAPI server (/chat, /health)
│   ├── config.py          ← Settings (reads ../.env)
│   ├── devui_app.py       ← MAF DevUI launcher (debug/test interface)
│   ├── kb/
│   │   ├── search.py      ← search_kb @tool (Azure AI Search, semantic search)
│   │   ├── priority.py    ← assess_priority @tool (multi-signal priority verification)
│   │   └── index_kb.py    ← Indexer script (Excel → Azure AI Search)
│   ├── voice/             ← Voice channel (Azure Communication Services)
│   │   ├── handler.py     ← ACS Call Automation handler (STT → agent → TTS loop)
│   │   └── routes.py      ← FastAPI routes for incoming calls
│   └── skills/            ← MAF Skills (loaded on-demand, saves tokens)
│       ├── ticket-creation/   ← Ticket workflow + categories, groups, business rules
│       ├── ticket-management/ ← Status checks, notes, updates, listing
│       ├── clinical-triage/   ← Patient care decision tree (equipment / Epic / non-Epic)
│       └── non-it-routing/    ← HR/Facilities/Operations contacts
│
├── tests/
│   ├── test_eval.py       ← agent behavior tests
│   └── fixtures/mock_mcp/ ← Mock ManageEngine MCP server (local dev)
│
├── frontend/              ← React chat UI
├── teams-app/             ← Teams manifest
├── infra/                 ← Azure Bicep (AI Foundry, AI Search, Cosmos DB, Key Vault, Monitoring)
└── .github/               ← cockpit (instructions, project-context, references — gitignored)
```

## Related

- `infra/` — Azure infrastructure (Bicep): Foundry Account + Project, GPT-4o, text-embedding-3-large, AI Search, Key Vault, Monitoring
- `.github/` — cockpit config (steering instructions, customer project-context, reference repos) — gitignored
