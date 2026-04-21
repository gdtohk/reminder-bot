from common import send_message

async def run_rebar_skill(env, chat_id, text):
    # text 會收到類似 "/rebar 20 12 50" 的字串
    parts = text.split()
    
    # 檢查輸入格式是否正確
    if len(parts) < 3:
        help_msg = "❌ **格式錯誤！**\n請輸入：`/rebar [直徑mm] [長度m] [數量(選填)]`\n例子：`/rebar 20 12 50`"
        await send_message(env.TELEGRAM_TOKEN, chat_id, help_msg)
        return

    try:
        d = float(parts[1])       # 直徑
        length = float(parts[2])  # 長度
        # 如果沒有輸入數量，預設為 1 支
        qty = float(parts[3]) if len(parts) > 3 else 1.0

        # 業界標準鋼筋重量公式：(D^2 / 162) * L * Q
        unit_weight = (d ** 2) / 162
        total_weight = unit_weight * length * qty

        # 排版輸出結果
        msg = f"🏗️ **鋼筋重量計算結果**\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"🔹 **直徑**：{d} mm\n"
        msg += f"🔹 **長度**：{length} m\n"
        msg += f"🔹 **數量**：{qty} 支\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"⚖️ **單支重量**：{unit_weight * length:.2f} kg\n"
        msg += f"📦 **總重量**：**{total_weight:.2f} kg** ({total_weight/1000:.3f} 噸)"

        await send_message(env.TELEGRAM_TOKEN, chat_id, msg)
    except Exception as e:
        await send_message(env.TELEGRAM_TOKEN, chat_id, "❌ 計算出錯，請確保輸入的是數字。")
