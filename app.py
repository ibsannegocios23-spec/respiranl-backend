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

    response = requests.post(url, json=payload)

    print("SEND MESSAGE STATUS:", response.status_code)
    print("SEND MESSAGE RESPONSE:", response.text)
