# backend/config.py

import os

# --- 全局常量 ---

# Ollama API 配置
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"

# LLM 服务的系统提示
SYSTEM_PROMPT = (
    "You are a gentle and empathetic conversational partner. "
    "Always respond in a natural, human-like manner. "
    "Keep your responses consistent with the user's language. "
    "Do not comment on the user's language skills."
)

# 摘要生成间隔 (每进行 X 轮用户-AI对话后生成一次摘要)
SUMMARY_INTERVAL = 5

# 实验数据存储路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# backend/config.py

# ... (顶部配置保持不变) ...

# 实验版本配置 (用于手动指定)
VERSION_MAP = {
    "XAI": "/html/XAI_Version.html",
    "NON_XAI": "/html/non-XAI_version.html"
}

# Instruction 页面版本配置
INSTRUCTION_VERSION_MAP = {
    "XAI": "/html/instructions_xai.html",
    "NON_XAI": "/html/instructions_non_xai.html"
}

# 实验步骤序列 (用于流程控制)
# 索引 0: DEMOGRAPHICS
# 索引 1: BASELINE_MOOD
# 索引 2: INSTRUCTIONS (现在只是一个占位符，实际跳转根据条件)
# 索引 3: DIALOGUE
# 索引 4: POST_QUESTIONNAIRE
# 索引 5: OPEN_ENDED_QS
# 索引 6: DEBRIEF (这是终点，不需数据保存)
EXPERIMENT_STEPS = [
    "DEMOGRAPHICS",
    "BASELINE_MOOD",
    "INSTRUCTIONS",
    "DIALOGUE",
    "POST_QUESTIONNAIRE",
    "OPEN_ENDED_QS",
    "DEBRIEF"
]