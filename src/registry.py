import json
from skills.weather import get_hk_weather_detailed

# 💡 未來如果有鋼筋計算工具，就在這裡匯入，例如：
# from skills.rebar import calc_rebar_weight 

# --- 【智能工具註冊表】 ---
# 未來增加新 Skill，只需要在這裡加一個 Block，其他檔案完全不用改！
AGENT_TOOLS_REGISTRY = {
    
    # 工具 1：天氣播報員
    "get_hk_weather": {
        "func": get_hk_weather_detailed, # 對應的執行函數
        "schema": {
            "type": "function",
            "function": {
                "name": "get_hk_weather",
                "description": "獲取香港最新的實時天氣、天氣警告以及未來七天的預報。當詢問天氣時必須調用。",
                "parameters": {"type": "object", "properties": {}, "required": []}
            }
        }
    },
    
    # 工具 2：(示範) 未來的鋼筋計算機
    # "calc_rebar": {
    #     "func": calc_rebar_weight,
    #     "schema": { ... 定義參數如直徑、長度 ... }
    # }
}

# 🚀 自動生成給 Gemini 看的清單 (提取所有的 schema)
GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]
