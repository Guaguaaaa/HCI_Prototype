import requests
import json
from backend.config import OLLAMA_API_URL, MODEL_NAME, SYSTEM_PROMPT, SUMMARY_INTERVAL

# === 全局存储 - 参与者会话数据隔离 ===
# Key: participant_id
# Value: {'history': [...], 'summary': '...', 'turn_count': 0, 'sentiment_scores': []}
session_data = {}


def get_session(participant_id: str) -> dict:
    """获取或初始化参与者的会话数据"""
    if participant_id not in session_data:
        session_data[participant_id] = {
            'history': [],
            'summary': "",
            'full_prompt': "",
            'turn_count': 0,  # <--- 回合计数器
            'sentiment_scores': []  # <--- 情绪得分占位符列表
        }
    return session_data[participant_id]


def clear_session(participant_id: str) -> bool:
    """清除特定参与者的会话历史和摘要 (用于新实验开始时)"""
    if participant_id in session_data:
        del session_data[participant_id]
        print(f"🧹 Session cleared for PID {participant_id}")
        return True
    return False


def generate_summary(session: dict):
    """生成近期对话的简短摘要 (用于上下文记忆)"""

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
                "model": MODEL_NAME,
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
            # print("✅ [Summary Updated]:", new_summary)
    except requests.RequestException as e:
        print(f"⚠️ Failed to generate summary: {e}")
    except Exception as e:
        print(f"⚠️ An unexpected error occurred during summary generation: {e}")


def get_llm_response_stream(participant_id: str, user_input: str):
    """
    处理聊天逻辑和 LLM 响应流。
    """
    session = get_session(participant_id)
    conversation_history = session['history']
    summary_memory = session['summary']

    # 1. 将用户输入添加到历史记录 (此历史记录只保留在内存中，不写入文件)
    conversation_history.append({"role": "user", "content": user_input})

    # --- 构建完整的提示词 (Prompt) ---
    full_prompt = ""

    if len(conversation_history) == 1:
        full_prompt += SYSTEM_PROMPT + "\n\n"

    if summary_memory:
        full_prompt += f"The following is a summary of previous conversation to help you understand context:\n{summary_memory}\n\n"

    for msg in conversation_history[-10:]:
        prefix = "User:" if msg["role"] == "user" else "AI:"
        full_prompt += f"{prefix} {msg['content']}\n"

    full_prompt += "AI:"

    session['full_prompt'] = full_prompt
    # print("\n--- LLM Prompt ---")
    # print(full_prompt)
    # print("------------------\n")

    # --- 流式响应 ---
    full_ai_reply = ""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL_NAME,
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
        yield f"⚠️ Failed connecting backend LLM: {e}".encode('utf-8')

    finally:
        if full_ai_reply:
            # 2. 将完整的 AI 回复添加到历史记录
            conversation_history.append({"role": "ai", "content": full_ai_reply.strip()})

            # --- 新增: 增加回合计数 ---
            session['turn_count'] += 1

            if len(conversation_history) % (SUMMARY_INTERVAL * 2) == 0:
                generate_summary(session)
        print("✅ Streaming Complete")