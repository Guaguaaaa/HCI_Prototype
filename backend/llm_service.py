# backend/llm_service.py
import requests
import json
import re
# 引入配置
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


def contains_chinese(text: str) -> bool:
    """简单的辅助函数：检查字符串是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


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


# --- XAI 解释生成函数 (动态 Prompt 语言) ---
def generate_xai_explanation(user_text: str, sentiment_data: dict) -> str:
    """
    使用小模型生成 XAI 解释。
    根据用户输入的语言动态切换 Prompt 语言，确保输出语言一致。
    """
    top_emotion = sentiment_data.get("top_emotion", "neutral")

    # 1. 语言检测与 Prompt 分流
    if contains_chinese(user_text):
        # --- 中文 Prompt ---
        xai_prompt = f"""
        请分析以下用户输入和检测到的情绪。

        用户输入: "{user_text}"
        检测到的情绪标签: {top_emotion}

        任务：
        1. 用第三人称（如“系统检测到...”）简要解释为什么系统认为用户处于“{top_emotion}”情绪。
        2. 说明系统在下一条回复中的目标是什么（如“系统旨在...”）。
        3. 解释必须简洁（1-2句话）。

        **强制要求**：必须使用**中文**直接回答，不要翻译用户的话。
        """
    else:
        # --- English Prompt ---
        xai_prompt = f"""
        Analyze the following user input and the detected emotion.
        
        User Input: "{user_text}"
        Detected Emotion: {top_emotion}
        
        Task: 
        1. Explain briefly (in 1-2 sentences, third person) why the system categorizes the user's emotion as '{top_emotion}'.
        2. State what the goal is for the next response to support them.
        
        **Constraint**: The explanation MUST be in **English**.
        """

    try:
        resp = requests.post(
            OLLAMA_API_URL,
            json={
                "model": XAI_MODEL_NAME,  # 使用小模型生成解释
                "prompt": xai_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 150
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


# --- MODIFIED: 主对话生成函数 (动态 System Prompt) ---
def get_llm_response_stream(participant_id: str, user_input: str):
    """
    处理聊天逻辑和 LLM 响应流 (使用主模型)。
    """
    session = get_session(participant_id)
    conversation_history = session['history']
    summary_memory = session['summary']

    # 1. 添加用户输入
    conversation_history.append({"role": "user", "content": user_input})

    # 2. 动态决定 System Prompt (语言跟随)
    # 如果检测到中文输入，强制使用中文 System Prompt
    if contains_chinese(user_input):
        current_system_prompt = (
            "你是一个温柔且富有同理心的对话伙伴。"
            "请始终以自然、像人一样的方式回应。"
            "请务必使用中文进行回复。"
            "不要评价用户的语言能力。"
        )
    else:
        # 英文输入则使用默认配置 (英文)
        current_system_prompt = SYSTEM_PROMPT

    # 3. 构建 Prompt
    full_prompt = ""

    # --- FIX: 始终在 Prompt 开头包含 System Prompt ---
    # 之前的逻辑是只在 len==1 时添加，导致后续轮次 System Prompt 丢失
    full_prompt += current_system_prompt + "\n\n"

    if summary_memory:
        full_prompt += f"Context Summary:\n{summary_memory}\n\n"

    for msg in conversation_history[-10:]:
        prefix = "User:" if msg["role"] == "user" else "AI:"
        full_prompt += f"{prefix} {msg['content']}\n"

    full_prompt += "AI:"

    # 存入 Session 仅供调试查看
    session['full_prompt'] = full_prompt

    # --- 流式响应 (使用 MAIN_MODEL_NAME) ---
    full_ai_reply = ""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MAIN_MODEL_NAME,
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