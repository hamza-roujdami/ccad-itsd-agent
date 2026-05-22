# kb/

Knowledge base search, data, and indexing for the CCAD ITSM Agent.

## Files

- `search.py` — `search_kb` @tool (Azure AI Search, semantic search)
- `solutions_kb.xlsx` — IT knowledge base articles from CCAD (33 articles)
- `index_kb.py` — Script to create/update the Azure AI Search index

## Columns in solutions_kb.xlsx

| Column | Description |
|--------|-------------|
| Category | Topic area (Epic, Passwords, Printing, VDI, etc.) |
| User Intent | What the user is trying to do |
| Content | Step-by-step resolution |
| Keywords | Search terms |

## Usage

Index (or re-index) the KB into Azure AI Search:

```bash
source .venv/bin/activate
python -m kb.index_kb
```

Requires Azure CLI login (`az login`) and the following env vars in `.env`:
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_INDEX_NAME` (default: `itsd-kb`)

## Updating the KB

1. Get the updated Excel from CCAD
2. Replace `solutions_kb.xlsx`
3. Re-run `python -m data.index_kb`
