# backend/config.py
import os

# --- 全局常量 ---

# Ollama API 配置
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# --- 模型配置 (Hybrid Architecture) ---
# 主对话模型 (Main Agent): 负责与用户进行共情对话
# 建议: qwen2.5:14b 或 qwen2.5:7b (根据您的显存情况)
MAIN_MODEL_NAME = "qwen3:1.7b"

# XAI 解释模型 (Explanation Agent): 负责生成简短的内部状态解释
# 建议: qwen2.5:1.5b 或 llama3.2:3b
XAI_MODEL_NAME = "qwen3:1.7b"

# LLM 服务的系统提示 (主对话用)
SYSTEM_PROMPT = (
    "You are a gentle and empathetic conversational partner. "
    "Always respond in a natural, human-like manner. "
    "Keep your responses consistent with the user's language. "
    "Do not comment on the user's language skills."
)

# 摘要生成间隔
SUMMARY_INTERVAL = 5

# 实验数据存储路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# 实验版本配置
VERSION_MAP = {
    "XAI": "/html/XAI_Version.html",
    "NON_XAI": "/html/non-XAI_version.html"
}

# Instruction 页面版本配置
INSTRUCTION_VERSION_MAP = {
    "XAI": "/html/instructions_xai.html",
    "NON_XAI": "/html/instructions_non_xai.html"
}

# 实验步骤序列 (Within-Subjects)
EXPERIMENT_STEPS = [
    "DEMOGRAPHICS",         # 0
    "BASELINE_MOOD",        # 1
    "INSTRUCTIONS_1",       # 2
    "DIALOGUE_1",           # 3
    "POST_QUESTIONNAIRE_1", # 4
    "WASHOUT",              # 5
    "INSTRUCTIONS_2",       # 6
    "DIALOGUE_2",           # 7
    "POST_QUESTIONNAIRE_2", # 8
    "OPEN_ENDED_QS",        # 9
    "DEBRIEF"               # 10
]