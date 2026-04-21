import json
from pyodide.http import pyfetch
from common import send_message

# 👉 直接從註冊表匯入工具名單和引擎字典
from registry import GET_TOOLS_LIST, AGENT_TOOLS_REGISTRY

async def chat_with_llm(env, chat_id, user_text):
    api_url = "https://ai.hk01.eu.cc/v1/chat/completions"
    api_key = env.GEMINI_API_KEY 
    model = "gemini-2.5-flash"  
    
    system_prompt = """
    你是何生（香港建築行業 QS 兼紮鐵拆圖工程師）的專屬智能助理。
    請用繁體中文（可適當夾雜地道廣東話）回答。
    你擁有實時獲取數據的工具。如果用戶的問題需要外部數據，請務必調用對應的工具，然後用自然、友好的語氣向老闆匯報結果。
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]
    
    payload = {
        "model": model,
        "messages": messages,
        "tools": GET_TOOLS_LIST,  # 🤖 直接塞入自動生成的名單
        "tool_choice": "auto"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        res = await pyfetch(api_url, method="POST", headers=headers, body=json.dumps(payload))
        if res.status != 200:
            await send_message(env.TELEGRAM_TOKEN, chat_id, f"❌ API 錯誤: {await res.text()}")
            return
            
        data = await res.json()
        response_message = data['choices'][0]['message']
        
        # --- 萬能引擎核心 ---
        if response_message.get('tool_calls'):
            messages.append(response_message)
            
            for tool_call in response_message['tool_calls']:
                function_name = tool_call['function']['name']
                # 解析大腦傳過來的參數 (例如 {"d": 32, "length": 12})
                arguments = json.loads(tool_call['function']['arguments'])
                
                # 🌟 奇蹟發生的地方：完全不需要 if/else！
                # 系統直接去註冊表裡找對應的函數，並把參數丟進去執行
                if function_name in AGENT_TOOLS_REGISTRY:
                    target_function = AGENT_TOOLS_REGISTRY[function_name]["func"]
                    
                    # 動態執行函數！
                    function_result = await target_function(**arguments)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "name": function_name,
                        "content": str(function_result) # 把結果轉成文字給大腦
                    })
                else:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "name": function_name,
                        "content": "❌ 系統找不到此工具"
                    })
            
            # 把執行結果交還給大腦做最終總結
            payload["messages"] = messages
            payload.pop("tools", None)
            
            res2 = await pyfetch(api_url, method="POST", headers=headers, body=json.dumps(payload))
            data2 = await res2.json()
            final_reply = data2['choices'][0]['message']['content']
            await send_message(env.TELEGRAM_TOKEN, chat_id, final_reply)
            
        else:
            reply = response_message.get('content')
            if reply:
                await send_message(env.TELEGRAM_TOKEN, chat_id, reply)
                
    except Exception as e:
        await send_message(env.TELEGRAM_TOKEN, chat_id, f"❌ 大腦連線發生錯誤：{str(e)}")
