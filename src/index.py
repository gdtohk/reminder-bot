from js import Response
import json
from skills.rebar import run_rebar_skill
from common import send_message
from skills.weather import run_weather_skill
from skills.reminder import check_reminders, add_reminder

# --- 【技能路由表：這是以後快速增加 Skill 的核心】 ---
# 未來其他人想加 Skill，只需要把指令和函數寫在這裡
SKILLS_MAP = {
    "/weather": run_weather_skill,
    "/start": lambda env, chat_id: send_message(env.TELEGRAM_TOKEN, chat_id, "🤖 助理已就位！\n/weather - 天氣預報\n/add - 新增提醒"),
    "/help": lambda env, chat_id: send_message(env.TELEGRAM_TOKEN, chat_id, "使用說明：\n/weather 獲取 7 天天氣\n/add 日期 時間 內容")
}

async def on_fetch(request, env):
    url = request.url
    
    if url.endswith("/setup"):
        webhook_url = url.replace("/setup", "/webhook")
        tg_url = f"https://api.telegram.org/bot{env.TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
        from pyodide.http import pyfetch
        res = await pyfetch(tg_url)
        return Response.new(f"綁定結果：{await res.text()}")

    if url.endswith("/webhook") and request.method == "POST":
        body = json.loads(await request.text())
        if "message" in body and "text" in body["message"]:
            chat_id = body["message"]["chat"]["id"]
            text = body["message"]["text"]

            # 1. 處理帶參數的特殊指令（如 /add）
            if text.startswith("/add "):
                await add_reminder(env, chat_id, text)

# 👉 新增這一塊：把 /rebar 派發給鋼筋部門
            elif text.startswith("/rebar "):
                await run_rebar_skill(env, chat_id, text)            

            # 2. 處理路由表裡的普通指令
            elif text in SKILLS_MAP:
                await SKILLS_MAP[text](env, chat_id)
                
            # 3. 處理偵錯指令
            elif text == "/test_id":
                await send_message(env.TELEGRAM_TOKEN, chat_id, f"👤 ID: `{chat_id}`\n🔑 Config ID: `{env.TELEGRAM_CHAT_ID}`")

        return Response.new("OK")
    return Response.new("Running...")

async def on_scheduled(event, env):
    if event.cron == "* * * * *":
        await check_reminders(env)
    else:
        # 定時報天氣
        await run_weather_skill(env, env.TELEGRAM_CHAT_ID)
