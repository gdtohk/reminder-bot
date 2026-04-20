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

# --- 【2. 核心功能：獲取全能天氣報告 (實時 + 預報)】 ---
async def get_hk_weather_detailed():
    """抓取香港天文台實時氣溫、現行警告及未來 7 天預報"""
    # 接口 A：實時報告 (溫度、濕度、警告)
    url_curr = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=tc"
    # 接口 B：九天預報 (今日概括、未來一週預測)
    url_fore = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=tc"
    
    try:
        # 非同步同時抓取
        res_c = await pyfetch(url_curr)
        data_c = await res_c.json()
        
        res_f = await pyfetch(url_fore)
        data_f = await res_f.json()
        
        # --- 整理實時數據 ---
        # 氣溫通常取第一個測站數據
        curr_temp = data_c['temperature']['data'][0]['value']
        curr_hum = data_c['humidity']['data'][0]['value']
        
        # 現行天氣警告處理
        warnings = data_c.get('warningMessage', [])
        warn_text = " ✅ 目前無生效警告" if not warnings else " ⚠️ " + "、".join(warnings)
        
        # 今日綜合概括
        general_sit = data_f.get('generalSituation', '暫無概括')
        
        # --- 開始組裝 Markdown 訊息 ---
        msg = f"🌤️ **老闆早晨！天氣全匯報**\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"🌡️ **當前氣溫**：{curr_temp}°C\n"
        msg += f"💧 **相對濕度**：{curr_hum}%\n"
        msg += f"📢 **天氣警告**：{warn_text}\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"📖 **今日概況**：\n> {general_sit}\n\n"
        msg += f"📅 **未來 7 天預報**：\n"
        
        # 循環處理未來 7 天數據
        forecasts = data_f.get('weatherForecast', [])
        for day in forecasts[:7]:
            d = day['forecastDate'] # 格式如 20260421
            date_label = f"{d[4:6]}/{d[6:8]}" # 轉為 04/21
            week = day['week']
            low = day['forecastMintemp']['value']
            high = day['forecastMaxtemp']['value']
            desc = day['forecastWeather']
            msg += f"• **{date_label} ({week})**：{low}-{high}°C | {desc}\n"
            
        return msg
    except Exception as e:
        return f"❌ 天氣獲取失敗，錯誤訊息：{str(e)}"

# --- 【3. 核心功能：檢查資料庫提醒任務】 ---
async def check_reminders(env):
    db = env.DB
    # 換算香港時間 (UTC+8)
    now_hk = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    current_time_str = now_hk.strftime("%Y-%m-%d %H:%M:00")
    
    query = "SELECT * FROM reminders WHERE is_sent = 0 AND remind_time <= ?"
    result = await db.prepare(query).bind(current_time_str).all()
    
    count = 0
    if result.results:
        for item in result.results:
            row = item.to_py() if hasattr(item, 'to_py') else item
            msg = f"⏰ **何生您好！任務提醒：**\n\n> {row['message']}"
            # 推送給你在環境變數設定的個人 Chat ID
            await send_message(env.TELEGRAM_TOKEN, env.TELEGRAM_CHAT_ID, msg)
            # 標記已發送，避免重複
            await db.prepare("UPDATE reminders SET is_sent = 1 WHERE id = ?").bind(row['id']).run()
            count += 1
    return count

# --- 【4. 流量入口：處理用戶發來的訊息 (Webhook)】 ---
async def on_fetch(request, env):
    url = request.url
    
    # 指令 A：初始化 Webhook 綁定 (只需訪問一次)
    if url.endswith("/setup"):
        webhook_url = url.replace("/setup", "/webhook")
        tg_url = f"https://api.telegram.org/bot{env.TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
        res = await pyfetch(tg_url)
        return Response.new(f"綁定結果：{await res.text()}")

    # 指令 B：接收 Telegram 伺服器傳來的對話
    if url.endswith("/webhook") and request.method == "POST":
        body = json.loads(await request.text())
        if "message" in body and "text" in body["message"]:
            chat_id = body["message"]["chat"]["id"]
            text = body["message"]["text"]
            
            # 功能 1：新增提醒
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
                    await send_message(env.TELEGRAM_TOKEN, chat_id, "❌ 格式錯誤！範例：\n/add 2026-03-08 15:30 內容")
            
            # 功能 2：手動查詢詳細天氣
            elif text == "/weather":
                weather_text = await get_hk_weather_detailed()
                await send_message(env.TELEGRAM_TOKEN, chat_id, weather_text)
            
            # 功能 3：幫助選單
            elif text == "/start" or text == "/help":
                help_text = "🤖 **何生專屬提醒助理 3.0**\n\n🔹 `/add YYYY-MM-DD HH:MM 內容` - 新增提醒\n🔹 `/weather` - 查看香港實時天氣及 7 天預報"
                await send_message(env.TELEGRAM_TOKEN, chat_id, help_text)
                
        return Response.new("OK")

    return Response.new("🤖 機器人運行中...")

# --- 【5. 定時入口：處理 Cron 定時觸發 (Scheduled)】 ---
async def on_scheduled(event, env):
    # 判斷是「每分鐘提醒檢查」還是「早晨報時」
    if event.cron == "* * * * *":
        await check_reminders(env)
    else:
        # 只要不是每分鐘任務，就視為早晨報時任務
        weather_text = await get_hk_weather_detailed()
        await send_message(env.TELEGRAM_TOKEN, env.TELEGRAM_CHAT_ID, weather_text)
