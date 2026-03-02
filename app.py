import os
import requests
from fastapi import FastAPI, Request
from datetime import datetime

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WAQI_TOKEN = os.getenv("WAQI_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN no está definido.")

if not WAQI_TOKEN:
    raise ValueError("WAQI_TOKEN no está definido.")

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": texto
    }

    response = requests.post(url, json=payload)
    print("Telegram:", response.status_code, response.text)

def consultar_waqi(ciudad):
    url = f"https://api.waqi.info/feed/{ciudad}/?token={WAQI_TOKEN}"
    response = requests.get(url)
    data = response.json()

    print("WAQI RESPONSE:", data)

    if data.get("status") != "ok":
        return None

    aqi = data["data"].get("aqi")
    contaminante = data["data"].get("dominentpol", "No disponible")

    return aqi, contaminante

@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()
    print("BODY:", body)

    message = body.get("message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    texto = message.get("text", "").strip()

    if not texto:
        return {"ok": True}

    texto_lower = texto.lower()

    if texto_lower in ["/start", "hola"]:
        enviar_mensaje(
            chat_id,
            "🌬️ Bienvenido a RespiraNL.\n\nEscribe un municipio de Nuevo León."
        )
        return {"ok": True}

    resultado = consultar_waqi(texto)

    if not resultado:
        enviar_mensaje(
            chat_id,
            "⚠️ No se encontró estación activa para ese municipio."
        )
        return {"ok": True}

    aqi, contaminante = resultado

    mensaje = f"""
🌬️ RESPIRA NL

📍 Municipio: {texto.title()}
📊 AQI: {aqi}
🧪 Contaminante dominante: {contaminante}
🕒 {datetime.now().strftime("%I:%M %p")}
"""

    enviar_mensaje(chat_id, mensaje.strip())

    return {"ok": True}
