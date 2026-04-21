from js import Response
from pyodide.http import pyfetch
import json
import datetime

# --- 【1. 通用功能：發送 Telegram 訊息】 ---
async def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id, 
        "text": text,
        "parse_mode": "Markdown" 
    })
    await pyfetch(url, method="POST", headers={"Content-Type": "application/json"}, body=payload)

# --- 【2. 核心功能：獲取實時及 7 天天氣（加入緩存刷新）】 ---
async def get_hk_weather_detailed():
    """抓取香港天文台最新數據，並透過時間戳確保數據新鮮"""
    
    # 【新增】取得目前秒數，作為隨機參數防止 Cloudflare 緩存舊數據
    t = int(datetime.datetime.now().timestamp())
    
    # 接口 A：實時報告
    url_curr = f"https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=tc&t={t}"
    # 接口 B：九天預報
    url_fore = f"https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=tc&t={t}"
    
    try:
        # 同時抓取數據
        res_c = await pyfetch(url_curr)
        data_c = await res_c.json()
        res_f = await pyfetch(url_fore)
        data_f = await res_f.json()
        
        # --- 整理實時數據 ---
        curr_temp = data_c['temperature']['data'][0]['value']
        curr_hum = data_c['humidity']['data'][0]['value']
        
        # 天氣警告處理
        warnings = data_c.get('warningMessage', [])
        warn_text = " ✅ 目前無生效警告" if not warnings else " ⚠️ " + "、".join(warnings)
        
        # 今日綜合概括
        general_sit = data_f.get('generalSituation', '暫無概括')
        
        # --- 組裝訊息 ---
        msg = f"🌤️ **何生早晨！天氣全匯報 (v3.1)**\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"🌡️ **當前氣溫**：{curr_temp}°C\n"
        msg += f"💧 **相對濕度**：{curr_hum}%\n"
        msg += f"📢 **天氣警告**：{warn_text}\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"📖 **今日概況**：\n> {general_sit}\n\n"
        msg += f"📅 **未來 7 天預報**：\n"
        
        forecasts = data_f.get('weatherForecast', [])
        for day in forecasts[:7]:
            d = day['forecastDate']
            date_label = f"{d[4:6]}/{d[6:8]}"
            week = day['week']
            low = day['forecastMintemp']['value']
            high = day['forecastMaxtemp']['value']
            desc = day['forecastWeather']
            msg += f"• **{date_label} ({week})**：{low}-{high}°C | {desc}\n"
            
        return msg
    except Exception as e:
        return f"❌ 天氣獲取失敗：{str(e)}"

# --- 【3. 核心功能：檢查資料庫提醒】 ---
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

# --- 【4. 流量入口：處理指令與對話】 ---
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
                    await send_message(env.TELEGRAM_TOKEN, chat_id, f"✅ 已記錄！會在 {date} {time_val} 提醒您。")
                else:
                    await send_message(env.TELEGRAM_TOKEN, chat_id, "❌ 格式：/add YYYY-MM-DD HH:MM 內容")
            
            elif text == "/weather":
                weather_text = await get_hk_weather_detailed()
                await send_message(env.TELEGRAM_TOKEN, chat_id, weather_text)
            
            elif text == "/test_id":
                await send_message(env.TELEGRAM_TOKEN, chat_id, f"👤 當前對話 ID: `{chat_id}`\n🔑 後台配置 ID: `{env.TELEGRAM_CHAT_ID}`")
            
            elif text == "/start" or text == "/help":
                help_text = "🤖 **何生專屬助理 3.1**\n\n🔹 `/add` - 新增提醒\n🔹 `/weather` - 獲取最新天氣預報\n🔹 `/test_id` - ID 偵錯"
                await send_message(env.TELEGRAM_TOKEN, chat_id, help_text)
                
        return Response.new("OK")
    return Response.new("Running...")

# --- 【5. 定時入口：處理 Cron 定時觸發】 ---
async def on_scheduled(event, env):
    if event.cron == "* * * * *":
        await check_reminders(env)
    else:
        weather_text = await get_hk_weather_detailed()
        await send_message(env.TELEGRAM_TOKEN, env.TELEGRAM_CHAT_ID, weather_text)
