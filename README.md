# model-router-mcp

An MCP server that dynamically selects the optimal Claude model for any prompt — so your agent or app doesn't have to hardcode one.

## The problem

Most Claude Code sessions and agent pipelines use a single hardcoded model for everything. Simple questions get routed to Opus (expensive, overkill). Complex architecture decisions get routed to Haiku (fast, but undersized). Users either overpay or get worse answers.

## The solution

A lightweight MCP server that classifies any prompt using Haiku (~100ms, <$0.0001 per call) and recommends the right model based on task complexity, type, and expected output. Plug it in once, use it everywhere.

## Tools

### `select_model(prompt, context?)`

Returns the recommended model + reasoning for a given prompt.

```
Recommended model: claude-opus-4-6

Task type:    architecture
Complexity:   high
Confidence:   92%
Output size:  long

Reasoning: This prompt asks for a comprehensive system design with multiple
           competing constraints, which requires expert-level reasoning.

Model description: Most capable. Complex reasoning, ambiguous problems, high-stakes planning.
Input cost:  $5.00 / 1M tokens
Output cost: $25.00 / 1M tokens
```

### `compare_models(prompt)`

Side-by-side cost and fit comparison across all models.

```
Prompt analysis: architecture task, high complexity
Recommended: claude-opus-4-6

Model                   Input cost    Est. output cost    Est. total  Fit
--------------------------------------------------------------------------------
claude-haiku-4-5        $  0.00012    $        0.00102    $  0.00114
claude-sonnet-4-6       $  0.00036    $        0.00614    $  0.00651
claude-opus-4-6         $  0.00060    $        0.01024    $  0.01084  ✓ recommended
```

## Setup

```bash
pip install -e .
```

Requires `ANTHROPIC_API_KEY` in your environment.

## Add to Claude Code

**Project-level** (`.mcp.json` in your project root):
```json
{
  "mcpServers": {
    "model-router": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/model-router-mcp"
    }
  }
}
```

**Global** (`~/.claude/mcp.json`) — available in all projects:
```json
{
  "mcpServers": {
    "model-router": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/model-router-mcp"
    }
  }
}
```

Restart Claude Code after adding. The tools appear automatically.

## How it works

```
Your prompt
    │
    ▼
Haiku classifier (~100ms)
  - task type: architecture / coding / qa / analysis / ...
  - complexity: low / medium / high
  - output length: short / medium / long
    │
    ▼
Routing decision
  low complexity   → claude-haiku-4-5
  medium / default → claude-sonnet-4-6
  high complexity  → claude-opus-4-6
    │
    ▼
Recommendation returned to your agent
```

The classifier itself always uses Haiku — it's cheap and fast enough that the routing overhead is negligible.

## Model reference

| Model | Input | Output | Best for |
|---|---|---|---|
| claude-haiku-4-5 | $1/1M | $5/1M | Q&A, classification, extraction, summarization |
| claude-sonnet-4-6 | $3/1M | $15/1M | Coding, analysis, writing, most agent work |
| claude-opus-4-6 | $5/1M | $25/1M | Architecture, complex planning, ambiguous problems |

## Improving accuracy

The routing logic lives in `classifier.py` → `CLASSIFIER_SYSTEM_PROMPT`. If you notice misroutes for your domain, add signals to the ROUTING RULES section. The more domain-specific signals you encode, the more accurate routing becomes for your specific use case.
