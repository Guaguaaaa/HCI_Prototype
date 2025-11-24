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
    针对小模型优化：加入 Few-Shot 示例 (Demonstration) 增强理解力。
    """
    if not text:
        return {"top_emotion": "neutral", "top_score": 0.0, "raw_scores": {}}

    # --- 1. 动态构建 Prompt (加入 Few-Shot 示例) ---
    if contains_chinese(text):
        # 中文 Prompt - 强化版
        prompt = f"""
        你是一个敏锐的心理分析师。请判断用户输入中最主要的情绪。
        必须从以下 7 类中选择一个: {EKMAN_EMOTIONS}。
        
        **参考示例 (Few-Shot Examples)**:
        - 用户: "你好，我想聊聊天。" -> 标签: neutral
        - 用户: "我刚刚分手了。" -> 标签: sadness (隐含了失去和痛苦)
        - 用户: "这简直不可理喻！" -> 标签: anger
        - 用户: "我真的很担心明天的考试。" -> 标签: fear
        - 用户: "没想到是你！" -> 标签: surprise
        
        **当前用户输入**: "{text}"
        
        **要求**:
        1. 如果用户陈述了负面事件（如分手、失败、生病），即使语气平静，也必须标记为负面情绪（如 sadness 或 fear），绝不能标为 neutral。
        2. 仅返回 JSON。
        
        Response format: {{"emotion": "label", "confidence": 0.95}}
        """
    else:
        # 英文 Prompt - 强化版
        prompt = f"""
        You are a psychological analyst. Classify the dominant emotion of the user input into EXACTLY ONE of: {EKMAN_EMOTIONS}.
        
        **Examples**:
        - User: "Hi, can we talk?" -> Label: neutral
        - User: "I just broke up." -> Label: sadness (Implicit loss implies sadness)
        - User: "This is ridiculous!" -> Label: anger
        - User: "I am worried about the test." -> Label: fear
        
        **Current User Input**: "{text}"
        
        **Guideline**:
        If the user describes a negative event (e.g., break up, failure), label it as 'sadness' or 'fear', NOT 'neutral'.
        
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