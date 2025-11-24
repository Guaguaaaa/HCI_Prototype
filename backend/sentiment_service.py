import requests
import json
import logging
import re
# 复用配置
from backend.config import OLLAMA_API_URL, XAI_MODEL_NAME

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ekman 基本情绪列表
EKMAN_EMOTIONS = [
    "anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"
]

# 极性权重
EMOTION_POLARITY = {
    "joy": 1.0, "neutral": 0.0, "surprise": 0.1,
    "sadness": -1.0, "fear": -1.0, "anger": -1.0, "disgust": -1.0
}


def init_sentiment_model():
    """基于 LLM 的方案不需要预加载模型，只需确认 Ollama 服务在线即可"""
    logger.info(f"🚀 Sentiment Engine using LLM ({XAI_MODEL_NAME}). Ready.")


def contains_chinese(text: str) -> bool:
    """检查是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def calculate_weighted_score(emotion_label: str, confidence: float) -> float:
    if not emotion_label: return 0.0
    weight = EMOTION_POLARITY.get(emotion_label.lower(), 0.0)
    return weight * confidence


def analyze_sentiment(text: str) -> dict:
    """
    使用 LLM 进行 Zero-shot 情感分类。
    根据输入语言动态切换 Prompt，提高小模型的准确率。
    """
    if not text:
        return {"top_emotion": "neutral", "top_score": 0.0, "raw_scores": {}}

    # --- 1. 动态构建 Prompt ---
    if contains_chinese(text):
        # 中文 Prompt
        prompt = f"""
你是一个心理分析专家。请判断以下用户输入中隐含的最主要情绪，并必须从以下列表中选择一个：{EKMAN_EMOTIONS}。

**判断指南**：
1. **隐含情绪**：不要只看表面词汇。如果用户描述了损失、失败或分离（如“分手”、“挂科”），即使语气平淡，也应归类为 'sadness'。
2. **中性场景**：只有普通的问候或信息询问才是 'neutral'。
3. **输出格式**：仅返回一个 JSON 对象。

用户输入: "{text}"

请严格按照此 JSON 格式回答: {{"emotion": "label", "confidence": 0.95}}
"""
    else:
        # 英文 Prompt
        prompt = f"""
You are an expert psychological analyst. Classify the underlying emotion of the following user input into EXACTLY ONE of these categories: {EKMAN_EMOTIONS}.

**Guidelines:**
1. **Implicit Emotion**: Look beyond keywords. If the user describes a loss (e.g., "break up", "failed"), it is 'sadness' even without sad words.
2. **Context**: Greetings or simple questions are 'neutral'. 
3. **Output Format**: Respond ONLY with a JSON object.

User Input: "{text}"

Response format: {{"emotion": "label", "confidence": 0.95}}
"""

    # --- 2. 调用 LLM ---
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": XAI_MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json",  # 强制 JSON
                "options": {"temperature": 0.1}  # 低温保证稳定
            },
            timeout=5
        )

        if response.status_code == 200:
            res_json = response.json()
            # 解析响应内容
            try:
                content = json.loads(res_json.get("response", "{}"))
            except json.JSONDecodeError:
                logger.warning(f"LLM JSON Decode Error. Raw response: {res_json.get('response')}")
                content = {}

            emotion = content.get("emotion", "neutral").lower()
            confidence = content.get("confidence", 0.9)

            # 容错映射
            if emotion not in EKMAN_EMOTIONS:
                if "happy" in emotion:
                    emotion = "joy"
                elif "sad" in emotion:
                    emotion = "sadness"
                elif "angry" in emotion:
                    emotion = "anger"
                else:
                    emotion = "neutral"

            # 构造伪造分布
            raw_scores = {e: (confidence if e == emotion else 0.01) for e in EKMAN_EMOTIONS}

            return {
                "top_emotion": emotion,
                "top_score": confidence,
                "ekman_scores": raw_scores,
                "raw_scores": raw_scores,
                "model_used": f"LLM-{XAI_MODEL_NAME}"
            }

    except Exception as e:
        logger.error(f"LLM Sentiment Analysis Failed: {e}")

    # Fallback
    return {"top_emotion": "neutral", "top_score": 0.0, "ekman_scores": {}, "raw_scores": {}}


# 测试
if __name__ == "__main__":
    init_sentiment_model()
    print("--- Testing Chinese (Should be Sadness) ---")
    print(analyze_sentiment("我前几天分手了"))
    print("\n--- Testing English (Should be Neutral) ---")
    print(analyze_sentiment("Can we chat?"))