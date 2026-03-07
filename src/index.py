from js import Response
from pyodide.http import pyfetch
import json

async def on_fetch(request, env):
    # 從 Cloudflare 環境變數中讀取
    TOKEN = env.TELEGRAM_TOKEN
    CHAT_ID = env.TELEGRAM_CHAT_ID
    
    message_text = "老闆你好！我是你的專屬提醒機器人，透過 GitHub Actions 全自動部署成功啦！🚀"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": message_text
    })
    
    await pyfetch(
        url,
        method="POST",
        headers={"Content-Type": "application/json"},
        body=payload
    )
    
    return Response.new("程式執行完畢！變數讀取成功並已發送訊息。")