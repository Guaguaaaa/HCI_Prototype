# backend/sentiment_service.py (适配 14B 大模型版)
import requests
import json
import logging
import re
from backend.config import OLLAMA_API_URL, XAI_MODEL_NAME  # 这里会自动读取到 "qwen3:14b"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EKMAN_EMOTIONS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
EMOTION_POLARITY = {"joy": 1.0, "neutral": 0.0, "surprise": 0.1, "sadness": -1.0, "fear": -1.0, "anger": -1.0,
                    "disgust": -1.0}


def init_sentiment_model():
    logger.info(f"🚀 Sentiment Engine using Main LLM ({XAI_MODEL_NAME}). Ready.")


def contains_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def calculate_weighted_score(emotion_label: str, confidence: float) -> float:
    if not emotion_label: return 0.0
    weight = EMOTION_POLARITY.get(emotion_label.lower(), 0.0)
    return weight * confidence


def analyze_sentiment(text: str) -> dict:
    if not text:
        return {"top_emotion": "neutral", "top_score": 0.0, "raw_scores": {}}

    # 14B 模型足够聪明，不需要复杂的 CoT，直接给清晰的定义即可
    if contains_chinese(text):
        prompt = f"""
        请分析用户输入的情感，并从以下列表中选择最准确的一个标签：{EKMAN_EMOTIONS}。
        
        用户输入: "{text}"
        
        判断逻辑：
        1. **Joy**: 表达开心、喜爱、赞美（如“我爱吃苹果”、“太棒了”）。
        2. **Sadness**: 表达失去、失败、难过（如“分手”、“挂科”、“不开心”）。
        3. **Neutral**: 普通陈述、问候（如“你好”、“我想聊聊”）。
        4. **Anger/Fear/Disgust/Surprise**: 对应其标准定义。
        
        请直接返回 JSON 格式：
        {{
            "emotion": "label",
            "confidence": 0.95
        }}
        """
    else:
        prompt = f"""
        Analyze the user's emotion and select the best label from: {EKMAN_EMOTIONS}.
        
        User Input: "{text}"
        
        Guidelines:
        1. **Joy**: Happiness, love, liking something (e.g., "I love apples").
        2. **Sadness**: Loss, failure, unhappiness (e.g., "break up", "failed").
        3. **Neutral**: General statements, greetings.
        
        Respond ONLY in JSON:
        {{
            "emotion": "label",
            "confidence": 0.95
        }}
        """

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": XAI_MODEL_NAME,  # 现在指向 14B
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1}
            },
            timeout=10  # 大模型可能需要稍长一点点的时间
        )

        if response.status_code == 200:
            res_json = response.json()
            content = json.loads(res_json.get("response", "{}"))
            emotion = content.get("emotion", "neutral").lower()
            confidence = content.get("confidence", 0.9)

            # 简单的容错
            if emotion not in EKMAN_EMOTIONS:
                if "happy" in emotion or "love" in emotion:
                    emotion = "joy"
                elif "sad" in emotion:
                    emotion = "sadness"
                else:
                    emotion = "neutral"

            raw_scores = {e: (confidence if e == emotion else 0.01) for e in EKMAN_EMOTIONS}

            return {
                "top_emotion": emotion,
                "top_score": confidence,
                "ekman_scores": raw_scores,
                "raw_scores": raw_scores,
                "model_used": f"LLM-{XAI_MODEL_NAME}"
            }

    except Exception as e:
        logger.error(f"Analysis Failed: {e}")
        return {"top_emotion": "neutral", "top_score": 0.0, "ekman_scores": {}, "raw_scores": {}}