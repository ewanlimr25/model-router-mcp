# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -e .
```

Requires `ANTHROPIC_API_KEY` set in the environment.

## Running the server

```bash
python server.py
```

## Architecture

Three files, intentionally flat:

**`models.py`** — Single source of truth for model IDs, pricing, strengths, and the task type list. Update pricing here when Anthropic changes rates.

**`classifier.py`** — Haiku-powered classification engine. `classify(prompt, context?)` calls Haiku with a carefully engineered system prompt and returns structured JSON: recommended model, task type, complexity, reasoning, confidence. `estimate_cost(prompt, model)` uses the token counting API for accurate input cost + heuristic output estimate.

**`server.py`** — FastMCP server exposing two tools:
- `select_model(prompt, context?)` — main routing tool, returns recommendation + reasoning
- `compare_models(prompt)` — side-by-side cost/fit comparison across all models

The classifier always uses `claude-haiku-4-5` internally — it's fast and cheap enough that the routing overhead is negligible (~100ms, <$0.0001 per call).

## Adding to Claude Code

Copy `.mcp.json.example` to `.mcp.json` in any project (or `~/.claude/mcp.json` globally), update the `cwd` path, and restart Claude Code. The `select_model` and `compare_models` tools will appear automatically.

## Improving routing accuracy

The classifier prompt is in `classifier.py` → `CLASSIFIER_SYSTEM_PROMPT`. When you notice misroutes:
1. Identify the pattern (what kind of prompt got wrong model)
2. Add a signal to the relevant ROUTING RULES section
3. Test with a few representative prompts
