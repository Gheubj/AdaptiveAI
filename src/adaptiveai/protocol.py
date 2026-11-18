from __future__ import annotations

SOURCE_SHA256 = "b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1"
DEFAULT_SEED = 3407

LIGHTWEIGHT20 = (
    "DeepHermes-3-Llama-3-8B-Preview",
    "DeepSeek-R1-0528-Qwen3-8B",
    "DeepSeek-R1-Distill-Qwen-7B",
    "Fin-R1",
    "GLM-Z1-9B-0414",
    "Intern-S1-mini",
    "Llama-3.1-8B-Instruct",
    "Llama-3.1-8B-UltraMedical",
    "Llama-3.1-Nemotron-Nano-8B-v1",
    "MiMo-7B-RL-0530",
    "MiniCPM4.1-8B",
    "NVIDIA-Nemotron-Nano-9B-v2",
    "OpenThinker3-7B",
    "Qwen2.5-Coder-7B-Instruct",
    "Qwen3-8B",
    "cogito-v1-preview-llama-8B",
    "gemma-2-9b-it",
    "glm-4-9b-chat",
    "granite-3.3-8b-instruct",
    "internlm3-8b-instruct",
)

PROPRIETARY8 = (
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "qwen3-235b-a22b-2507",
    "deepseek-v3.1-terminus",
    "deepseek-r1-0528",
    "deepseek-v3-0324",
    "glm-4.6",
    "kimi-k2-0905",
)

PAPER_PROPRIETARY13 = (
    "claude-sonnet-4",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gpt-5-chat",
    "gpt-5",
    "qwen3-235b-a22b-2507",
    "qwen3-235b-a22b-thinking-2507",
    "deepseek-v3-0324",
    "deepseek-v3.1-terminus",
    "deepseek-r1-0528",
    "glm-4.6",
    "kimi-k2-0905",
    "intern-s1",
)

PAPER_PERFORMANCE_DATASETS = (
    "aime",
    "math500",
    "mathbench",
    "humaneval",
    "mbpp",
    "livecodebench",
    "bbh",
    "korbench",
    "kandk",
    "mmlupro",
    "gpqa",
    "finqa",
    "medqa",
    "emorynlp",
    "meld",
)
PAPER_COST_DATASETS = (
    "aime",
    "livemathbench",
    "livecodebench",
    "swe-bench",
    "gpqa",
    "hle",
    "mmlupro",
    "simpleqa",
    "arenahard",
    "tau2",
)

TASK_BY_DATASET = {
    **{d: "mathematics" for d in ("aime", "math500", "mathbench", "livemathbench", "finqa")},
    **{d: "coding" for d in ("humaneval", "mbpp", "livecodebench", "swe-bench")},
    **{d: "reasoning" for d in ("bbh", "korbench", "kandk", "arcc", "winogrande", "arc-agi")},
    **{d: "knowledge" for d in ("mmlupro", "gpqa", "medqa", "hle", "simpleqa")},
    **{d: "affective" for d in ("emorynlp", "meld")},
    "arenahard": "instruction",
    "tau2": "tool_use",
}
