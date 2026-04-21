import json
from pyodide.http import pyfetch

async def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id, 
        "text": text,
        "parse_mode": "Markdown" 
    })
    await pyfetch(url, method="POST", headers={"Content-Type": "application/json"}, body=payload)
