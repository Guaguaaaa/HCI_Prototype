import os
import time
import secrets
import hashlib
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import ReturnDocument
import certifi
from config import VERSION_MAP

# 1. Load environment variables and connect to MongoDB
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ CRITICAL ERROR: MONGO_URI not found. Please check your .env file.")

client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
PRODUCTION_DB_NAME = os.getenv("MONGO_DB_NAME", "hci_experiment")
TEST_DB_NAME = os.getenv("MONGO_TEST_DB_NAME", "hci_experiment_test")
prod_db = client[PRODUCTION_DB_NAME]
test_db = client[TEST_DB_NAME]


def _collections_for_db(db):
    return {
        "participants": db["participants_status"],
        "experiment_data": db["experiment_events"],
        "turn_data": db["dialogue_turns"],
        "contacts": db["follow_up_contacts"],
        "invite_batches": db["invite_batches"],
        "invite_links": db["invite_links"],
    }


prod_collections = _collections_for_db(prod_db)
test_collections = _collections_for_db(test_db)

def create_data_dir():
    """Placeholder for backward compatibility. MongoDB doesn't need local directories."""
    print("✅ MongoDB Ready. (Local directory creation skipped)")

    try:
        for collection_set in (prod_collections, test_collections):
            collection_set["participants"].create_index("participant_id", unique=True)
            collection_set["invite_batches"].create_index("batch_id", unique=True)
            collection_set["invite_links"].create_index("token_hash", unique=True)
            collection_set["invite_links"].create_index("participant_id", unique=True)
            collection_set["invite_links"].create_index("batch_id")
    except Exception as e:
        print(f"⚠️ Failed to ensure MongoDB indexes: {e}")


def _collections_for_invite_type(invite_type: str):
    return test_collections if invite_type == "test" else prod_collections


def _find_participant_collections(participant_id: str):
    if prod_collections["participants"].find_one({"participant_id": participant_id}, {"_id": 1}):
        return prod_collections
    if test_collections["participants"].find_one({"participant_id": participant_id}, {"_id": 1}):
        return test_collections
    return None


def _find_invite_collections_by_token(token: str):
    token_hash = _hash_invite_token(token)
    if prod_collections["invite_links"].find_one({"token_hash": token_hash}, {"_id": 1}):
        return prod_collections
    if test_collections["invite_links"].find_one({"token_hash": token_hash}, {"_id": 1}):
        return test_collections
    return None


def _find_invite_collections_by_participant(participant_id: str):
    if prod_collections["invite_links"].find_one({"participant_id": participant_id}, {"_id": 1}):
        return prod_collections
    if test_collections["invite_links"].find_one({"participant_id": participant_id}, {"_id": 1}):
        return test_collections
    return None


def _find_batch_collections(batch_id: str):
    if prod_collections["invite_batches"].find_one({"batch_id": batch_id}, {"_id": 1}):
        return prod_collections
    if test_collections["invite_batches"].find_one({"batch_id": batch_id}, {"_id": 1}):
        return test_collections
    return None

def get_participant_status(participant_id: str) -> dict:
    """Fetch participant status from MongoDB"""
    collections = _find_participant_collections(participant_id)
    if not collections:
        return {}
    status = collections["participants"].find_one({"participant_id": participant_id}, {"_id": 0})
    return status if status else {}

def get_participant_condition(participant_id: str) -> str:
    status = get_participant_status(participant_id)
    return status.get("condition", "UNKNOWN")

def get_participant_language(participant_id: str) -> str:
    status = get_participant_status(participant_id)
    return status.get("language", "en")

def save_participant_data(participant_id: str, step_name: str, data: dict):
    """Save general experiment data (questionnaires, etc.) to experiment_events"""
    collections = _find_participant_collections(participant_id)
    if not collections:
        print(f"❌ Failed to save data: participant {participant_id} not found in any database.")
        return False

    record = {
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "participant_id": participant_id,
        "step": step_name,
        "data": data
    }
    try:
        collections["experiment_data"].insert_one(record)
        print(f"✅ Data saved for PID {participant_id} at step {step_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to save data: {e}")
        return False

