"""
Model Router MCP Server

Exposes two tools to any MCP-compatible agent host (Claude Code, custom agents, etc.):

  select_model(prompt, context?)
    → recommends the optimal Claude model for a given prompt

  compare_models(prompt)
    → returns cost and capability comparison across all models for a prompt

Usage:
  python server.py

Add to .mcp.json:
  {
    "mcpServers": {
      "model-router": {
        "command": "python",
        "args": ["server.py"],
        "cwd": "/Users/ewan/Development/model-router-mcp"
      }
    }
  }
"""

from mcp.server.fastmcp import FastMCP

from classifier import classify, estimate_cost
from models import MODELS

mcp = FastMCP(
    "model-router",
    instructions=(
        "Use select_model before running any significant task to determine the optimal "
        "Claude model. Use compare_models when the user wants to understand cost tradeoffs."
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


if __name__ == "__main__":
    mcp.run()
