# model-router-mcp

An MCP server that automatically selects the optimal Claude model for every prompt — so you never have to think about it again.

## Why this exists

Every Claude Code session locks you into a single model for the entire conversation. You manually pick Sonnet or Opus at the start, then use it for everything — whether you're asking a simple question or designing a full system architecture.

This MCP server adds model-awareness. It works in two modes:

**Claude Code (interactive)**
Claude Code calls `select_model` automatically and surfaces the recommendation. Because Claude Code can't switch its own model mid-session, it tells you which model would be better and you switch via `/model`. It's advisory — but it means you're always informed rather than guessing.

**Standalone / custom agents (programmatic)**
Your agent loop calls `get_routing_decision`, gets back structured JSON with the model ID, and routes the actual API call automatically. Full closed-loop routing with no user intervention.

## How it works

```
Your prompt
    │
    ▼
Haiku classifier  (~100ms, <$0.0001 per call)
  ├── What kind of task is this?  (coding, architecture, Q&A, analysis...)
  ├── How complex is it?          (low / medium / high)
  └── How long will the output be? (short / medium / long)
    │
    ▼
Routing decision
  └── low complexity    →  claude-haiku-4-5   (fast, cheap)
      medium / default  →  claude-sonnet-4-6  (balanced)
      high complexity   →  claude-opus-4-6    (most capable)
    │
    ▼
Recommendation returned to Claude Code or your agent
```

The classifier itself always uses Haiku — it's cheap and fast enough that the overhead is negligible. You're not paying Opus prices to decide whether to use Opus.

## What gets routed where

| Model | When | Examples |
|---|---|---|
| `claude-haiku-4-5` | Simple, fast, cheap | Q&A, classification, extraction, summarization, yes/no decisions |
| `claude-sonnet-4-6` | Balanced (default) | Code generation, analysis, writing, most everyday agent tasks |
| `claude-opus-4-6` | Complex, high-stakes | System architecture, ambiguous multi-constraint problems, comprehensive planning |

## Setup

**1. Install dependencies**

```bash
git clone https://github.com/ewanlimr25/model-router-mcp
cd model-router-mcp
pip install -e .
```

Requires `ANTHROPIC_API_KEY` in your environment.

**2. Enable globally in Claude Code**

Add to `~/.claude/mcp.json` (creates it if it doesn't exist):

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

Replace `/path/to/model-router-mcp` with the actual path where you cloned the repo.

**3. Restart Claude Code**

Three tools appear automatically in every session, across every project:
- `select_model` — human-readable recommendation, Claude Code surfaces it to you
- `compare_models` — cost/fit breakdown across all models
- `get_routing_decision` — structured JSON for programmatic agent loops

**Important:** Claude Code cannot switch its own model mid-session. When `select_model` recommends a different model, Claude Code will tell you and you switch manually with `/model`. This is a Claude Code limitation, not a server limitation — in a custom agent loop, `get_routing_decision` gives you the model ID and your code routes the API call directly.

## Global vs project-level

| Location | Effect |
|---|---|
| `~/.claude/mcp.json` | Available in **all** Claude Code sessions globally |
| `.mcp.json` in a project | Available only in that project |

For a routing tool like this, global makes the most sense — you want it everywhere.

## Example output

### `get_routing_decision` (programmatic)

```json
{
  "recommended_model": "claude-opus-4-6",
  "task_type": "architecture",
  "complexity": "high",
  "reasoning": "Requires expert-level reasoning across multiple competing constraints.",
  "confidence": 0.92,
  "estimated_output_length": "long",
  "cost_per_1m_input": 5.0,
  "cost_per_1m_output": 25.0
}
```

Your agent loop extracts `recommended_model` and passes it directly to the Anthropic API.

### `select_model` (Claude Code / interactive)

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

### `compare_models`

```
Prompt analysis: architecture task, high complexity
Recommended: claude-opus-4-6

Model                   Input cost    Est. output cost    Est. total  Fit
--------------------------------------------------------------------------------
claude-haiku-4-5        $  0.00012    $        0.00102    $  0.00114
claude-sonnet-4-6       $  0.00036    $        0.00614    $  0.00651
claude-opus-4-6         $  0.00060    $        0.01024    $  0.01084  ✓ recommended
```

## Improving accuracy for your use case

The routing logic is in `classifier.py` → `CLASSIFIER_SYSTEM_PROMPT`. The rules are plain English — if you notice misroutes for your domain, add signals to the ROUTING RULES section.

Example: if you work in a domain where "migration" always means complex database work (not a simple script), add that signal:

```
Route to claude-opus-4-6 when the prompt involves:
- ...existing rules...
- Database migrations with schema changes or multi-system coordination
```

The more domain-specific signals you encode, the more accurate routing becomes for your specific workflow.

## Model reference

| Model | Input | Output |
|---|---|---|
| claude-haiku-4-5 | $1.00 / 1M tokens | $5.00 / 1M tokens |
| claude-sonnet-4-6 | $3.00 / 1M tokens | $15.00 / 1M tokens |
| claude-opus-4-6 | $5.00 / 1M tokens | $25.00 / 1M tokens |

Pricing sourced from [Anthropic's pricing page](https://www.anthropic.com/pricing). Update `models.py` if rates change.
