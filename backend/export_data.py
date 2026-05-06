import os
import json
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi

# 1. 连接数据库
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = client["hci_experiment"]

# 2. 你想要导出的三个集合
collections_to_export = ["participants_status", "experiment_events", "dialogue_turns"]

print("⏳ 正在从云端下载数据...")

for col_name in collections_to_export:
    collection = db[col_name]

    # 查找集合中的所有数据
    # {"_id": 0} 的意思是：告诉 MongoDB 不要把自动生成的 ObjectId 下载下来
    # 因为 ObjectId 是一串特殊代码，直接存 JSON 会报错，且对我们分析数据没有用
    data = list(collection.find({}, {"_id": 0}))

    # 将下载的数据保存为本地的 .json 文件
    output_filename = f"{col_name}_exported.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✅ 成功导出 {len(data)} 条记录 -> {output_filename}")

print("🎉 全部导出完成！")