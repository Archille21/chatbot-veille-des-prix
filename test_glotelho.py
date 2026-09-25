import re
from playwright.sync_api import sync_playwright

GLOTELHO_URL = "https://glotelho.cm/fr/iphone-12-pro-max-seconde-main-128go-6go-ram-12mp-12mp-12mp-12mp-4k-li-ion-2815-mah-6-7-5g-03-mois.html"

# Sélecteur raccourci et robuste basé sur la structure Nuxt + classes Tailwind clés
PRICE_SELECTOR = "span.font-montserrat.font-extrabold, span.font-bold.text-gray-900"

def clean_price(price_str: str) -> float:
    """
    Nettoie le texte (ex: "225 000 FCFA" -> 225000.0)
    """
    if not price_str:
        return 0.0
    
    # Enlève tous les espaces (y compris les espaces insécables)
    cleaned = price_str.replace(" ", "").replace("\xa0", "").replace(",", "").strip()
    
    # Extrait la suite de chiffres
    match = re.search(r"(\d+)", cleaned)
    if match:
        return float(match.group(1))
    return 0.0

def scrape_glotelho_price():
    print("🌐 Chargement de la page Glotelho (Nuxt.js)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # wait_until="networkidle" est crucial pour les sites Nuxt/Vue
            page.goto(GLOTELHO_URL, wait_until="networkidle", timeout=45000)
            
            # Attente spécifique de l'élément de prix
            page.wait_for_selector(PRICE_SELECTOR, timeout=15000)
            
            # Récupération du premier élément correspondant
            price_element = page.locator(PRICE_SELECTOR).first
            raw_price = price_element.inner_text()
            
            print(f"🔍 Texte brut extrait : '{raw_price}'")
            
            price = clean_price(raw_price)
            print(f"✅ Prix extrait avec succès : {price} FCFA")
            
            browser.close()
            return price

        except Exception as e:
            print(f"❌ Erreur lors du scraping : {e}")
            browser.close()
            return 0.0

if __name__ == "__main__":
    scrape_glotelho_price()