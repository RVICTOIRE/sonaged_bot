#!/usr/bin/env python3
"""
Script Python pour exécuter la migration de base de données
Alternative au script PowerShell quand psql n'est pas accessible
"""

import psycopg2
import os
from urllib.parse import urlparse

def get_db_connection():
    """Se connecter à la base de données en utilisant les variables d'environnement"""
    try:
        # Essayer d'abord avec les variables d'environnement séparées
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        dbname = os.getenv('DB_NAME', 'sonaged_reporting')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '123456789')
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        # Définir l'encodage après la connexion
        conn.set_client_encoding("UTF8")
        return conn
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return None

def run_migration():
    """Exécuter la migration pour ajouter les colonnes de statut"""
    conn = get_db_connection()
    if not conn:
        print("❌ Impossible de se connecter à la base de données")
        return False
    
    try:
        with conn.cursor() as cur:
            print("🔄 Exécution de la migration...")
            
            # Vérifier et ajouter la colonne status
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'rapport_journalier' AND column_name = 'status'
            """)
            
            if not cur.fetchone():
                print("➕ Ajout de la colonne 'status'...")
                cur.execute("""
                    ALTER TABLE rapport_journalier 
                    ADD COLUMN status VARCHAR(20) DEFAULT 'brouillon' 
                    CHECK (status IN ('brouillon', 'partiel', 'complet', 'finalise'))
                """)
            else:
                print("✅ Colonne 'status' existe déjà")
            
            # Vérifier et ajouter la colonne completion_percentage
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'rapport_journalier' AND column_name = 'completion_percentage'
            """)
            
            if not cur.fetchone():
                print("➕ Ajout de la colonne 'completion_percentage'...")
                cur.execute("""
                    ALTER TABLE rapport_journalier 
                    ADD COLUMN completion_percentage INTEGER DEFAULT 0 
                    CHECK (completion_percentage >= 0 AND completion_percentage <= 100)
                """)
            else:
                print("✅ Colonne 'completion_percentage' existe déjà")
            
            # Vérifier et ajouter la colonne last_updated
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'rapport_journalier' AND column_name = 'last_updated'
            """)
            
            if not cur.fetchone():
                print("➕ Ajout de la colonne 'last_updated'...")
                cur.execute("""
                    ALTER TABLE rapport_journalier 
                    ADD COLUMN last_updated TIMESTAMP DEFAULT now()
                """)
            else:
                print("✅ Colonne 'last_updated' existe déjà")
            
            # Mettre à jour les rapports existants
            print("🔄 Mise à jour des rapports existants...")
            cur.execute("""
                UPDATE rapport_journalier 
                SET status = 'brouillon', completion_percentage = 0, last_updated = now()
                WHERE status IS NULL OR completion_percentage IS NULL
            """)
            
            conn.commit()
            print("✅ Migration exécutée avec succès!")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Démarrage de la migration de base de données...")
    success = run_migration()
    
    if success:
        print("\n🎉 Migration terminée avec succès!")
        print("Les colonnes de statut de complétion ont été ajoutées à la table rapport_journalier.")
    else:
        print("\n💥 Échec de la migration.")
        print("Vérifiez votre connexion à la base de données et les permissions.")
