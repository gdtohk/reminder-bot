import json
from pyodide.http import pyfetch
from common import send_message

async def chat_with_llm(env, chat_id, user_text):
    # --- 你的專屬 API 配置 ---
    api_url = "https://ai.hk01.eu.cc/v1/chat/completions"
    api_key = "sk-hk001"
    model = "gemini-2.5-flash"  # 你指定絕對可用的極速模型
    
    # --- 賦予 AI 靈魂（System Prompt） ---
    system_prompt = """
    你是何生（香港建築行業 QS 兼紮鐵拆圖工程師）的專屬智能助理。
    請用繁體中文（可適當夾雜地道廣東話）回答。
    你非常懂建築工程、鋼筋計算和香港的施工環境。
    回答請保持簡潔、專業、直接。
    """
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        # 發送請求給你的 hk01 伺服器
        res = await pyfetch(api_url, method="POST", headers=headers, body=json.dumps(payload))
        
        if res.status != 200:
            error_text = await res.text()
            await send_message(env.TELEGRAM_TOKEN, chat_id, f"❌ API 請求失敗 (狀態碼 {res.status}): {error_text}")
            return
            
        data = await res.json()
        
        # 提取 Gemini 的回答
        reply = data['choices'][0]['message']['content']
        
        # 發送回 Telegram
        await send_message(env.TELEGRAM_TOKEN, chat_id, reply)
        
    except Exception as e:
        await send_message(env.TELEGRAM_TOKEN, chat_id, f"❌ 大腦連線發生錯誤：{str(e)}")
