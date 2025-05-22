# 儲存目前記憶體內的使用者狀態與資料
from datetime import datetime
from services.data_manager import load_data, save_data
import os
user_data: dict[str, list] = {}
user_dirs: dict[str, str] = {}

data = load_data()
collecting_users = data.get('collecting_users', [])
new_case = data.get('new_case', {})

def parse_case_message_text(text: str) -> dict:
    # 去除 --- 和前後空白
    clean_text = text.replace('---', '').strip()

    data = {}
    for line in clean_text.split('\n'):
        if ':' in line:
            key, *rest = line.split(':')
            value = ':'.join(rest).strip()  # 保留冒號右側所有內容
            data[key.strip()] = value
    return data

def remove_collecting_user(user_id:str):
    """
    移除正在收集的使用者
    :param user_id: 使用者ID
    """
    if user_id in collecting_users:
        collecting_users.remove(user_id)
        save_data(data)

def remove_case(user_id:str):
    """
    移除案例
    :param user_id: 使用者ID
    """
    if user_id in new_case:
        del new_case[user_id]
        save_data(data)

def add_case(user_id: str, case_message: str = None, image_id: str = None):
    """
    新增案例
    :param user_id: 使用者ID
    :param case_message: 案例訊息
    :param image_id: 圖片ID
    """
    case_obj = {
        'case_message': {},
        'images': []
    }
    if user_id in new_case:
        if image_id:
            new_case[user_id]['images'].append(image_id)
        if case_message:
            new_case[user_id]['case_message'] = parse_case_message_text(case_message)
    else:
        if image_id:
            case_obj['images'].append(image_id)
        if case_message:
            case_obj['case_message'] = parse_case_message_text(case_message)
        new_case[user_id] = case_obj
    save_data(data)