def init_participant_session(participant_id: str, condition_order: str, language: str, invite_type: str = "participant"):
    """Initialize session, write to status and event collections"""
    condition_order_upper = condition_order.upper()
    if condition_order_upper not in ["AB", "BA"]:
        raise ValueError(f"Invalid condition_order: {condition_order}. Must be 'AB' or 'BA'.")
    collections = _collections_for_invite_type(invite_type)

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

    try:
        collections["experiment_data"].insert_one({
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "participant_id": participant_id,
            "step": "INIT",
            "data": init_data
        })
        collections["participants"].update_one(
            {"participant_id": participant_id},
            {"$set": init_data},
            upsert=True
        )
        print(f"🎉 Session initialized for PID {participant_id} in {condition_order_upper} order. Language: {language}")
        return "/html/demographics.html"
    except Exception as e:
        print(f"❌ Failed to init session status: {e}")
        return "/html/admin_setup.html?error=db_error"


def _hash_invite_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_invite_token() -> str:
    return secrets.token_urlsafe(24)


def generate_participant_id() -> str:
    return f"P_{secrets.token_hex(8).upper()}"


def create_invite_batch(batch_name: str, language: str, condition_order: str, quantity: int, invite_type: str):
    collections = _collections_for_invite_type(invite_type)
    timestamp = time.time()
    created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    batch_id = f"batch_{secrets.token_hex(8)}"

    batch_doc = {
        "batch_id": batch_id,
        "batch_name": batch_name,
        "language": language,
        "condition_order": condition_order,
        "quantity": quantity,
        "invite_type": invite_type,
        "created_at": created_at,
        "created_ts": timestamp,
    }

    invite_docs = []
    invite_results = []
    for _ in range(quantity):
        token = generate_invite_token()
        participant_id = generate_participant_id()
        invite_doc = {
            "batch_id": batch_id,
            "token": token,
            "token_hash": _hash_invite_token(token),
            "participant_id": participant_id,
            "language": language,
            "condition_order": condition_order,
            "invite_type": invite_type,
            "status": "unused",
            "created_at": created_at,
            "created_ts": timestamp,
            "first_opened_at": None,
            "first_opened_ts": None,
            "last_opened_at": None,
            "last_opened_ts": None,
            "completed_at": None,
            "completed_ts": None,
            "disabled_at": None,
            "disabled_ts": None,
        }
        invite_docs.append(invite_doc)
        invite_results.append({
            "token": token,
            "participant_id": participant_id,
            "language": language,
            "condition_order": condition_order,
            "invite_type": invite_type,
            "status": "unused",
        })

    collections["invite_batches"].insert_one(batch_doc)
    if invite_docs:
        collections["invite_links"].insert_many(invite_docs)

    return {
        "batch_id": batch_id,
        "batch_name": batch_name,
        "language": language,
        "condition_order": condition_order,
        "quantity": quantity,
        "invite_type": invite_type,
        "database_label": "test" if invite_type == "test" else "production",
        "created_at": created_at,
        "links": invite_results,
    }


def get_invite_by_token(token: str) -> dict:
    collections = _find_invite_collections_by_token(token)
    if not collections:
        return {}
    invite = collections["invite_links"].find_one({"token_hash": _hash_invite_token(token)}, {"_id": 0})
    return invite if invite else {}


def update_invite_last_opened(participant_id: str):
    collections = _find_invite_collections_by_participant(participant_id)
    if not collections:
        return
    now_ts = time.time()
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_ts))
    collections["invite_links"].update_one(
        {"participant_id": participant_id},
        {"$set": {"last_opened_at": now_str, "last_opened_ts": now_ts}}
    )


def redeem_invite_token(token: str) -> dict:
    collections = _find_invite_collections_by_token(token)
    if not collections:
        return {}

    token_hash = _hash_invite_token(token)
    now_ts = time.time()
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_ts))

    invite = collections["invite_links"].find_one({"token_hash": token_hash}, {"_id": 0})

    status = invite.get("status")
    if status in {"completed", "disabled"}:
        return invite

    if status == "unused":
        updated = collections["invite_links"].find_one_and_update(
            {"token_hash": token_hash, "status": "unused"},
            {"$set": {
                "status": "in_progress",
                "first_opened_at": now_str,
                "first_opened_ts": now_ts,
                "last_opened_at": now_str,
                "last_opened_ts": now_ts,
            }},
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0}
        )
        if updated:
            return updated
        invite = collections["invite_links"].find_one({"token_hash": token_hash}, {"_id": 0})
        return invite if invite else {}

    if status == "in_progress":
        update_invite_last_opened(invite["participant_id"])
        invite["last_opened_at"] = now_str
        invite["last_opened_ts"] = now_ts
        return invite

    return invite


