"""
Haiku-powered prompt classifier.

Takes a user prompt and returns a structured routing decision:
which model to use, why, and how confident we are.
"""

import json

import anthropic

from models import CLASSIFIER_MODEL, MODELS, TASK_TYPES

CLASSIFIER_SYSTEM_PROMPT = f"""You are a model routing expert for Claude AI. Your only job is to analyze a user prompt and decide which Claude model should handle it — optimizing for quality, speed, and cost.

Available models:

claude-haiku-4-5 (cheapest, fastest)
  Best for: {", ".join(MODELS["claude-haiku-4-5"]["strengths"])}

claude-sonnet-4-6 (balanced — the default)
  Best for: {", ".join(MODELS["claude-sonnet-4-6"]["strengths"])}

claude-opus-4-6 (most capable, most expensive)
  Best for: {", ".join(MODELS["claude-opus-4-6"]["strengths"])}

ROUTING RULES:

Route to claude-opus-4-6 when the prompt involves:
- Designing or architecting a system, application, or platform
- Words like "architect", "design", "strategy", "comprehensive plan", "tradeoffs"
- Multiple competing constraints that require expert balancing
- High ambiguity where the wrong answer has real consequences
- Novel problems with no obvious established pattern

Route to claude-haiku-4-5 when the prompt involves:
- A single clear factual question
- Classifying, tagging, or categorizing something
- Extracting fields from structured text
- A yes/no or short fixed-format answer
- Routing or triage decisions (meta-tasks)

Route to claude-sonnet-4-6 (default) when:
- Writing or reviewing code of moderate complexity
- Analyzing something with a clear scope
- Multi-step tasks that are well-defined
- The prompt doesn't clearly fit haiku or opus

IMPORTANT: When in doubt, prefer sonnet. Only use opus when the task genuinely requires deep expert reasoning. Only use haiku when the task is clearly simple.

Task types: {", ".join(TASK_TYPES)}

Respond with a JSON object ONLY — no explanation, no markdown, no other text:
{{
  "recommended_model": "claude-haiku-4-5" | "claude-sonnet-4-6" | "claude-opus-4-6",
  "task_type": "<one of the task types above>",
  "complexity": "low" | "medium" | "high",
  "reasoning": "<one concise sentence explaining the choice>",
  "confidence": <float 0.0 to 1.0>,
  "estimated_output_length": "short" | "medium" | "long"
}}"""


def classify(prompt: str, context: str = "") -> dict:
    """
    Classify a prompt and return a routing decision.

    Args:
        prompt: The user's prompt to classify.
        context: Optional additional context (e.g. conversation history summary).

    Returns:
        dict with keys: recommended_model, task_type, complexity,
                        reasoning, confidence, estimated_output_length
    """
    client = anthropic.Anthropic()

    user_content = f"Prompt to classify:\n\n{prompt}"
    if context:
        user_content += f"\n\nAdditional context:\n{context}"

    response = client.messages.create(
        model=CLASSIFIER_MODEL,
        max_tokens=256,
        system=CLASSIFIER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: if Haiku returned malformed JSON, default to Sonnet
        result = {
            "recommended_model": "claude-sonnet-4-6",
            "task_type": "other",
            "complexity": "medium",
            "reasoning": "Classifier returned malformed output; defaulting to sonnet.",
            "confidence": 0.5,
            "estimated_output_length": "medium",
        }

    # Validate model is one we know about
    if result.get("recommended_model") not in MODELS:
        result["recommended_model"] = "claude-sonnet-4-6"

    return result


def estimate_cost(prompt: str, model: str, estimated_output_length: str = "medium") -> dict:
    """
    Rough cost estimate for running a prompt on a given model.

    Uses token counting for input, and a heuristic for output.
    """
    if model not in MODELS:
        raise ValueError(f"Unknown model: {model}. Choose from: {list(MODELS.keys())}")

    client = anthropic.Anthropic()

    token_count = client.messages.count_tokens(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    input_tokens = token_count.input_tokens

    # Heuristic output token estimates
    output_estimates = {"short": 256, "medium": 1024, "long": 4096}
    output_tokens = output_estimates.get(estimated_output_length, 1024)

    model_info = MODELS[model]
    input_cost  = (input_tokens  / 1_000_000) * model_info["cost_input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * model_info["cost_output_per_1m"]

    return {
        "model": model,
        "input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "estimated_input_cost_usd":  round(input_cost,  6),
        "estimated_output_cost_usd": round(output_cost, 6),
        "estimated_total_cost_usd":  round(input_cost + output_cost, 6),
    }
