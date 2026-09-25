import os
import requests
from dotenv import load_dotenv
# Charge les variables contenues dans le fichier .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Erreur : Les variables d'environnement ne sont pas configurées dans le fichier .env")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Message Telegram envoyé avec succès !")
    else:
        print(f"❌ Erreur lors de l'envoi : {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    send_telegram_message("🎯 *Test Sniper Bot* : Configuration sécurisée validée !")