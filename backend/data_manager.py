import os
import time
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
from backend.config import VERSION_MAP

# 1. Load environment variables and connect to MongoDB
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ CRITICAL ERROR: MONGO_URI not found. Please check your .env file.")

client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = client["hci_experiment"] # Database name

# 2. Define core data collections
db_participants = db["participants_status"]
db_experiment_data = db["experiment_events"]
db_turn_data = db["dialogue_turns"]
db_contacts = db["follow_up_contacts"] # For saving follow-up interview emails

def create_data_dir():
    """Placeholder for backward compatibility. MongoDB doesn't need local directories."""
    print("✅ MongoDB Ready. (Local directory creation skipped)")

def get_participant_status(participant_id: str) -> dict:
    """Fetch participant status from MongoDB"""
    status = db_participants.find_one({"participant_id": participant_id}, {"_id": 0})
    return status if status else {}

def get_participant_condition(participant_id: str) -> str:
    status = get_participant_status(participant_id)
    return status.get("condition", "UNKNOWN")

def get_participant_language(participant_id: str) -> str:
    status = get_participant_status(participant_id)
    return status.get("language", "en")

def save_participant_data(participant_id: str, step_name: str, data: dict):
    """Save general experiment data (questionnaires, etc.) to experiment_events"""
    record = {
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "participant_id": participant_id,
        "step": step_name,
        "data": data
    }
    try:
        db_experiment_data.insert_one(record)
        print(f"✅ Data saved for PID {participant_id} at step {step_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to save data: {e}")
        return False

def init_participant_session(participant_id: str, condition_order: str, language: str):
    """Initialize session, write to status and event collections"""
    condition_order_upper = condition_order.upper()
    if condition_order_upper not in ["AB", "BA"]:
        raise ValueError(f"Invalid condition_order: {condition_order}. Must be 'AB' or 'BA'.")

    initial_condition = "XAI" if condition_order_upper == "AB" else "NON_XAI"

    init_data = {
        "participant_id": participant_id,
        "condition": initial_condition,
        "condition_order": condition_order_upper,
        "language": language,
        "start_time": time.time(),
        "version_url": VERSION_MAP[initial_condition],
        "current_step_index": -1
    }

    # 1. Record the initial event
    save_participant_data(participant_id, "INIT", init_data)

    # 2. Update or insert participant status (upsert=True)
    try:
        db_participants.update_one(
            {"participant_id": participant_id},
            {"$set": init_data},
            upsert=True
        )
        print(f"🎉 Session initialized for PID {participant_id} in {condition_order_upper} order. Language: {language}")
        return "/html/demographics.html"
    except Exception as e:
        print(f"❌ Failed to init session status: {e}")
        return "/html/admin_setup.html?error=db_error"

def update_participant_condition(participant_id: str):
    """Switch condition after Washout (AB -> BA or BA -> AB)"""
    status_data = get_participant_status(participant_id)
    if not status_data:
        return False

    current_condition = status_data.get("condition")
    condition_order = status_data.get("condition_order")

    new_condition = "UNKNOWN"
    if condition_order == "AB" and current_condition == "XAI":
        new_condition = "NON_XAI"
    elif condition_order == "BA" and current_condition == "NON_XAI":
        new_condition = "XAI"
    else:
        new_condition = "NON_XAI" if current_condition == "XAI" else "XAI"

    try:
        db_participants.update_one(
            {"participant_id": participant_id},
            {"$set": {
                "condition": new_condition,
                "washout_completed": True
            }}
        )
        print(f"✅ PID {participant_id} condition switched to {new_condition}")
        return True
    except Exception as e:
        print(f"❌ Failed to update participant condition: {e}")
        return False

def update_participant_step(participant_id: str, new_step_index: int):
    """Update the current step index of the user"""
    try:
        db_participants.update_one(
            {"participant_id": participant_id},
            {"$set": {"current_step_index": new_step_index}}
        )
        print(f"✅ PID {participant_id} advanced to step index {new_step_index}")
        return True
    except Exception as e:
        print(f"❌ Failed to update participant step: {e}")
        return False

def record_washout_start(participant_id: str, start_ts: float):
    """Helper function to record washout start time for app.py"""
    try:
        db_participants.update_one(
            {"participant_id": participant_id},
            {"$set": {"washout_start_ts": start_ts}}
        )
        return True
    except Exception as e:
        print(f"❌ Failed to record washout start: {e}")
        return False

def save_turn_data(participant_id: str, turn_data: dict):
    """Save individual dialogue turns into the dialogue_turns collection"""
    record = {
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "participant_id": participant_id,
        "step": "DIALOGUE_TURN",
        "data": turn_data
    }
    try:
        db_turn_data.insert_one(record)
        print(f"✅ Turn data saved for PID {participant_id}, Turn {turn_data.get('turn')}")
        return True
    except Exception as e:
        print(f"❌ Failed to save turn data: {e}")
        return False

def save_contact_email(participant_id: str, email: str):
    """Save contact information for follow-up interviews"""
    try:
        db_contacts.insert_one({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "participant_id": participant_id,
            "email": email
        })
        print(f"✅ Contact data saved for PID {participant_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to save contact data: {e}")
        return False
