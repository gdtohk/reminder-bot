import datetime
from common import send_message

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

async def add_reminder(env, chat_id, text):
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
