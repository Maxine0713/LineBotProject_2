from fastapi import FastAPI, Request, Header, HTTPException
from dotenv import load_dotenv
from datetime import datetime
import os
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent
)
from linebot.v3.exceptions import InvalidSignatureError

from services.excel import save_to_excel
from services.state import user_data, collecting_status, user_dirs

# 載入 .env
load_dotenv()
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# 初始化 SDK
handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=access_token)

app = FastAPI()


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: str = Header(None)
):
    body = await request.body()
    try:
        handler.handle(body.decode(), x_line_signature)
    except InvalidSignatureError:
        print("[警告] LINE 簽章驗證失敗！")
        raise HTTPException(status_code=400, detail="Invalid signature")

    return {"message": "OK"}


# 處理文字訊息
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent):
    print('event',event)
    user_id = event.source.user_id
    user_text = event.message.text
    reply_token = event.reply_token

    if user_id not in user_data:
        user_data[user_id] = []
        collecting_status[user_id] = False

    if user_text == "開始填寫":
        collecting_status[user_id] = True
        reply = "請開始輸入資料。"

    elif user_text == "結束填寫":
        collecting_status[user_id] = False
        save_to_excel(user_id,access_token)
        user_data[user_id] = []
        reply = "資料已成功儲存，謝謝！"

    elif collecting_status[user_id]:
        user_data[user_id].append((datetime.now(), user_text))
        reply = "已收到文字，請繼續輸入或輸入 '結束填寫'"

    else:
        reply = "請先輸入『開始填寫』"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

# 處理圖片訊息（延遲下載）
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event: MessageEvent):
    user_id = event.source.user_id
    image_id = event.message.id
    reply_token = event.reply_token

    if user_id not in user_data or not collecting_status.get(user_id):
        reply = "請先輸入『開始填寫』"
    else:
        # 只紀錄 image_id，不立即下載
        user_data[user_id].append((datetime.now(), f"[image_id]{image_id}"))
        reply = "圖片已記錄，將於結束後儲存。"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply)]
            )
        )



