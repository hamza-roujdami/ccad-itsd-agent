"""KB search tool — Azure AI Search for ITSD knowledge base."""

from agent_framework import tool
from typing import Annotated
from pydantic import Field
from azure.identity import DefaultAzureCredential
from azure.search.documents.aio import SearchClient

from config import settings


@tool(approval_mode="never_require")
async def search_kb(
    query: Annotated[str, Field(description="Search query describing the user's IT issue")],
) -> str:
    """Search the clinical IT knowledge base for troubleshooting guides, FAQs, and known solutions.
    Use this BEFORE creating a ticket to check if the issue can be resolved with self-service steps."""
    credential = DefaultAzureCredential()
    async with SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=credential,
    ) as client:
        results = await client.search(
            search_text=query,
            top=3,
            query_type="semantic",
            semantic_configuration_name="default",
        )

        articles = []
        async for result in results:
            category = result.get("category", "")
            intent = result.get("user_intent", "")
            content = result.get("content", "")
            score = result.get("@search.reranker_score", result.get("@search.score", 0))
            articles.append(
                f"**[{category}] {intent}** (relevance: {score:.2f})\n{content}"
            )

        if not articles:
            return "No matching KB articles found. Consider creating a ticket if the user needs IT support."

        return "\n\n---\n\n".join(articles)
    return "No matching KB articles found. Consider creating a ticket if the user needs IT support."
