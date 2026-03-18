# model-router-mcp

An MCP server that automatically selects the optimal Claude model for every prompt — so you never have to think about it again.

## Why this exists

Every Claude Code session locks you into a single model for the entire conversation. You manually pick Sonnet or Opus at the start, then use it for everything — whether you're asking a simple question or designing a full system architecture.

This MCP server fixes that. Enable it once globally and Claude Code gains two tools it can call automatically:

- **`select_model`** — classifies any prompt and recommends the right model (Haiku, Sonnet, or Opus) based on task complexity
- **`compare_models`** — shows a cost/fit breakdown across all models so you can make an informed tradeoff

You stop thinking about models. The agent does it for you.

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
Recommendation returned to Claude Code
Claude Code uses the right model for that specific task
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

The `select_model` and `compare_models` tools will appear automatically in every session, across every project.

That's it. You don't touch it again.

## Global vs project-level

| Location | Effect |
|---|---|
| `~/.claude/mcp.json` | Available in **all** Claude Code sessions globally |
| `.mcp.json` in a project | Available only in that project |

For a routing tool like this, global makes the most sense — you want it everywhere.

## Example output

### `select_model`

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