def mark_invite_completed(participant_id: str) -> bool:
    collections = _find_invite_collections_by_participant(participant_id)
    if not collections:
        return True
    now_ts = time.time()
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_ts))
    result = collections["invite_links"].update_one(
        {"participant_id": participant_id, "status": {"$ne": "completed"}},
        {"$set": {
            "status": "completed",
            "completed_at": now_str,
            "completed_ts": now_ts,
            "last_opened_at": now_str,
            "last_opened_ts": now_ts,
        }}
    )
    return result.acknowledged


def get_invite_for_participant(participant_id: str) -> dict:
    collections = _find_invite_collections_by_participant(participant_id)
    if not collections:
        return {}
    invite = collections["invite_links"].find_one({"participant_id": participant_id}, {"_id": 0})
    return invite if invite else {}


def list_invite_batches() -> list:
    batches = []
    for db_label, collections in (("production", prod_collections), ("test", test_collections)):
        current_batches = list(collections["invite_batches"].find({}, {"_id": 0}).sort("created_ts", -1))
        for batch in current_batches:
            counts = {"unused": 0, "in_progress": 0, "completed": 0, "disabled": 0}
            for row in collections["invite_links"].aggregate([
                {"$match": {"batch_id": batch["batch_id"]}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]):
                counts[row["_id"]] = row["count"]
            batch["status_counts"] = counts
            batch["database_label"] = db_label
        batches.extend(current_batches)
    batches.sort(key=lambda row: row.get("created_ts", 0), reverse=True)
    return batches


def list_invite_links_for_batch(batch_id: str) -> list:
    collections = _find_batch_collections(batch_id)
    if not collections:
        return []
    return list(
        collections["invite_links"].find(
            {"batch_id": batch_id},
            {
                "_id": 0,
                "batch_id": 1,
                "token": 1,
                "participant_id": 1,
                "language": 1,
                "condition_order": 1,
                "invite_type": 1,
                "status": 1,
                "created_at": 1,
                "first_opened_at": 1,
                "last_opened_at": 1,
                "completed_at": 1,
            }
        ).sort("created_ts", 1)
    )

def update_participant_condition(participant_id: str):
    """Switch condition after Washout (AB -> BA or BA -> AB)"""
    status_data = get_participant_status(participant_id)
    if not status_data:
        return False
    collections = _find_participant_collections(participant_id)
    if not collections:
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
        collections["participants"].update_one(
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
    collections = _find_participant_collections(participant_id)
    if not collections:
        return False
    try:
        collections["participants"].update_one(
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
    collections = _find_participant_collections(participant_id)
    if not collections:
        return False
    try:
        collections["participants"].update_one(
            {"participant_id": participant_id},
            {"$set": {"washout_start_ts": start_ts}}
        )
        return True
    except Exception as e:
        print(f"❌ Failed to record washout start: {e}")
        return False

def save_turn_data(participant_id: str, turn_data: dict):
    """Save individual dialogue turns into the dialogue_turns collection"""
    collections = _find_participant_collections(participant_id)
    if not collections:
        print(f"❌ Failed to save turn data: participant {participant_id} not found in any database.")
        return False
    record = {
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "participant_id": participant_id,
        "step": "DIALOGUE_TURN",
        "data": turn_data
    }
    try:
        collections["turn_data"].insert_one(record)
        print(f"✅ Turn data saved for PID {participant_id}, Turn {turn_data.get('turn')}")
        return True
    except Exception as e:
        print(f"❌ Failed to save turn data: {e}")
        return False

def save_contact_email(participant_id: str, email: str):
    """Save contact information for follow-up interviews"""
    collections = _find_participant_collections(participant_id)
    if not collections:
        print(f"❌ Failed to save contact data: participant {participant_id} not found in any database.")
        return False
    try:
        collections["contacts"].insert_one({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "participant_id": participant_id,
            "email": email
        })
        print(f"✅ Contact data saved for PID {participant_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to save contact data: {e}")
        return False


def clear_database_contents(database_label: str) -> dict:
    collections = test_collections if database_label == "test" else prod_collections
    deleted = {}
    for name, collection in collections.items():
        result = collection.delete_many({})
        deleted[name] = result.deleted_count
    return deleted
