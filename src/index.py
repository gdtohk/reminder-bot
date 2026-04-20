from js import Response
from pyodide.http import pyfetch
import json
import datetime

# --- 【通用函數：發送訊息】 ---
async def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id, 
        "text": text,
        "parse_mode": "Markdown" # 讓訊息支援加粗等格式
    })
    await pyfetch(url, method="POST", headers={"Content-Type": "application/json"}, body=payload)

# --- 【技能 1：天氣預報 (Weather Skill)】 ---
async def get_hk_weather():
    """獲取香港天文台今日天氣概況"""
    url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=flw&lang=tc"
    try:
        res = await pyfetch(url)
        data = await res.json()
        forecast = data.get('generalSituation', '暫時無法獲取天氣概況')
        return f"🌤️ **老闆早晨！今日天氣匯報：**\n\n{forecast}"
    except Exception as e:
        return f"❌ 天氣獲取失敗：{str(e)}"

# --- 【技能 2：定時提醒檢查 (Reminder Skill)】 ---
async def check_reminders(env):
    db = env.DB
    # 獲取香港時間 (UTC+8)
    now_hk = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    current_time_str = now_hk.strftime("%Y-%m-%d %H:%M:00")
    
    query = "SELECT * FROM reminders WHERE is_sent = 0 AND remind_time <= ?"
    result = await db.prepare(query).bind(current_time_str).all()
    
    count = 0
    if result.results:
        for item in result.results:
            row = item.to_py() if hasattr(item, 'to_py') else item
            msg = f"⏰ **何生您好！**\n您下達的任務時間到啦：\n\n> {row['message']}"
            # 這裡發送給 env.TELEGRAM_CHAT_ID 確保你自己能收到
            await send_message(env.TELEGRAM_TOKEN, env.TELEGRAM_CHAT_ID, msg)
            await db.prepare("UPDATE reminders SET is_sent = 1 WHERE id = ?").bind(row['id']).run()
            count += 1
    return count

# --- 【主入口：網路請求接收 (Webhook/API)】 ---
async def on_fetch(request, env):
    url = request.url
    
    # 1. 綁定 Webhook
    if url.endswith("/setup"):
        webhook_url = url.replace("/setup", "/webhook")
        tg_url = f"https://api.telegram.org/bot{env.TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
        res = await pyfetch(tg_url)
        data_text = await res.text()
        return Response.new(f"綁定結果：{data_text}")

    # 2. 接收 Telegram 訊息 (Webhook)
    if url.endswith("/webhook") and request.method == "POST":
        body_text = await request.text()
        body = json.loads(body_text)
        
        if "message" in body and "text" in body["message"]:
            chat_id = body["message"]["chat"]["id"]
            text = body["message"]["text"]
            
            # 指令：新增提醒
            if text.startswith("/add "):
                parts = text.split(" ", 3)
                if len(parts) >= 4:
                    date, time_val, message = parts[1], parts[2], parts[3]
                    remind_time = f"{date} {time_val}:00"
                    await env.DB.prepare("INSERT INTO reminders (chat_id, message, remind_time) VALUES (?, ?, ?)").bind(
                        str(chat_id), message, remind_time
                    ).run()
                    await send_message(env.TELEGRAM_TOKEN, chat_id, f"✅ 收到！何生，已記錄入庫！\n會在 {date} {time_val} 提醒您。")
                else:
                    await send_message(env.TELEGRAM_TOKEN, chat_id, "❌ 格式：/add YYYY-MM-DD HH:MM 內容")
            
            # --- 新增：手動測試天氣技能 ---
            elif text == "/weather":
                weather_text = await get_hk_weather()
                await send_message(env.TELEGRAM_TOKEN, chat_id, weather_text)
            
            # 指令：幫助
            elif text == "/start" or text == "/help":
                help_msg = "老闆好！我是你的提醒助手🤖\n\n🔹 **/add** `日期` `時間` `內容` (新增提醒)\n🔹 **/weather** (立即查看香港天氣)"
                await send_message(env.TELEGRAM_TOKEN, chat_id, help_msg)
                
        return Response.new("OK")

    return Response.new("🤖 機器人運行中")

# --- 【主入口：定時觸發器 (Cron Trigger)】 ---
async def on_scheduled(event, env):
    # 任務 1：每分鐘檢查一次資料庫提醒
    if event.cron == "* * * * *":
        await check_reminders(env)
        
    # 任務 2：天氣報時 (請確保此處字串與 wrangler.toml 裡的 crons 列表完全一致)
    else:
        # 只要不是每分鐘任務，就當作是天氣任務執行 (這樣即使你改了時間也不怕對不上暗號)
        weather_text = await get_hk_weather()
        await send_message(env.TELEGRAM_TOKEN, env.TELEGRAM_CHAT_ID, weather_text)
