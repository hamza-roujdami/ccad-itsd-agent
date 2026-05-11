"""Index KB data from Excel into Azure AI Search.

Usage:
    python -m data.index_kb

Reads data/solutions_kb.xlsx and uploads all articles to the itsd-kb index.
Creates the index if it doesn't exist, or updates documents if it does.
"""

import openpyxl
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)

from config import settings

EXCEL_PATH = "data/solutions_kb.xlsx"


def load_articles() -> list[dict]:
    """Read articles from the Excel file."""
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active
    articles = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=1):
        category, user_intent, content, keywords = row
        if not user_intent:
            continue
        articles.append({
            "id": str(i),
            "category": category or "",
            "user_intent": user_intent or "",
            "content": content or "",
            "keywords": keywords or "",
        })
    return articles


def ensure_index(client: SearchIndexClient):
    """Create the itsd-kb index if it doesn't exist."""
    existing = list(client.list_index_names())
    if settings.azure_search_index_name in existing:
        print(f"Index '{settings.azure_search_index_name}' already exists, skipping creation.")
        return

    fields = [
        SearchField(name="id", type=SearchFieldDataType.String, key=True, searchable=False, filterable=True, sortable=False, facetable=False),
        SearchField(name="category", type=SearchFieldDataType.String, searchable=True, filterable=True, facetable=True),
        SearchField(name="user_intent", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="keywords", type=SearchFieldDataType.String, searchable=True),
    ]

    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="user_intent"),
            content_fields=[SemanticField(field_name="content")],
            keywords_fields=[SemanticField(field_name="keywords")],
        ),
    )

    index = SearchIndex(
        name=settings.azure_search_index_name,
        fields=fields,
        semantic_search=SemanticSearch(configurations=[semantic_config]),
    )

    client.create_or_update_index(index)
    print(f"Index '{settings.azure_search_index_name}' ready.")


def upload_documents(client: SearchClient, articles: list[dict]):
    """Upload articles to the index."""
    result = client.upload_documents(documents=articles)
    succeeded = sum(1 for r in result if r.succeeded)
    print(f"Uploaded {succeeded}/{len(articles)} documents.")


def main():
    credential = DefaultAzureCredential()

    index_client = SearchIndexClient(settings.azure_search_endpoint, credential)
    ensure_index(index_client)

    search_client = SearchClient(
        settings.azure_search_endpoint,
        settings.azure_search_index_name,
        credential,
    )

    articles = load_articles()
    print(f"Loaded {len(articles)} articles from {EXCEL_PATH}")
    upload_documents(search_client, articles)
    print("Done.")


if __name__ == "__main__":
    main()
