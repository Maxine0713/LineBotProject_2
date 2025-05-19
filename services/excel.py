
import httpx
# 儲存資料與下載圖片
import os
from openpyxl import Workbook, load_workbook
from datetime import datetime

# 新增儲存圖片的資料夾基底
BASE_DIR = "./collect/image"
os.makedirs(BASE_DIR, exist_ok=True)



# 指定 Excel 檔案
EXCEL_PATH = "./collect/collected_data.xlsx"
# 初始化 Excel
if not os.path.exists(EXCEL_PATH):
    wb = Workbook()
    ws = wb.active
    ws.append(["User ID", "Timestamp", "Content"])  # 欄位名稱
    wb.save(EXCEL_PATH)

from services.state import user_data



def save_to_excel(user_id: str,access_token):
    wb = load_workbook(EXCEL_PATH)
    ws = wb.active

    folder_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(BASE_DIR, user_id, folder_timestamp)
    os.makedirs(folder, exist_ok=True)

    for ts, content in user_data[user_id]:
        if content.startswith("[image_id]"):
            image_id = content.replace("[image_id]", "").strip()
            image_path = os.path.join(folder, f"{image_id}.jpg")

            if download_image_via_http(image_id, access_token, image_path):
                final_content = f"[圖片] {image_path}"
            else:
                final_content = f"[圖片下載失敗: {image_id}]"

        else:
            final_content = content

        ws.append([
            user_id,
            ts.strftime("%Y-%m-%d %H:%M:%S"),
            final_content
        ])

    wb.save(EXCEL_PATH)

def get_user_profile(user_id: str, access_token: str):
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        profile = response.json()
        return profile["displayName"]
    except Exception as e:
        print(f"[錯誤] 無法取得使用者名稱: {e}")
        return "未知使用者"

def download_image_via_http(image_id: str, access_token: str, image_path: str):
    url = f"https://api-data.line.me/v2/bot/message/{image_id}/content"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        with httpx.stream("GET", url, headers=headers) as r:
            r.raise_for_status()
            with open(image_path, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"[錯誤] 下載失敗: {e}")
        return False