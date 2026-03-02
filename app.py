import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN no está definido en Render.")

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": texto
    }

    response = requests.post(url, json=payload)

    print("Telegram status:", response.status_code)
    print("Telegram body:", response.text)


@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()
    print("BODY RECIBIDO:", body)

    try:
        message = body.get("message")
        if not message:
            return {"ok": True}

        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        enviar_mensaje(chat_id, f"Recibí: {text}")

    except Exception as e:
        print("ERROR:", e)

    return {"ok": True}
