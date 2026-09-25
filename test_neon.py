import os
import psycopg2
from dotenv import load_dotenv

# Charge les variables d'environnement (.env)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    if not DATABASE_URL:
        print("❌ Erreur : DATABASE_URL n'est pas configurée dans le fichier .env")
        return False

    try:
        # Connexion à Neon
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Création de la table pour enregistrer l'historique des prix
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

        conn.commit()
        print("✅ Table 'price_history' créée ou déjà existante dans Neon.")

        # Test d'insertion d'une ligne
        cursor.execute("""
            INSERT INTO price_history (product_name, product_url, price, target_price)
            VALUES (%s, %s, %s, %s);
        """, ("Produit Test", "https://example.com/item", 299.99, 250.00))

        conn.commit()
        print("✅ Donnée de test insérée avec succès dans Neon.")

        # Lecture de la donnée
        cursor.execute("SELECT * FROM price_history ORDER BY checked_at DESC LIMIT 1;")
        row = cursor.fetchone()
        print(f"📊 Dernière ligne lue depuis Neon : {row}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erreur de connexion à Neon : {e}")
        return False

if __name__ == "__main__":
    init_db()