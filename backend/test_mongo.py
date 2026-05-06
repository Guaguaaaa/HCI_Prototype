import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi  # 👈 新增：导入 certifi

# 加载 .env 文件中的环境变量
load_dotenv()

# 获取连接字符串
uri = os.getenv("MONGO_URI")

if not uri:
    print("❌ 错误：没有找到 MONGO_URI，请检查 .env 文件！")
    exit()

# 👈 修改：在 MongoClient 中加入 tlsCAFile=certifi.where()
client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

try:
    # ping 一下确认连接成功
    client.admin.command('ping')
    print("✅ Ping 成功！你已经成功连接到了 MongoDB 云端数据库！")

    # 选择一个数据库
    db = client["hci_experiment"]

    # 选择一个集合
    collection = db["test_collection"]

    # 准备一条假数据
    test_data = {
        "participant_id": "test_user_001",
        "condition": "XAI",
        "message": "Hello from local VS Code with certifi!"
    }

    # 插入数据
    result = collection.insert_one(test_data)
    print(f"✅ 成功写入一条测试数据！数据 ID: {result.inserted_id}")

except Exception as e:
    print(f"❌ 连接或写入失败，错误信息: {e}")