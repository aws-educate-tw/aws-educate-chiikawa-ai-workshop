import json
import os
import boto3
import time
from time import sleep
import logging

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    StickerMessageContent,
    FollowEvent
)
import urllib.request

from app import run

logger = logging.getLogger()
logger.setLevel(logging.INFO)

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))


# 使用單一通用處理器
@handler.add(MessageEvent)
def handle_message(event):
    user_id = event.source.user_id
    
    # 統一處理不同消息類型
    if isinstance(event.message, TextMessageContent):
        user_message = event.message.text
    elif isinstance(event.message, StickerMessageContent):
        sticker_id = event.message.sticker_id
        package_id = event.message.package_id
        user_message = f"[STICKER] package_id={package_id}, sticker_id={sticker_id}"
    else:
        user_message = "[不支持的消息類型]"
    
    profile_url = f'https://api.line.me/v2/bot/profile/{user_id}'
    headers = {
        'Authorization': f'Bearer {os.getenv("CHANNEL_ACCESS_TOKEN")}'
    }
    
    req = urllib.request.Request(profile_url, headers=headers)
    
    logger.info(f"發送請求獲取用戶資料: {profile_url}")
    with urllib.request.urlopen(req) as response:
        profile_json = json.loads(response.read().decode('utf-8'))
    
    logger.info(f"獲取到用戶資料: {profile_json}")
    user_name = profile_json.get('displayName', '朋友')
    
    logger.info(f"Received message from {user_id}: {user_message}")
    
    response = run(user_id, user_name, user_message)

    logger.info(f"Response: {response}")
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=response
            )
        )

def lambda_handler(event, context):
    try: 
        body = event['body']
        signature = event['headers']['x-line-signature']
        handler.handle(body, signature)
        return {
            'statusCode': 200,
            'body': json.dumps('Success!!!')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
