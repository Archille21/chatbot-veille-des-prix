import os
import re
import time
import psycopg2
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Chargement des variables d'environnement (.env)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuration du produit
PRODUCT_NAME = "iPhone 12 Pro Max (Seconde main)"
GLOTELHO_URL = "https://glotelho.cm/fr/iphone-12-pro-max-seconde-main-128go-6go-ram-12mp-12mp-12mp-12mp-4k-li-ion-2815-mah-6-7-5g-03-mois.html"
PRICE_SELECTOR = "span.font-montserrat.font-extrabold, span.font-bold.text-gray-900"
TARGET_PRICE = 200000.0  # Prix cible en FCFA (Alerte si <= 200 000 FCFA)

CHECK_INTERVAL_HOURS = 6


def send_telegram_message(text: str):
    """Envoie un message via Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Variables Telegram manquantes dans le .env")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print("📲 Notification Telegram envoyée.")
    except Exception as e:
        print(f"❌ Erreur envoi Telegram : {e}")


def save_to_neon(product_name: str, url: str, price: float, target_price: float):
    """Enregistre la vérification dans la BDD Neon"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL manquante dans le .env")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id SERIAL PRIMARY KEY,
                product_name TEXT NOT NULL,
                product_url TEXT NOT NULL,
                price REAL NOT NULL,
                target_price REAL NOT NULL,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            INSERT INTO price_history (product_name, product_url, price, target_price)
            VALUES (%s, %s, %s, %s);
        """, (product_name, url, price, target_price))

        conn.commit()
        cursor.close()
        conn.close()
        print("💾 Données enregistrées dans Neon.")
    except Exception as e:
        print(f"❌ Erreur BDD Neon : {e}")


def clean_price(price_str: str) -> float:
    """Nettoie et extrait la valeur numérique du prix"""
    if not price_str:
        return 0.0
    cleaned = price_str.replace(" ", "").replace("\xa0", "").replace(",", "").strip()
    match = re.search(r"(\d+)", cleaned)
    if match:
        return float(match.group(1))
    return 0.0


def check_price() -> float:
    """Scrape le prix sur Glotelho"""
    print(f"\n🔍 [Vérification] Scraping de {PRODUCT_NAME}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(GLOTELHO_URL, wait_until="networkidle", timeout=45000)
            page.wait_for_selector(PRICE_SELECTOR, timeout=15000)
            raw_price = page.locator(PRICE_SELECTOR).first.inner_text()
            price = clean_price(raw_price)
            browser.close()
            return price
        except Exception as e:
            print(f"❌ Erreur pendant le scraping : {e}")
            browser.close()
            return 0.0


def run_sniper():
    print(f"🚀 Bot Price Sniper démarré ! (Vérification toutes les {CHECK_INTERVAL_HOURS} heures)")
    send_telegram_message(f"🚀 *Price Sniper Actif*\nSurveillance lancée pour : `{PRODUCT_NAME}`\nPrix cible : *{TARGET_PRICE:,.0f} FCFA*")

    while True:
        current_price = check_price()

        if current_price > 0:
            print(f"📊 Prix actuel : {current_price:,.0f} FCFA | Prix Cible : {TARGET_PRICE:,.0f} FCFA")
            
            # Sauvegarde en BDD
            save_to_neon(PRODUCT_NAME, GLOTELHO_URL, current_price, TARGET_PRICE)

            # Alerte si le prix est inférieur ou égal à la cible
            if current_price <= TARGET_PRICE:
                msg = (
                    f"🎯 *ALERTE BONNE AFFAIRE !*\n\n"
                    f"Le prix de *{PRODUCT_NAME}* a chuté !\n"
                    f"💰 *Prix actuel :* {current_price:,.0f} FCFA\n"
                    f"🎯 *Prix cible :* {TARGET_PRICE:,.0f} FCFA\n\n"
                    f"🔗 [Acheter sur Glotelho]({GLOTELHO_URL})"
                )
                send_telegram_message(msg)
            else:
                print("ℹ️ Le prix reste au-dessus du prix cible. Pas de notification d'alerte envoyée.")
        else:
            print("⚠️ Impossible d'obtenir le prix lors de cette session.")

        # Pause de 6 heures (21 600 secondes)
        time.sleep(CHECK_INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    run_sniper()