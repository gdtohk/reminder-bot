from js import Response
from pyodide.http import pyfetch
import json
import datetime

# 傳送訊息給你的專屬函數
async def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text})
    await pyfetch(url, method="POST", headers={"Content-Type": "application/json"}, body=payload)

# 檢查時間並發送提醒的專屬函數
async def check_reminders(env):
    db = env.DB
    # 獲取目前的香港時間 (UTC+8)
    now_hk = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    current_time_str = now_hk.strftime("%Y-%m-%d %H:%M:00")
    
    # 從資料庫找出「時間到了」且「還沒發送過」的任務
    query = "SELECT * FROM reminders WHERE is_sent = 0 AND remind_time <= ?"
    result = await db.prepare(query).bind(current_time_str).all()
    
    count = 0
    if result.results:
        for row in result.results:
            msg = f"⏰ **時間到啦！老闆請注意：**\n\n{row['message']}"
            await send_message(env.TELEGRAM_TOKEN, row['chat_id'], msg)
            # 標記為已發送
            await db.prepare("UPDATE reminders SET is_sent = 1 WHERE id = ?").bind(row['id']).run()
            count += 1
    return count

# 處理所有網路請求的大門
async def on_fetch(request, env):
    url = request.url
    
    # 1. 綁定耳朵 (Webhook)：告訴 Telegram 只要有人說話，就把訊息送到這裡
    if url.endswith("/setup"):
        webhook_url = url.replace("/setup", "/webhook")
        tg_url = f"https://api.telegram.org/bot{env.TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
        res = await pyfetch(tg_url)
        data = await res.json()
        return Response.new(f"綁定結果：{json.dumps(data)}")

    # 2. 手動時鐘：讓你隨時可以手動測試檢查任務
    if url.endswith("/check"):
        count = await check_reminders(env)
        return Response.new(f"檢查完畢！現在時間，共發送了 {count} 條提醒。")

    # 3. 接收指令：處理你在 Telegram 發送的訊息
    if url.endswith("/webhook") and request.method == "POST":
        body = await request.json()
        
        if "message" in body and "text" in body["message"]:
            chat_id = body["message"]["chat"]["id"]
            text = body["message"]["text"]
            
            # 解析你設定的提醒任務
            if text.startswith("/add "):
                parts = text.split(" ", 3)
                if len(parts) >= 4:
                    date = parts[1]
                    time = parts[2]
                    message = parts[3]
                    remind_time = f"{date} {time}:00"
                    
                    # 存入大腦 (D1 資料庫)
                    await env.DB.prepare("INSERT INTO reminders (chat_id, message, remind_time) VALUES (?, ?, ?)").bind(
                        str(chat_id), message, remind_time
                    ).run()
                    
                    await send_message(env.TELEGRAM_TOKEN, chat_id, f"✅ 任務已記錄入庫！\n我會在 {date} {time} 準時提醒你：\n「{message}」")
                else:
                    await send_message(env.TELEGRAM_TOKEN, chat_id, "❌ 格式錯誤！請使用格式：\n/add 2026-03-08 15:00 填寫你的任務內容")
            elif text == "/start" or text == "/help":
                help_msg = "老闆好！我是你的專屬提醒機器人🤖\n\n👉 **如何新增提醒？**\n請傳送以下格式的訊息：\n/add YYYY-MM-DD HH:MM 你的任務內容\n\n📝 **範例**：\n/add 2026-03-08 15:30 記得提交鋼筋圖紙\n\n(注意：時間請使用香港時間，24小時制)"
                await send_message(env.TELEGRAM_TOKEN, chat_id, help_msg)
                
        return Response.new("OK")

    return Response.new("🤖 機器人主程式正常運作中！")

# 給 Cloudflare 自動定時器 (Cron) 用的專屬通道
async def on_scheduled(event, env):
    await check_reminders(env)
