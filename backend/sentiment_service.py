import torch
from transformers import pipeline
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量持有模型
sentiment_analyzer = None

# 模型名称：支持中文和英文的 GoEmotions 模型
MODEL_NAME = "SchuylerH/bert-multilingual-go-emtions"

# Ekman 基本情绪列表
EKMAN_EMOTIONS = [
    "anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"
]

# 极性权重 (用于计算 Signed Score)
EMOTION_POLARITY = {
    "joy": 1.0,
    "neutral": 0.0,
    "surprise": 0.1,
    "sadness": -1.0,
    "fear": -1.0,
    "anger": -1.0,
    "disgust": -1.0
}

# 映射字典：28 -> 7
EMOTION_MAPPING = {
    "admiration": "joy", "amusement": "joy", "approval": "joy", "caring": "joy",
    "desire": "joy", "excitement": "joy", "gratitude": "joy", "joy": "joy",
    "love": "joy", "optimism": "joy", "pride": "joy", "relief": "joy",
    "disappointment": "sadness", "embarrassment": "sadness", "grief": "sadness",
    "remorse": "sadness", "sadness": "sadness",
    "anger": "anger", "annoyance": "anger", "disapproval": "anger",
    "fear": "fear", "nervousness": "fear",
    "confusion": "surprise", "curiosity": "surprise", "realization": "surprise",
    "surprise": "surprise",
    "disgust": "disgust",
    "neutral": "neutral"
}


def init_sentiment_model():
    global sentiment_analyzer
    if sentiment_analyzer is not None:
        return

    device = -1
    if torch.cuda.is_available():
        device = 0
        logger.info("🚀 CUDA detected. Using GPU.")
    elif torch.backends.mps.is_available():
        device = "mps"
        logger.info("🍎 Apple Silicon (MPS) detected.")
    else:
        logger.info("🐢 Using CPU.")

    try:
        logger.info(f"⏳ Loading Sentiment Model ({MODEL_NAME})...")
        sentiment_analyzer = pipeline(
            "text-classification",
            model=MODEL_NAME,
            top_k=None,
            device=device
        )
        logger.info("✅ Sentiment Model Loaded.")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")


def calculate_weighted_score(emotion_label: str, confidence: float) -> float:
    """计算加权分数 = 极性 * 置信度"""
    if not emotion_label or not isinstance(confidence, (int, float)):
        return 0.0
    weight = EMOTION_POLARITY.get(emotion_label.lower(), 0.0)
    return weight * confidence


def analyze_sentiment(text: str) -> dict:
    """
    返回:
    - top_emotion: 分数最高的 Ekman 情绪
    - top_score: 该情绪的聚合得分 (可能 > 1.0)
    - ekman_scores: 7种基本情绪的得分分布
    - raw_scores: 原始模型的 28 种情绪得分
    """
    if not sentiment_analyzer:
        return {
            "top_emotion": "neutral", "top_score": 0.0,
            "ekman_scores": {}, "raw_scores": {}
        }

    try:
        # 截断输入防止报错
        results = sentiment_analyzer(text[:512])

        ekman_scores = {e: 0.0 for e in EKMAN_EMOTIONS}
        raw_scores = {}

        # 聚合逻辑
        for item in results[0]:
            raw_label = item['label']
            score = item['score']

            # 1. 记录原始分数
            raw_scores[raw_label] = score

            # 2. 聚合到 Ekman
            target_emotion = EMOTION_MAPPING.get(raw_label)
            if target_emotion:
                ekman_scores[target_emotion] += score

        # 找出最高分
        top_emotion = max(ekman_scores, key=ekman_scores.get)
        top_score = ekman_scores[top_emotion]

        return {
            "top_emotion": top_emotion,
            "top_score": top_score,
            "ekman_scores": ekman_scores,  # 7维数据
            "raw_scores": raw_scores  # 28维数据 (修复：确保返回这个)
        }

    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return {
            "top_emotion": "neutral", "top_score": 0.0,
            "ekman_scores": {}, "raw_scores": {}
        }