from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WAQI_TOKEN = os.getenv("WAQI_TOKEN")

CITY_ALIASES = {
    "san nicolas": "monterrey",
    "san nicolas de los garza": "monterrey",
    "guadalupe": "monterrey",
    "guadalupe nuevo leon": "monterrey",
    "juarez": "monterrey",
    "juarez nuevo leon": "monterrey",
    "escobedo": "monterrey",
    "santa catarina": "santa catarina",
    "san pedro": "san pedro",
    "monterrey": "monterrey"
}


@app.get("/")
def home():
    return {"status": "Bot running"}


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        text_lower = text.lower()

        if text_lower == "/start" or text_lower == "hola":
            send_message(
                chat_id,
                "Hola 👋 Soy RespiraNL Bot.\n\n"
                "Escribe una ciudad de Nuevo León para consultar su calidad del aire.\n\n"
            )
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

    original_city = city
    city = city.lower().strip()
    city = CITY_ALIASES.get(city, city)

    url = f"https://api.waqi.info/feed/{city}/?token={WAQI_TOKEN}"
    response = requests.get(url).json()

    if response.get("status") == "ok":
        data = response["data"]
        aqi = data.get("aqi")
        station_name = data["city"]["name"]

        message = "🌎 Calidad del aire\n"
        message += f"Consulta solicitada: {original_city}\n"
        message += f"Estación utilizada: {station_name}\n"
        message += f"AQI: {aqi}\n\n"

        if isinstance(aqi, int):
            if aqi <= 50:
                message += "🟢 Buena\nIdeal para actividades al aire libre."
            elif aqi <= 100:
                message += "🟡 Moderada\nPersonas sensibles deben limitar exposición prolongada."
            elif aqi <= 150:
                message += "🟠 Dañina para grupos sensibles."
            elif aqi <= 200:
                message += "🔴 Dañina."
            else:
                message += "🟣 Muy dañina."
        else:
            message += "⚠️ No se pudo interpretar el índice AQI."

    else:
        message = (
            f"⚠️ No existe una estación oficial de monitoreo en '{original_city}'.\n\n"
            "Actualmente solo puedo mostrar datos donde hay sensores registrados.\n"
            "Intenta con Monterrey, San Pedro o Santa Catarina."
        )

    send_message(chat_id, message)
