from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WAQI_TOKEN = os.getenv("WAQI_TOKEN")

@app.get("/")
def home():
    return {"status": "Bot running"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.lower() == "hola":
            send_message(chat_id, "Hola 👋 Soy RespiraNL Bot.\nEscribe una ciudad para consultar su calidad del aire.")
        else:
            get_air_quality(chat_id, text)

    return {"ok": True}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

def get_air_quality(chat_id, city):
    url = f"https://api.waqi.info/feed/{city}/?token={WAQI_TOKEN}"
    response = requests.get(url).json()

    if response.get("status") == "ok":
        data = response["data"]
        aqi = data.get("aqi")
        city_name = data["city"]["name"]

        message = f"🌎 Calidad del aire en {city_name}\nAQI: {aqi}\n"

        if aqi <= 50:
            message += "🟢 Buena\n\n✅ Ideal para actividades al aire libre."
        elif aqi <= 100:
            message += "🟡 Moderada\n\n⚠️ Personas sensibles deben limitar exposición prolongada."
        elif aqi <= 150:
            message += "🟠 Dañina para grupos sensibles\n\n😷 Niños, adultos mayores y personas con asma deben evitar actividad intensa."
        elif aqi <= 200:
            message += "🔴 Dañina\n\n🚨 Evita actividades al aire libre."
        else:
            message += "🟣 Muy dañina\n\n☠️ Permanece en interiores y usa protección."

    else:
        message = "❌ No encontré datos para esa ciudad."

    send_message(chat_id, message)
