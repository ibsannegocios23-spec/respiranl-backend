import os
import requests
from fastapi import FastAPI, Request
from datetime import datetime
from zoneinfo import ZoneInfo

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WAQI_TOKEN = os.getenv("WAQI_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN no está definido en Render.")

if not WAQI_TOKEN:
    raise ValueError("WAQI_TOKEN no está definido en Render.")

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": texto
    }

    response = requests.post(url, json=payload)

    print("Telegram status:", response.status_code)
    print("Telegram response:", response.text)

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

def clasificar_aqi(aqi):

    if aqi <= 50:
        return (
            "🟢 Bueno",
            "Sin riesgo para la población general.",
            "Actividades al aire libre seguras."
        )

    elif aqi <= 100:
        return (
            "🟡 Moderado",
            "Personas sensibles pueden presentar molestias leves.",
            "Si tienes asma o alergias, limita ejercicio intenso."
        )

    elif aqi <= 150:
        return (
            "🟠 No saludable para sensibles",
            "Niños, adultos mayores y personas con enfermedades respiratorias deben limitar exposición.",
            "Evita ejercicio al aire libre."
        )

    elif aqi <= 200:
        return (
            "🔴 No saludable",
            "Toda la población puede comenzar a experimentar efectos adversos.",
            "Reduce actividades prolongadas en exteriores."
        )

    elif aqi <= 300:
        return (
            "🟣 Muy no saludable",
            "Alto riesgo respiratorio para toda la población.",
            "Evita salir si no es necesario."
        )

    else:
        return (
            "⚫ Peligroso",
            "Emergencia sanitaria.",
            "Permanece en interiores y usa protección respiratoria."
        )

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
            "🌬️ Bienvenido a RespiraNL.\n\nEscribe un municipio de Nuevo León para conocer su calidad del aire."
        )
        return {"ok": True}

    resultado = consultar_waqi(texto)

    if not resultado:
        enviar_mensaje(
            chat_id,
            "⚠️ No se encontró estación activa para ese municipio.\nVerifica el nombre e intenta nuevamente."
        )
        return {"ok": True}

    aqi, contaminante = resultado

    if aqi is None:
        enviar_mensaje(
            chat_id,
            "⚠️ No se pudo obtener el AQI en este momento."
        )
        return {"ok": True}

    categoria, riesgo, recomendacion = clasificar_aqi(aqi)

    hora_local = datetime.now(
        ZoneInfo("America/Monterrey")
    ).strftime("%H:%M")

    mensaje = f"""
🌬️ RESPIRA NL | Calidad del Aire

📍 Municipio: {texto.title()}

📊 AQI: {aqi}
{categoria}

🧪 Contaminante dominante: {contaminante}

🫁 Riesgo:
{riesgo}

🔎 Recomendación:
{recomendacion}

🕒 {hora_local}
"""

    enviar_mensaje(chat_id, mensaje.strip())

    return {"ok": True}
