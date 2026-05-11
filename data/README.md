# data/

KB data and indexing scripts for the CCAD ITSD Agent.

## Files

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
cd csa-code
source .venv/bin/activate
python -m data.index_kb
```

Requires Azure CLI login (`az login`) and the following env vars in `.env`:
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_INDEX_NAME` (default: `itsd-kb`)

## Updating the KB

1. Get the updated Excel from CCAD
2. Replace `solutions_kb.xlsx`
3. Re-run `python -m data.index_kb`
