"""
Model definitions, capabilities, and cost data.
Update pricing here if Anthropic changes rates.
"""

MODELS = {
    "claude-haiku-4-5": {
        "description": "Fast and cheap. Simple tasks, classification, extraction, summarization.",
        "cost_input_per_1m":  1.00,
        "cost_output_per_1m": 5.00,
        "strengths": [
            "simple Q&A",
            "classification",
            "data extraction",
            "summarization",
            "routing decisions",
            "short straightforward tasks",
        ],
    },
    "claude-sonnet-4-6": {
        "description": "Balanced speed and capability. Most everyday agent work.",
        "cost_input_per_1m":  3.00,
        "cost_output_per_1m": 15.00,
        "strengths": [
            "code generation and review",
            "standard multi-step reasoning",
            "analysis with clear scope",
            "writing",
            "RAG synthesis",
            "most coding tasks",
        ],
    },
    "claude-opus-4-6": {
        "description": "Most capable. Complex reasoning, ambiguous problems, high-stakes planning.",
        "cost_input_per_1m":  5.00,
        "cost_output_per_1m": 25.00,
        "strengths": [
            "system and application architecture",
            "complex multi-faceted planning",
            "ambiguous problems requiring expert judgment",
            "synthesizing conflicting information",
            "novel unseen problems",
            "high-stakes decisions",
        ],
    },
}

# Model used internally to classify prompts — always Haiku, never changes
CLASSIFIER_MODEL = "claude-haiku-4-5"

TASK_TYPES = [
    "architecture",   # system/application design and planning
    "coding",         # writing, debugging, or reviewing code
    "analysis",       # investigating data, documents, or situations
    "creative",       # writing, brainstorming, ideation
    "qa",             # simple factual questions and answers
    "extraction",     # pulling structured data from unstructured text
    "planning",       # project plans, strategies, roadmaps
    "reasoning",      # multi-step logic or mathematical problems
    "other",
]
