import requests
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

@app.post("/webhook")
async def webhook(update: dict):
    message = update.get("message")
    
    if message:
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        response_text = "RespiraNL activo 🌎"

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": response_text
            }
        )

    return {"ok": True}
