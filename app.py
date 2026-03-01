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
    print("TELEGRAM DATA:", data)

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.lower() == "hola":
            send_message(chat_id, "Hola 👋 Soy RespiraNL Bot. Escribe el nombre de tu ciudad.")
        else:
            send_air_quality(chat_id, text)

    return {"ok": True}
def send_air_quality(chat_id, city):
    url = f"https://api.waqi.info/feed/{city}/?token={WAQI_TOKEN}"
    response = requests.get(url).json()

    if response.get("status") == "ok":
        aqi = response["data"]["aqi"]
        message = f"🌎 Calidad del aire en {city}:\nAQI: {aqi}"
    else:
        message = "❌ No encontré datos para esa ciudad."

    send_message(chat_id, message)
