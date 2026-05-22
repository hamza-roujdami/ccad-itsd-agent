"""Clinical ITSM Agent — Agent definition."""

from pathlib import Path

from agent_framework import Agent, MCPStreamableHTTPTool, SkillsProvider
from agent_framework.foundry import FoundryChatClient
from agent_framework._sessions import HistoryProvider
from azure.identity import DefaultAzureCredential

from config import settings
from kb.search import search_kb
from kb.priority import assess_priority

SYSTEM_PROMPT = """\
You are the Clinical IT Service Desk Agent.
You help clinicians, nurses, doctors, and IT staff resolve technical issues.
Your goal is to SOLVE the issue first, and only create a ticket if self-service fails.

## Core Workflow

1. **Understand the issue** — ask clarifying questions if the description is vague
   (what system? since when? who is affected? which floor/department?).

2. **Determine if IT or non-IT** — if non-IT, load the `non-it-routing` skill
   for correct department contacts. Do NOT create a ticket.

3. **Knowledge-first resolution** — ALWAYS use search_kb BEFORE creating any ticket.
   Walk the user through KB steps. Only proceed to ticket creation if KB did NOT help.

4. **Patient care / clinical triage** — if the issue involves medical equipment,
   Epic, or any clinical system that may impact patient care, load the
   `clinical-triage` skill. It has the full decision tree: equipment vs Epic vs
   non-Epic apps, single vs multiple users, workaround checks, and escalation paths.
   For any patient care impact, add `[Urgent]` to the subject and create immediately.

5. **Ticket creation** — load the `ticket-creation` skill for full classification rules,
   categories, resolver groups, business rules, and mandatory fields.
   Always call assess_priority first to verify the priority.

6. **Ticket management** — load the `ticket-management` skill when the user asks
   about existing tickets (status checks, updates, notes, listing).

## Guidelines
- Be professional, concise, and empathetic — users may be stressed clinicians in a hospital.
- For patient care issues, ALWAYS escalate immediately — do not delay with KB search.
- Never make up solutions — only provide guidance from the KB or escalate.
- After creating a ticket, always share the ticket ID and expected next steps.
- Keep responses focused — clinicians are busy, avoid unnecessary verbosity.
"""


def create_agent(history_provider: HistoryProvider | None = None) -> Agent:
    """Build and return the Clinical ITSM agent."""
    client = FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=settings.foundry_model,
        credential=DefaultAzureCredential(),
    )

    # Skills — progressive disclosure of ticket rules, categories, business rules
    skills_dir = Path(__file__).parent / "skills"
    skills_provider = SkillsProvider.from_paths(skill_paths=str(skills_dir))

    # MCP connection to ManageEngine (mock locally, real APIM in production)
    headers = {}
    if settings.apim_subscription_key:
        headers["Ocp-Apim-Subscription-Key"] = settings.apim_subscription_key

    manage_engine_mcp = MCPStreamableHTTPTool(
        name="ManageEngine",
        description="ManageEngine ServiceDesk Plus — ITSM ticketing system",
        url=settings.mcp_server_url,
        header_provider=(lambda _kwargs: headers) if headers else None,
        approval_mode="never_require",
        load_prompts=False,
    )

    context_providers = [skills_provider]
    if history_provider:
        context_providers.append(history_provider)

    return Agent(
        client=client,
        name="Clinical ITSM Agent",
        instructions=SYSTEM_PROMPT,
        tools=[search_kb, assess_priority, manage_engine_mcp],
        context_providers=context_providers,
    )
