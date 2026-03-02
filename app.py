import os
import requests
from fastapi import FastAPI, Request
from datetime import datetime

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WAQI_TOKEN = os.getenv("WAQI_TOKEN")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

ALIAS_MUNICIPIOS = {
    "santa": "Santa Catarina",
    "sanico": "San Nicolás",
    "sn": "San Nicolás",
    "escobedo": "General Escobedo",
    "guadalupe": "Guadalupe",
    "apodaca": "Apodaca",
    "monterrey": "Monterrey",
    "garcia": "García",
    "juarez": "Juárez"
}

def clasificar_aqi(aqi: int):
    if aqi <= 50:
        return "Bueno", "Sin riesgo para la población general.", \
               "Puedes realizar actividades al aire libre con normalidad."
    elif aqi <= 100:
        return "Moderado", "Personas sensibles podrían presentar molestias leves.", \
               "Si tienes asma o alergias, modera actividad intensa."
    elif aqi <= 150:
        return "No saludable para sensibles", "Niños, adultos mayores y personas con asma deben limitar actividad exterior.", \
               "Evita ejercicio al aire libre."
    elif aqi <= 200:
        return "No saludable", "Riesgo para toda la población.", \
               "Reduce exposición prolongada al exterior."
    elif aqi <= 300:
        return "Muy no saludable", "Alto riesgo respiratorio.", \
               "Evita salir si no es necesario."
    else:
        return "Peligroso", "Emergencia sanitaria.", \
               "Permanece en interiores y usa protección respiratoria."

def build_response(municipio, aqi, categoria, riesgo, recomendacion):
    hora = datetime.now().strftime("%I:%M %p")

    mensaje = f"""
🌬️ *RESPIRA NL | Calidad del Aire*

📍 *Municipio:* {municipio}
📊 *AQI actual:* {aqi} ({categoria})

🫁 *Riesgo:* {riesgo}

🔎 *Recomendación:*
{recomendacion}

🕒 Actualizado: {hora}
Fuente: WAQI
"""
    return mensaje

def consultar_waqi(ciudad: str):
    url = f"https://api.waqi.info/feed/{ciudad}/?token={WAQI_TOKEN}"
    response = requests.get(url)
    data = response.json()

    if data["status"] != "ok":
        return None

    aqi = data["data"]["aqi"]
    return aqi

def enviar_mensaje(chat_id, texto):
    payload = {
        "chat_id": chat_id,
        "text": texto,
        
    }
    requests.post(TELEGRAM_API_URL, json=payload)

@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()

    if "message" not in body:
        return {"ok": True}

    message = body["message"]
    chat_id = message["chat"]["id"]
    texto_usuario = message.get("text", "").lower().strip()

    if texto_usuario in ["/start", "hola"]:
        enviar_mensaje(chat_id,
                       "🌬️ Bienvenido a *RespiraNL*.\n\nEscribe el nombre de un municipio de Nuevo León para conocer su calidad del aire.")
        return {"ok": True}

    municipio = ALIAS_MUNICIPIOS.get(texto_usuario, texto_usuario.title())

    aqi = consultar_waqi(municipio)

    if not aqi:
        enviar_mensaje(chat_id,
                       "⚠️ No se encontró estación activa para ese municipio.\nIntenta con otro nombre.")
        return {"ok": True}

    categoria, riesgo, recomendacion = clasificar_aqi(aqi)
    mensaje_final = build_response(municipio, aqi, categoria, riesgo, recomendacion)

    enviar_mensaje(chat_id, mensaje_final)

    return {"ok": True}
