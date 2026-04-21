import datetime
from pyodide.http import pyfetch
from common import send_message

async def get_hk_weather_detailed():
    t = int(datetime.datetime.now().timestamp())
    url_curr = f"https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=tc&t={t}"
    url_fore = f"https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=tc&t={t}"
    
    try:
        res_c = await pyfetch(url_curr)
        data_c = await res_c.json()
        res_f = await pyfetch(url_fore)
        data_f = await res_f.json()
        
        curr_temp = data_c['temperature']['data'][0]['value']
        curr_hum = data_c['humidity']['data'][0]['value']
        warnings = data_c.get('warningMessage', [])
        warn_text = " ✅ 目前無生效警告" if not warnings else " ⚠️ " + "、".join(warnings)
        general_sit = data_f.get('generalSituation', '暫無概括')
        
        msg = f"🌤️ **老闆早晨！天氣全匯報**\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"🌡️ **當前氣溫**：{curr_temp}°C\n"
        msg += f"💧 **相對濕度**：{curr_hum}%\n"
        msg += f"📢 **天氣警告**：{warn_text}\n"
        msg += f"━━━━━━━━━━━━━━\n"
        msg += f"📖 **今日概況**：\n> {general_sit}\n\n"
        msg += f"📅 **未來 7 天預報**：\n"
        
        for day in data_f.get('weatherForecast', [])[:7]:
            d = day['forecastDate']
            msg += f"• **{d[4:6]}/{d[6:8]} ({day['week']})**：{day['forecastMintemp']['value']}-{day['forecastMaxtemp']['value']}°C | {day['forecastWeather']}\n"
            
        return msg
    except Exception as e:
        return f"❌ 天氣獲取失敗：{str(e)}"

async def run_weather_skill(env, chat_id):
    weather_text = await get_hk_weather_detailed()
    await send_message(env.TELEGRAM_TOKEN, chat_id, weather_text)
