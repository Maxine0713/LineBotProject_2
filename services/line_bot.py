import httpx
from logger import log




def download_image_via_http(image_id: str, access_token: str, image_path: str):
    url = f"https://api-data.line.me/v2/bot/message/{image_id}/content"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        # 發送 GET 請求，串流模式下載
        with httpx.stream("GET", url, headers=headers) as response:
            response.raise_for_status()  # 如果有錯誤的狀態碼，會拋出例外

            # 以二進位寫入模式開啟檔案
            with open(image_path, "wb") as image_file:
                # 將下載內容一塊塊寫入檔案
                for data_chunk in response.iter_bytes():
                    image_file.write(data_chunk)

        return True  # 下載成功
    except Exception as e:
        log(f"[錯誤] 下載失敗: {e}")
        return False


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
        log(f"[錯誤] 無法取得使用者名稱: {e}")
        return "未知使用者"