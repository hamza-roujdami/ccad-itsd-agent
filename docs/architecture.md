# Architecture

## Solution Overview

The Clinical ITSM Agent is an AI-powered IT Service Desk agent for hospital/clinical environments.
It uses the Microsoft Agent Framework (MAF) with a single-agent architecture, progressive skill
disclosure, and MCP integration with ManageEngine ServiceDesk Plus.

## Infrastructure View

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

## Agent Internals

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
            SK1["📄 SKILL.md"]
            R1["📎 categories.md"]
            R2["📎 resolver-groups.md"]
            R3["📎 business-rules.md"]
        end
        subgraph S2["clinical-triage"]
            SK2["📄 SKILL.md<br/>Decision tree"]
        end
        subgraph S3["ticket-management"]
            SK3["📄 SKILL.md"]
        end
        subgraph S4["non-it-routing"]
            SK4["📄 SKILL.md"]
        end
    end

    subgraph MCPLayer["MCP Tools (ManageEngine)"]
        direction TB
        MCP["🔧 MCPStreamableHTTPTool<br/>(17 tools via APIM)"]
    end

    subgraph HistoryLayer["Conversation History"]
        HP["📚 HistoryProvider<br/>CosmosDB (prod) / File (dev)"]
    end

    User --> Prompt
    Prompt --> LLM
    LLM --> SearchKB
    LLM --> AssessPri
    LLM -->|"load_skill"| S1
    LLM -->|"load_skill"| S2
    LLM -->|"load_skill"| S3
    LLM -->|"load_skill"| S4
    LLM --> MCP
    LLM -.-> HP

    class Prompt prompt
    class SearchKB,AssessPri tool
    class SK1,SK2,SK3,SK4 skill
    class R1,R2,R3 resource
    class MCP external
    class HP history
```

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Single agent vs multi-agent | Single agent | ITSM scope is sequential (KB → ticket), not parallel. 1 LLM call vs 2. |
| Skills vs hardcoded prompts | MAF SkillsProvider | Business rules loaded on-demand. KB-only queries save ~800 tokens. |
| MCP vs direct API | MCP for ManageEngine | Customer owns MCP server. Agent auto-discovers 17 tools. Decoupled. |
| Native tool vs MCP for KB search | Native `search_kb` | Tightly coupled to our Azure AI Search config. No MCP overhead. |
| Priority scoring | Deterministic `assess_priority` tool | Weighted vote (user × matrix × text analysis). Not LLM-interpreted. |
| Conversation persistence | CosmosDB (prod) / File (dev) | MAF built-in `HistoryProvider`. Zero custom code. |
| Observability | OpenTelemetry → App Insights | MAF `configure_otel_providers()`. Agents (Preview) view in portal. |

## Azure Resources

| Resource | Purpose | Bicep Module |
|---|---|---|
| Azure AI Foundry | GPT-4o model hosting | `infra/modules/ai-foundry.bicep` |
| Azure AI Search | KB index (33 articles) | `infra/modules/ai-search.bicep` |
| Azure Cosmos DB | Conversation history (serverless) | `infra/modules/cosmos-db.bicep` |
| Azure Key Vault | Secrets management | `infra/modules/key-vault.bicep` |
| Azure Monitor + App Insights | Telemetry, agent tracing | `infra/modules/monitoring.bicep` |
| Azure Communication Services | Voice channel (Phase 2) | `infra/modules/communication-services.bicep` |
