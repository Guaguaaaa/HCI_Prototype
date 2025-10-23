import json
import os
import time
from backend.config import DATA_DIR, VERSION_MAP


def create_data_dir():
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"✅ Data directory ensured: {DATA_DIR}")


def get_participant_status(participant_id: str) -> dict:
    """从状态文件中获取受试者的实验条件和其他状态信息"""
    status_path = os.path.join(DATA_DIR, f"P_{participant_id}_status.json")
    try:
        with open(status_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"❌ Error reading status file: {e}")
        return {}


def get_participant_condition(participant_id: str) -> str:
    """获取受试者的实验条件 (XAI/NON_XAI)"""
    status = get_participant_status(participant_id)
    return status.get("condition", "UNKNOWN")  # Default to UNKNOWN if not set


# 获取受试者的语言
def get_participant_language(participant_id: str) -> str:
    """获取受试者的实验语言 (en/zh-CN)"""
    status = get_participant_status(participant_id)
    # 默认语言为英文，以防万一
    return status.get("language", "en")


def save_participant_data(participant_id: str, step_name: str, data: dict):
    """
    通用数据保存函数：将一个步骤数据（如问卷、初始化）以 JSON Line 格式追加写入。
    """
    create_data_dir()
    file_path = os.path.join(DATA_DIR, f"P_{participant_id}.jsonl")

    record = {
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "participant_id": participant_id,
        "step": step_name,
        "data": data
    }

    json_line = json.dumps(record, ensure_ascii=False)

    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json_line + '\n')

        print(f"✅ Data saved for PID {participant_id} at step {step_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to save data: {e}")
        return False


def init_participant_session(participant_id: str, condition: str, language: str):
    """
    初始化受试者会话，保存实验条件和开始时间。
    返回下一个页面的 URL (人口统计页面)。
    """
    if condition.upper() not in VERSION_MAP:
        raise ValueError(f"Invalid condition: {condition}. Must be one of {list(VERSION_MAP.keys())}")

    # 1. 保存初始化数据 (将条件和开始时间作为第一个记录)
    init_data = {
        "condition": condition.upper(),
        "language": language,
        "start_time": time.time(),
        "version_url": VERSION_MAP[condition.upper()]
    }
    save_participant_data(participant_id, "INIT", init_data)

    # 2. 写入一个单独的 JSON 文件来保存**会话状态** (用于 LLM 部分的引用)
    status_path = os.path.join(DATA_DIR, f"P_{participant_id}_status.json")
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(init_data, f, ensure_ascii=False, indent=4)

    print(f"🎉 Session initialized for PID {participant_id} in {condition} condition. Language: {language}")

    # 返回下一步的 URL (人口统计页面)
    return "/html/demographics.html"


def save_turn_data(participant_id: str, turn_data: dict):
    """
    将一轮对话的分析数据以 JSON Line 格式追加写入其专属文件。
    """
    create_data_dir()

    # 构造文件路径
    file_path = os.path.join(DATA_DIR, f"P_{participant_id}.jsonl")

    # 构造完整的记录对象
    record = {
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "participant_id": participant_id,
        "step": "DIALOGUE_TURN",  # 使用新的步骤名称
        "data": turn_data
    }

    json_line = json.dumps(record, ensure_ascii=False)

    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json_line + '\n')

        print(f"✅ Turn data saved for PID {participant_id}, Turn {turn_data.get('turn')}")
        return True
    except Exception as e:
        print(f"❌ Failed to save turn data: {e}")
        return False