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

