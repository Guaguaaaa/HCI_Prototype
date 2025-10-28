import json
import os
import time
from backend.config import DATA_DIR, VERSION_MAP


# (create_data_dir 保持不变)
def create_data_dir():
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"✅ Data directory ensured: {DATA_DIR}")


# (get_participant_status 保持不变)
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


# (get_participant_condition 保持不变)
def get_participant_condition(participant_id: str) -> str:
    """获取受试者的实验条件 (XAI/NON_XAI)"""
    status = get_participant_status(participant_id)
    return status.get("condition", "UNKNOWN")  # Default to UNKNOWN if not set


# (get_participant_language 保持不变)
def get_participant_language(participant_id: str) -> str:
    """获取受试者的实验语言 (en/zh-CN)"""
    status = get_participant_status(participant_id)
    # 默认语言为英文，以防万一
    return status.get("language", "en")


# (save_participant_data 保持不变)
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


# --- MODIFIED: init_participant_session ---
# def init_participant_session(participant_id: str, condition: str, language: str): # (OLD)
def init_participant_session(participant_id: str, condition_order: str, language: str):
    """
    初始化受试者会话，保存实验条件和开始时间。
    返回下一个页面的 URL (人口统计页面)。
    """
    # if condition.upper() not in VERSION_MAP: # (OLD)
    #     raise ValueError(f"Invalid condition: {condition}. Must be one of {list(VERSION_MAP.keys())}")

    condition_order_upper = condition_order.upper()
    if condition_order_upper not in ["AB", "BA"]:
        raise ValueError(f"Invalid condition_order: {condition_order}. Must be 'AB' or 'BA'.")

    # (NEW) Determine the *initial* condition based on the order
    initial_condition = "XAI" if condition_order_upper == "AB" else "NON_XAI"

    # 1. 保存初始化数据 (将条件和开始时间作为第一个记录)
    init_data = {
        # "condition": condition.upper(), # (OLD)
        "condition": initial_condition,  # (NEW) Store the *first* condition
        "condition_order": condition_order_upper,  # (NEW) Store the counterbalance order
        "language": language,
        "start_time": time.time(),
        # "version_url": VERSION_MAP[condition.upper()], # (OLD)
        "version_url": VERSION_MAP[initial_condition],  # (NEW) Store URL for the *first* condition
        "current_step_index": -1  # 步骤 0 (DEMOGRAPHICS) 是下一步
    }
    save_participant_data(participant_id, "INIT", init_data)

    # 2. 写入一个单独的 JSON 文件来保存**会话状态** (用于 LLM 部分的引用)
    status_path = os.path.join(DATA_DIR, f"P_{participant_id}_status.json")
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(init_data, f, ensure_ascii=False, indent=4)

    # print(f"🎉 Session initialized for PID {participant_id} in {condition} condition. Language: {language}") # (OLD)
    print(f"🎉 Session initialized for PID {participant_id} in {condition_order_upper} order. Language: {language}")

    # 返回下一步的 URL (人口统计页面)
    return "/html/demographics.html"


# --- (NEW) NEW FUNCTION: update_participant_condition ---
def update_participant_condition(participant_id: str):
    """
    (Within-Subjects) Updates the participant's status file to the second condition
    after the washout period.
    """
    status_path = os.path.join(DATA_DIR, f"P_{participant_id}_status.json")
    try:
        # 1. Read existing status
        status_data = get_participant_status(participant_id)
        if not status_data:
            print(f"❌ CRITICAL ERROR: Status file missing for PID {participant_id}. Cannot update condition.")
            return False

        current_condition = status_data.get("condition")
        condition_order = status_data.get("condition_order")

        # 2. Determine the new condition
        new_condition = "UNKNOWN"
        if condition_order == "AB" and current_condition == "XAI":
            new_condition = "NON_XAI"
        elif condition_order == "BA" and current_condition == "NON_XAI":
            new_condition = "XAI"
        else:
            # This case shouldn't happen if logic is correct, but good to check
            print(
                f"⚠️ Warning: Condition update for PID {participant_id} in unexpected state. Order: {condition_order}, Current: {current_condition}")
            # Force set to the *other* condition
            new_condition = "NON_XAI" if current_condition == "XAI" else "XAI"

        status_data["condition"] = new_condition

        # (NEW) Also add a marker that washout is complete
        status_data["washout_completed"] = True

        # 3. Write back the file
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=4)

        print(f"✅ PID {participant_id} condition switched to {new_condition}")
        return True
    except Exception as e:
        print(f"❌ Failed to update participant condition: {e}")
        return False


# --- (OLD) update_participant_step ---
def update_participant_step(participant_id: str, new_step_index: int):
    """
    更新受试者的状态文件，记录他们当前所在的步骤索引。
    """
    status_path = os.path.join(DATA_DIR, f"P_{participant_id}_status.json")
    try:
        # 1. 读取现有状态
        status_data = get_participant_status(participant_id)
        if not status_data:
            print(f"❌ CRITICAL ERROR: Status file missing for PID {participant_id}. Cannot update step.")
            return False

        # 2. 更新步骤索引
        status_data["current_step_index"] = new_step_index

        # 3. 写回文件
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=4)

        print(f"✅ PID {participant_id} advanced to step index {new_step_index}")
        return True
    except Exception as e:
        print(f"❌ Failed to update participant step: {e}")
        return False


# (save_turn_data 保持不变)
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