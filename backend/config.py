# backend/config.py
import os
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = "gemini-2.5-flash"

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
