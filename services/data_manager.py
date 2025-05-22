import json
import os

DATA_PATH = "./collect/cases.json"

# 初始資料
default_data = {
    "collecting_users": [],
    "new_case": {}
}

def load_data():
    if not os.path.exists(DATA_PATH):
        return default_data.copy()
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data: dict):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


