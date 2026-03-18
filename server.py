"""
Model Router MCP Server

Works in two modes:

  Claude Code (interactive):
    select_model / compare_models return human-readable text.
    Claude Code surfaces the recommendation to the user, who can then
    switch models via /model. Claude Code cannot switch its own model
    mid-session — the tool is advisory.

  Standalone / programmatic (custom agent loops):
    get_routing_decision returns structured JSON so your code can extract
    the model ID and route the API call automatically.

Usage:
  python server.py

Add to ~/.claude/mcp.json (global) or .mcp.json (project):
  {
    "mcpServers": {
      "model-router": {
        "command": "python",
        "args": ["server.py"],
        "cwd": "/path/to/model-router-mcp"
      }
    }
  }
"""

import json

from mcp.server.fastmcp import FastMCP

from classifier import classify, estimate_cost
from models import MODELS

mcp = FastMCP(
    "model-router",
    instructions=(
        "Use select_model before starting any significant task to recommend the optimal "
        "Claude model. Tell the user the recommendation and suggest they switch via /model "
        "if a different model would serve them better. "
        "Use compare_models when the user wants to understand cost tradeoffs across models. "
        "Use get_routing_decision when a programmatic client needs structured JSON output."
    ),
)


@mcp.tool()
def select_model(prompt: str, context: str = "") -> str:
    """
    Analyze a prompt and recommend the optimal Claude model to use.

    Returns the recommended model ID, task classification, complexity assessment,
    reasoning, and confidence score. Always call this before deciding which model
    to use for a task — it optimizes for quality, speed, and cost automatically.

    Args:
        prompt:  The user prompt or task description to evaluate.
        context: Optional context about the conversation or project to improve accuracy.
    """
    result = classify(prompt, context)

    model_info = MODELS[result["recommended_model"]]

    lines = [
        f"Recommended model: {result['recommended_model']}",
        f"",
        f"Task type:    {result['task_type']}",
        f"Complexity:   {result['complexity']}",
        f"Confidence:   {result['confidence']:.0%}",
        f"Output size:  {result['estimated_output_length']}",
        f"",
        f"Reasoning: {result['reasoning']}",
        f"",
        f"Model description: {model_info['description']}",
        f"Input cost:  ${model_info['cost_input_per_1m']:.2f} / 1M tokens",
        f"Output cost: ${model_info['cost_output_per_1m']:.2f} / 1M tokens",
    ]

    # Surface a warning when confidence is low
    if result["confidence"] < 0.65:
        lines += [
            "",
            f"⚠️  Low confidence ({result['confidence']:.0%}). Consider using "
            f"claude-sonnet-4-6 as a safe default, or provide more context.",
        ]

    # Claude Code advisory note
    lines += [
        "",
        "Note: To switch models in Claude Code, use /model in the chat.",
    ]

    return "\n".join(lines)


@mcp.tool()
def compare_models(prompt: str) -> str:
    """
    Compare cost and suitability of all Claude models for a given prompt.

    Returns a side-by-side breakdown of estimated cost and capability fit
    for claude-haiku-4-5, claude-sonnet-4-6, and claude-opus-4-6.
    Useful when the user wants to make an informed cost/quality tradeoff decision.

    Args:
        prompt: The prompt or task description to evaluate.
    """
    # Classify once to get the recommendation and output length estimate
    classification = classify(prompt)
    output_length = classification.get("estimated_output_length", "medium")

    lines = [
        f"Prompt analysis: {classification['task_type']} task, "
        f"{classification['complexity']} complexity",
        f"Recommended: {classification['recommended_model']}",
        f"",
        f"{'Model':<22} {'Input cost':>12} {'Est. output cost':>18} {'Est. total':>12}  Fit",
        "-" * 80,
    ]

    for model_id, info in MODELS.items():
        costs = estimate_cost(prompt, model_id, output_length)
        is_recommended = "✓ recommended" if model_id == classification["recommended_model"] else ""
        lines.append(
            f"{model_id:<22} "
            f"${costs['estimated_input_cost_usd']:>10.5f}  "
            f"${costs['estimated_output_cost_usd']:>15.5f}  "
            f"${costs['estimated_total_cost_usd']:>10.5f}  "
            f"{is_recommended}"
        )

    lines += [
        "",
        f"Input tokens in prompt: {estimate_cost(prompt, 'claude-sonnet-4-6')['input_tokens']}",
        f"Estimated output tokens ({output_length}): "
        f"{'256' if output_length == 'short' else '1024' if output_length == 'medium' else '4096'}",
        "",
        f"Reasoning: {classification['reasoning']}",
    ]

    return "\n".join(lines)


@mcp.tool()
def get_routing_decision(prompt: str, context: str = "") -> str:
    """
    Return a structured JSON routing decision for programmatic use.

    Designed for custom agent loops that need to extract the model ID and
    route an API call automatically — not for interactive Claude Code sessions.

    Returns JSON with:
      recommended_model  — exact model ID to pass to the Anthropic API
      task_type          — classified task category
      complexity         — low / medium / high
      reasoning          — one-sentence explanation
      confidence         — float 0.0–1.0
      estimated_output_length — short / medium / long
      cost_per_1m_input  — input cost in USD per 1M tokens
      cost_per_1m_output — output cost in USD per 1M tokens

    Args:
        prompt:  The user prompt or task description to evaluate.
        context: Optional context to improve classification accuracy.
    """
    result = classify(prompt, context)
    model_info = MODELS[result["recommended_model"]]

    payload = {
        "recommended_model":      result["recommended_model"],
        "task_type":               result["task_type"],
        "complexity":              result["complexity"],
        "reasoning":               result["reasoning"],
        "confidence":              result["confidence"],
        "estimated_output_length": result["estimated_output_length"],
        "cost_per_1m_input":       model_info["cost_input_per_1m"],
        "cost_per_1m_output":      model_info["cost_output_per_1m"],
    }

    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    mcp.run()
