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
        "parse_mode": "Markdown" 
    })
    await pyfetch(url, method="POST", headers={"Content-Type": "application/json"}, body=payload)

# --- 【升級版技能：詳細天氣預報】 ---
async def get_hk_weather_detailed():
    url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=tc"
    try:
        res = await pyfetch(url)
        data = await res.json()
        
        general_sit = data.get('generalSituation', '')
        msg = f"🌤️ **老闆早晨！天氣匯報**\n\n> {general_sit}\n\n"
        msg += "📅 **未來 7 天預報：**\n"
        msg += "---"
        
        forecasts = data.get('weatherForecast', [])
        for day in forecasts[:7]:
            d = day['forecastDate']
            date_label = f"{d[4:6]}月{d[6:8]}日"
            week = day['week']
            low = day['forecastMintemp']['value']
            high = day['forecastMaxtemp']['value']
            desc = day['forecastWeather']
            
            msg += f"\n📌 **{date_label} ({week})**\n🌡️ {low}°C ~ {high}°C\n☁️ {desc}\n"
            
        return msg
    except Exception as e:
        return f"❌ 天氣獲取失敗：{str(e)}"

# --- 【定時提醒檢查】 ---
async def check_reminders(env):
    db = env.DB
    now_hk = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    current_time_str = now_hk.strftime("%Y-%m-%d %H:%M:00")
    
    query = "SELECT * FROM reminders WHERE is_sent = 0 AND remind_time <= ?"
    result = await db.prepare(query).bind(current_time_str).all()
    
    count = 0
    if result.results:
        for item in result.results:
            row = item.to_py() if hasattr(item, 'to_py') else item
            msg = f"⏰ **何生您好！任務提醒：**\n\n> {row['message']}"
            await send_message(env.TELEGRAM_TOKEN, env.TELEGRAM_CHAT_ID, msg)
            await db.prepare("UPDATE reminders SET is_sent = 1 WHERE id = ?").bind(row['id']).run()
            count += 1
    return count

# --- 【主入口：網路請求】 ---
async def on_fetch(request, env):
    url = request.url
    if url.endswith("/setup"):
        webhook_url = url.replace("/setup", "/webhook")
        tg_url = f"https://api.telegram.org/bot{env.TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
        res = await pyfetch(tg_url)
        return Response.new(f"綁定結果：{await res.text()}")

    if url.endswith("/webhook") and request.method == "POST":
        body = json.loads(await request.text())
        if "message" in body and "text" in body["message"]:
            chat_id = body["message"]["chat"]["id"]
            text = body["message"]["text"]
            
            if text.startswith("/add "):
                parts = text.split(" ", 3)
                if len(parts) >= 4:
                    date, time_val, message = parts[1], parts[2], parts[3]
                    remind_time = f"{date} {time_val}:00"
                    await env.DB.prepare("INSERT INTO reminders (chat_id, message, remind_time) VALUES (?, ?, ?)").bind(
                        str(chat_id), message, remind_time
                    ).run()
                    await send_message(env.TELEGRAM_TOKEN, chat_id, f"✅ 已入庫！會在 {date} {time_val} 提醒。")
                else:
                    await send_message(env.TELEGRAM_TOKEN, chat_id, "❌ 格式：/add YYYY-MM-DD HH:MM 內容")
            
            elif text == "/weather":
                weather_text = await get_hk_weather_detailed()
                await send_message(env.TELEGRAM_TOKEN, chat_id, weather_text)
            
            elif text == "/start" or text == "/help":
                await send_message(env.TELEGRAM_TOKEN, chat_id, "🤖 提醒助手\n/add 日期 時間 內容\n/weather 查看7天預報")
                
        return Response.new("OK")
    return Response.new("Running...")

# --- 【主入口：定時觸發】 ---
async def on_scheduled(event, env):
    if event.cron == "* * * * *":
        await check_reminders(env)
    else:
        # 其他定時（如早晨 07:30）發送詳細預報
        weather_text = await get_hk_weather_detailed()
        await send_message(env.TELEGRAM_TOKEN, env.TELEGRAM_CHAT_ID, weather_text)
