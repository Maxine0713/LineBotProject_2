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
    TemplateMessage,
    PostbackAction,
    ButtonsTemplate,
    QuickReply,
    QuickReplyItem,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    PostbackEvent
)
from linebot.v3.exceptions import InvalidSignatureError
from services.excel import save_to_excel
from services.state import add_case, collecting_users, remove_collecting_user, remove_case
from logger import log

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
        log("[警告] LINE 簽章驗證失敗！")
        raise HTTPException(status_code=400, detail="Invalid signature")

    return {"message": "OK"}


add_case_button_template = TemplateMessage(
    alt_text="開始新增範例",
    template=ButtonsTemplate(
        text="開始新增範例，結束請按結束填寫",
        actions=[
            PostbackAction(
                label="開始填寫",
                data="ADD_CASE",
                input_option="openKeyboard",
                fill_in_text="新增案例---\n服務人員: \n客戶: \n機號: \n出廠日期: \n產品: \n塑料: \n其他備註: \n---"
            ),
            PostbackAction(
                label="取消填寫",
                data="CANCEL_CASE"
            ),
            PostbackAction(
                label="結束填寫",
                data="CASE_SUBMIT"
            )
        ]
    )
)

reminder_message = TextMessage(
    text="正在蒐集資料中，若完成請按下「結束填寫」來提交資料，或按下「取消填寫」來取消填寫",
    quick_reply=QuickReply(items=[
        QuickReplyItem(action=PostbackAction(
            label="取消填寫",
            data="CANCEL_CASE"
        )),
        QuickReplyItem(action=PostbackAction(
            label="結束填寫",
            data="CASE_SUBMIT"
        )),
    ])
)
# 處理文字訊息


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent):
    user_id = event.source.user_id
    user_text = event.message.text
    reply_token = event.reply_token
    reply = []
    # 使用者開始填寫資料
    if user_text == "新增案例":
        # 建立 TemplateMessage 實例
        reply.append(add_case_button_template)
    elif "新增案例---" in user_text:
        if user_id in collecting_users:
            add_case(user_id=user_id, case_message=user_text)
        else:
            reply_message = TextMessage(text="請先按下「開始填寫」，再開始上傳資料。")
            reply.append(reply_message)
            reply.append(add_case_button_template)
    elif user_id in collecting_users:
        # 如果此使用者在正收集資料，則傳送的其他訊息將會被忽略，並提醒使用者要結束填寫
        reply.append(reminder_message)
    if reply:
        # 傳送訊息
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=reply
                )
            )

# 處理圖片訊息（延遲下載）


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event: MessageEvent):
    user_id = event.source.user_id
    image_id = event.message.id
    if user_id in collecting_users:
        # 只紀錄 image_id，不立即下載
        add_case(user_id=user_id, image_id=image_id)
        log(f"{image_id}已儲存，稍後下載")


# 處理 postbackAction
@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    reply_token = event.reply_token
    user_id = event.source.user_id
    reply = None
    if data == 'ADD_CASE':
        if user_id not in collecting_users:
            collecting_users.append(user_id)
    if data == "CASE_SUBMIT":
        # 處理提交的資料
        if user_id in collecting_users:
            # 先回復使用者，再儲存資料到 Excel
            with ApiClient(configuration) as api_client:
                MessagingApi(api_client).reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text="資料已儲存，謝謝！")]
                    )
                )
            save_to_excel(user_id, access_token)
        else:
            reply = "沒有可儲存的資料。"
    if data == "CANCEL_CASE":
        remove_collecting_user(user_id)
        remove_case(user_id)
        reply = "已取消填寫，謝謝!"


    if reply:
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=reply)]
                )
            )
