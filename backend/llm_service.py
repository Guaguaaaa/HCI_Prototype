# backend/llm_service.py
import re
from google import genai
from google.genai import types

from backend.config import GEMINI_API_KEY, GEMINI_MODEL_NAME, SYSTEM_PROMPT, SUMMARY_INTERVAL

_client = genai.Client(api_key=GEMINI_API_KEY)

# Exposed for compatibility with app.py references
XAI_MODEL_NAME = GEMINI_MODEL_NAME

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


def _build_contents(conversation_history: list) -> list:
    """Convert internal history format to Gemini contents format.
    Gemini requires the list to start with a user turn and alternate roles."""
    recent = conversation_history[-10:]
    # Drop any leading model turns so the list starts with a user turn
    start = next((i for i, m in enumerate(recent) if m["role"] == "user"), 0)
    return [
        types.Content(
            role="model" if m["role"] == "ai" else "user",
            parts=[types.Part(text=m["content"])]
        )
        for m in recent[start:]
    ]


def generate_summary(session: dict):
    """生成近期对话摘要"""
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
        response = _client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=summary_prompt
        )
        new_summary = response.text.strip()
        if new_summary:
            session['summary'] = new_summary
    except Exception as e:
        print(f"⚠️ Failed to generate summary: {e}")


def generate_xai_explanation(user_text: str, sentiment_data: dict) -> str:
    """
    使用 Gemini 生成 XAI 解释。
    根据用户输入的语言动态切换 Prompt 语言，确保输出语言一致。
    """
    top_emotion = sentiment_data.get("top_emotion", "neutral")

    if contains_chinese(user_text):
        xai_prompt = f"""
        请分析以下用户输入和检测到的情绪。

        用户输入: "{user_text}"
        检测到的情绪标签: {top_emotion}

        任务：
        1. 用第三人称（如"系统检测到..."）简要解释为什么系统认为用户处于"{top_emotion}"情绪。
        2. 说明系统在下一条回复中的目标是什么（如"系统旨在..."）。
        3. 解释必须简洁（1-2句话）。

        **强制要求**：必须使用**中文**直接回答，不要翻译用户的话。
        """
    else:
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
        response = _client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=xai_prompt,
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=150)
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ XAI Gen Error: {e}")
        return "System analysis unavailable."


def get_llm_response_stream(participant_id: str, user_input: str):
    """
    处理聊天逻辑和 Gemini 流式响应 (使用主模型)。
    """
    session = get_session(participant_id)
    conversation_history = session['history']
    summary_memory = session['summary']

    # 1. 添加用户输入
    conversation_history.append({"role": "user", "content": user_input})

    # 2. 动态决定 System Prompt (语言跟随)
    if contains_chinese(user_input):
        system_inst = (
            "你是一个温柔且富有同理心的对话伙伴。"
            "请始终以自然、像人一样的方式回应。"
            "请务必使用中文进行回复。"
            "不要评价用户的语言能力。"
        )
    else:
        system_inst = SYSTEM_PROMPT

    if summary_memory:
        system_inst += f"\n\n[Conversation Context Summary]\n{summary_memory}"

    # 3. 构建 Gemini contents
    contents = _build_contents(conversation_history)

    # 供调试查看
    session['full_prompt'] = f"[system]\n{system_inst}\n\n[contents]\n{contents}"

    # 4. 流式响应
    full_ai_reply = ""
    try:
        for chunk in _client.models.generate_content_stream(
            model=GEMINI_MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_inst)
        ):
            if chunk.text:
                full_ai_reply += chunk.text
                yield chunk.text.encode('utf-8')

    except Exception as e:
        yield f"⚠️ Backend LLM error: {e}".encode('utf-8')

    finally:
        if full_ai_reply:
            conversation_history.append({"role": "ai", "content": full_ai_reply.strip()})
            session['turn_count'] += 1
            if len(conversation_history) % (SUMMARY_INTERVAL * 2) == 0:
                generate_summary(session)
        print("✅ Streaming Complete")
