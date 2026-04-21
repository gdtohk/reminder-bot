from js import Response
import json
from common import send_message
from skills.weather import run_weather_skill
from skills.reminder import check_reminders, add_reminder
from skills.rebar import run_rebar_skill
# 👉 新增：把大腦請進辦公室
from agent import chat_with_llm

# --- 【技能路由表】 ---
SKILLS_MAP = {
    "/weather": run_weather_skill,
    "/start": lambda env, chat_id: send_message(env.TELEGRAM_TOKEN, chat_id, "🤖 助理已升級！\n輸入指令可執行技能，直接打字可與 AI 聊天！"),
    "/help": lambda env, chat_id: send_message(env.TELEGRAM_TOKEN, chat_id, "使用說明：\n/weather - 天氣\n/rebar - 鋼筋計算\n直接對我說話，大腦會回答你！")
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

            # 1. 處理帶參數的特殊指令
            if text.startswith("/add "):
                await add_reminder(env, chat_id, text)
            elif text.startswith("/rebar "):
                await run_rebar_skill(env, chat_id, text)

            # 2. 處理路由表裡的普通指令
            elif text in SKILLS_MAP:
                await SKILLS_MAP[text](env, chat_id)
                
            # 3. 處理偵錯指令
            elif text == "/test_id":
                await send_message(env.TELEGRAM_TOKEN, chat_id, f"👤 ID: `{chat_id}`\n🔑 Config ID: `{env.TELEGRAM_CHAT_ID}`")
                
            # 🌟 4. 重頭戲：如果不是任何指令，就丟給 Gemini 大腦處理！
            else:
                await chat_with_llm(env, chat_id, text)

        return Response.new("OK")
    return Response.new("Running...")

async def on_scheduled(event, env):
    if event.cron == "* * * * *":
        await check_reminders(env)
    else:
        # 定時報天氣
        await run_weather_skill(env, env.TELEGRAM_CHAT_ID)
