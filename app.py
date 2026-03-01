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
        send_message(chat_id, "Recibí tu mensaje 👀")

    return {"ok": True}
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

def send_air_quality(chat_id, city):
    url = f"https://api.waqi.info/feed/{city}/?token={WAQI_TOKEN}"
    response = requests.get(url).json()

    if response.get("status") == "ok":
        aqi = response["data"]["aqi"]
        message = f"🌎 Calidad del aire en {city}:\nAQI: {aqi}"
    else:
        message = "❌ No encontré datos para esa ciudad."

    send_message(chat_id, message)
