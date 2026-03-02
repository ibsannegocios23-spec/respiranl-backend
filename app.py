import os
import requests
from fastapi import FastAPI, Request
from datetime import datetime
from zoneinfo import ZoneInfo

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WAQI_TOKEN = os.getenv("WAQI_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN no está definido.")

if not WAQI_TOKEN:
    raise ValueError("WAQI_TOKEN no está definido.")

ULTIMOS_AQI = {}

ALIAS_MUNICIPIOS = {
    "santa": "Santa Catarina",
    "sanico": "San Nicolás",
    "sn": "San Nicolás",
    "escobedo": "General Escobedo",
    "guada": "Guadalupe",
    "apod": "Apodaca",
    "mty": "Monterrey",
    "garcia": "García",
    "juarez": "Juárez"
}

def enviar_mensaje(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto
    }
    requests.post(url, json=payload)

def normalizar_contaminante(pol):

    mapa = {
        "pm25": "PM2.5 (Partículas finas)",
        "pm10": "PM10 (Partículas inhalables)",
        "o3": "Ozono (O₃)",
        "no2": "Dióxido de nitrógeno (NO₂)",
        "so2": "Dióxido de azufre (SO₂)",
        "co": "Monóxido de carbono (CO)"
    }

    return mapa.get(pol.lower(), pol.upper())

def clasificar_aqi(aqi):

    if aqi <= 50:
        return "🟢 Bueno", "Sin riesgo para la población general.", "Actividades al aire libre seguras."

    elif aqi <= 100:
        return "🟡 Moderado", "Personas sensibles pueden presentar molestias leves.", "Si tienes asma o alergias, limita ejercicio intenso."

    elif aqi <= 150:
        return "🟠 No saludable para sensibles", "Niños, adultos mayores y personas con enfermedades respiratorias deben limitar exposición.", "Evita ejercicio al aire libre."

    elif aqi <= 200:
        return "🔴 No saludable", "Toda la población puede comenzar a experimentar efectos adversos.", "Reduce actividades prolongadas en exteriores."

    elif aqi <= 300:
        return "🟣 Muy no saludable", "Alto riesgo respiratorio para toda la población.", "Evita salir si no es necesario."

    else:
        return "⚫ Peligroso", "Emergencia sanitaria.", "Permanece en interiores y usa protección respiratoria."

def consultar_waqi(ciudad):
    url = f"https://api.waqi.info/feed/{ciudad}/?token={WAQI_TOKEN}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") != "ok":
        return None

    aqi = data["data"].get("aqi")
    contaminante = data["data"].get("dominentpol", "No disponible")

    return aqi, contaminante

@app.post("/webhook")
async def webhook(req: Request):

    body = await req.json()
    message = body.get("message")

    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    texto = message.get("text", "").strip()

    if not texto:
        return {"ok": True}

    texto_lower = texto.lower()

    if texto_lower in ["/start", "hola"]:

        bienvenida = """
🌬️ Bienvenido a RespiraNL.

Este proyecto nace del interés genuino por el cuidado de la salud respiratoria en Nuevo León.

La información aquí presentada busca ayudarte a tomar decisiones más informadas para tu bienestar y el de tu familia.

Escribe un municipio de Nuevo León para consultar su calidad del aire actual.
"""
        enviar_mensaje(chat_id, bienvenida.strip())
        return {"ok": True}

    municipio = ALIAS_MUNICIPIOS.get(texto_lower, texto.title())

    resultado = consultar_waqi(municipio)

    if not resultado:
        enviar_mensaje(
            chat_id,
            "⚠️ No se encontró estación activa para ese municipio.\nVerifica el nombre e intenta nuevamente."
        )
        return {"ok": True}

    aqi, contaminante = resultado

    if aqi is None:
        enviar_mensaje(chat_id, "⚠️ No se pudo obtener el AQI en este momento.")
        return {"ok": True}

    contaminante = normalizar_contaminante(contaminante)

    categoria, riesgo, recomendacion = clasificar_aqi(aqi)

    tendencia = "—"

    if municipio in ULTIMOS_AQI:
        if aqi > ULTIMOS_AQI[municipio]:
            tendencia = "⬆️ Subiendo"
        elif aqi < ULTIMOS_AQI[municipio]:
            tendencia = "⬇️ Bajando"
        else:
            tendencia = "➡️ Estable"

    ULTIMOS_AQI[municipio] = aqi

    hora_local = datetime.now(
        ZoneInfo("America/Monterrey")
    ).strftime("%H:%M")

    tabla_niveles = """
📘 Guía rápida AQI:
🟢 0–50 Bueno
🟡 51–100 Moderado
🟠 101–150 Sensibles
🔴 151–200 No saludable
🟣 201+ Muy alto riesgo
"""

    mensaje = f"""
🌬️ RESPIRA NL | Monitoreo de Calidad del Aire

📍 Municipio: {municipio}

📊 AQI: {aqi}
{categoria}
📈 Tendencia: {tendencia}

🧪 Contaminante dominante:
{contaminante}

🫁 Riesgo:
{riesgo}

🔎 Recomendación:
{recomendacion}

🕒 {hora_local}

{tabla_niveles}

Este reporte tiene fines informativos.
Ante contingencias ambientales, sigue indicaciones de autoridades oficiales.
"""

    enviar_mensaje(chat_id, mensaje.strip())

    return {"ok": True}
