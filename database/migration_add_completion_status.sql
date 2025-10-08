-- Migration pour ajouter les colonnes de statut de complétion
-- Exécuter ce script si la table rapport_journalier existe déjà sans ces colonnes

-- Ajouter les colonnes si elles n'existent pas
DO $$ 
BEGIN
    -- Ajouter la colonne status si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'rapport_journalier' AND column_name = 'status') THEN
        ALTER TABLE rapport_journalier 
        ADD COLUMN status VARCHAR(20) DEFAULT 'brouillon' 
        CHECK (status IN ('brouillon', 'partiel', 'complet', 'finalise'));
    END IF;
    
    -- Ajouter la colonne completion_percentage si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'rapport_journalier' AND column_name = 'completion_percentage') THEN
        ALTER TABLE rapport_journalier 
        ADD COLUMN completion_percentage INTEGER DEFAULT 0 
        CHECK (completion_percentage >= 0 AND completion_percentage <= 100);
    END IF;
    
    -- Ajouter la colonne last_updated si elle n'existe pas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'rapport_journalier' AND column_name = 'last_updated') THEN
        ALTER TABLE rapport_journalier 
        ADD COLUMN last_updated TIMESTAMP DEFAULT now();
    END IF;
END $$;

-- Mettre à jour les rapports existants avec un statut par défaut
UPDATE rapport_journalier 
SET status = 'brouillon', completion_percentage = 0, last_updated = now()
WHERE status IS NULL OR completion_percentage IS NULL;
