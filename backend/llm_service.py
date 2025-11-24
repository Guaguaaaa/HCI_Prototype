# backend/llm_service.py
import requests
import json
# 引入新的配置变量名
from backend.config import OLLAMA_API_URL, MAIN_MODEL_NAME, XAI_MODEL_NAME, SYSTEM_PROMPT, SUMMARY_INTERVAL

# === 全局存储 - 参与者会话数据隔离 ===
session_data = {}


def get_session(participant_id: str) -> dict:
    """获取或初始化参与者的会话数据"""
    if participant_id not in session_data:
        session_data[participant_id] = {
            'history': [],
            'summary': "",
            'full_prompt': "",
            'turn_count': 0,
            'sentiment_scores': []
        }
    return session_data[participant_id]


def clear_session(participant_id: str) -> bool:
    """清除特定参与者的会话历史"""
    if participant_id in session_data:
        del session_data[participant_id]
        print(f"🧹 Session cleared for PID {participant_id}")
        return True
    return False


def generate_summary(session: dict):
    """生成近期对话摘要 (使用 XAI 小模型以节省资源)"""
    conversation_history = session['history']
    summary_memory = session['summary']

    recent_dialogue = "\n".join(
        [f"{m['role'].capitalize()}: {m['content']}" for m in conversation_history[-10:]]
    )

    summary_prompt = f"""
Please summarize the following conversation into a concise summary of no more than 150 words. 
Focus on the user's main emotions, topics, and intents. Keep the summary in English.

Previous summary (if any):
{summary_memory if summary_memory else "(None)"}

New conversation:
{recent_dialogue}

Output the new summary:
"""
    try:
        resp = requests.post(
            OLLAMA_API_URL,
            json={
                "model": XAI_MODEL_NAME,  # 使用小模型做摘要
                "prompt": summary_prompt,
                "stream": False
            },
            timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        new_summary = data.get("response", "").strip()
        if new_summary:
            session['summary'] = new_summary
    except Exception as e:
        print(f"⚠️ Failed to generate summary: {e}")


# --- NEW: XAI 解释生成函数 ---
def generate_xai_explanation(user_text: str, sentiment_data: dict) -> str:
    """
    使用小模型生成 XAI 解释。
    解释包含：对用户情绪的识别 + AI 意图的简述。
    """
    top_emotion = sentiment_data.get("top_emotion", "neutral")

    # 构造 XAI Prompt
    # 这是一个 Meta-Prompt，让 AI 解释自己的“内部状态”
    xai_prompt = f"""
Analyze the following user input and the detected emotion.
User Input: "{user_text}"
Detected Emotion: {top_emotion}

Task: Explain briefly (in 1-2 sentences) why you categorize the user's emotion as '{top_emotion}' and what your goal is for the next response to support them. 
Write the explanation in the third person (e.g., "The system detects...", "The agent aims to...").
Keep it concise and objective.
"""

    try:
        resp = requests.post(
            OLLAMA_API_URL,
            json={
                "model": XAI_MODEL_NAME,  # 使用小模型生成解释
                "prompt": xai_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # 保持解释的稳定性
                    "max_tokens": 100
                }
            },
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
        return "System analysis unavailable."
    except Exception as e:
        print(f"⚠️ XAI Gen Error: {e}")
        return "System analysis unavailable."


def get_llm_response_stream(participant_id: str, user_input: str):
    """
    处理聊天逻辑和 LLM 响应流 (使用主模型)。
    """
    session = get_session(participant_id)
    conversation_history = session['history']
    summary_memory = session['summary']

    # 1. 添加用户输入
    conversation_history.append({"role": "user", "content": user_input})

    # --- 构建 Prompt ---
    full_prompt = ""
    if len(conversation_history) == 1:
        full_prompt += SYSTEM_PROMPT + "\n\n"

    if summary_memory:
        full_prompt += f"Context Summary:\n{summary_memory}\n\n"

    for msg in conversation_history[-10:]:
        prefix = "User:" if msg["role"] == "user" else "AI:"
        full_prompt += f"{prefix} {msg['content']}\n"

    full_prompt += "AI:"
    session['full_prompt'] = full_prompt

    # --- 流式响应 (使用 MAIN_MODEL_NAME) ---
    full_ai_reply = ""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MAIN_MODEL_NAME,  # 使用大模型进行对话
                "prompt": full_prompt,
                "stream": True
            },
            stream=True,
            timeout=300
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    json_line = line.decode('utf-8')
                    data = json.loads(json_line)
                    text_chunk = data.get("response", "")
                    if text_chunk:
                        full_ai_reply += text_chunk
                        yield text_chunk.encode('utf-8')
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    pass

    except requests.RequestException as e:
        yield f"⚠️ Backend LLM error: {e}".encode('utf-8')

    finally:
        if full_ai_reply:
            conversation_history.append({"role": "ai", "content": full_ai_reply.strip()})
            session['turn_count'] += 1
            if len(conversation_history) % (SUMMARY_INTERVAL * 2) == 0:
                generate_summary(session)
        print("✅ Streaming Complete")