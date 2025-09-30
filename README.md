# Gander LLM CLI

Tiny CLI that answers a user question like a normal chat assistant and returns one JSON object with:
- `human_response_markdown`  
- `citations`  
- `mentions`  
- `owned_sources`  
- `sources`  
- `metadata` (budgets, token notes)


## How it works (high level)
1. Optional web search up to `max-searches`
2. Select up to `max-sources` high quality URLs
3. Build a short context
4. Ask model for a natural, user-facing answer
5. Post-process the final answer to extract mentions and URLs
6. Output a single JSON

## How to run

Prereqs:
- Python 3.11
- A virtual environment

Setup:
1. python -m venv .venv
2. source .venv/bin/activate
3. pip install -r requirements.txt
4. pip install -e .

Run:
python -m gander_llm_cli
--brand "Gander GEO"
--url "https://gandergeo.com"
--question "What does this brand offer?"
--max-searches 0
--max-sources 0
--output examples/sample_output.json

pgsql
Copy code

The command prints a single JSON object and, if `--output` is provided, writes it to that path.

## Design decisions and trade-offs

- Single-command interface: keeps usage obvious for non-engineers.
- JSON enforced by Pydantic: guarantees a stable schema and clear validation errors.
- URL parsing: favor a compact, readable regex with a short cleanup step; avoids overfitting to markdown variants.
- Mentions: exact-case word-boundary match for determinism. This avoids false positives from case drift.
- Owned vs external: compare registrable domains and subdomains. Simple and predictable.
- Budgets: recorded in `metadata` today; search and source selection will honor caps once search is added.
- Token efficiency (initial plan): 
  1) Aggressive snippet trimming to only the smallest relevant paragraphs.
  2) Deduplicate near-identical passages across sources.
  Trade-off: trimming can miss nuance; deduping can drop rare but useful phrasing.
