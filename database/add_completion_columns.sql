-- Script SQL simple pour ajouter les colonnes de complétion
-- Exécuter directement dans votre interface PostgreSQL (pgAdmin, DBeaver, etc.)

-- Ajouter la colonne status
ALTER TABLE rapport_journalier 
ADD COLUMN status VARCHAR(20) DEFAULT 'brouillon' 
CHECK (status IN ('brouillon', 'partiel', 'complet', 'finalise'));

-- Ajouter la colonne completion_percentage
ALTER TABLE rapport_journalier 
ADD COLUMN completion_percentage INTEGER DEFAULT 0 
CHECK (completion_percentage >= 0 AND completion_percentage <= 100);

-- Ajouter la colonne last_updated
ALTER TABLE rapport_journalier 
ADD COLUMN last_updated TIMESTAMP DEFAULT now();

-- Mettre à jour les rapports existants
UPDATE rapport_journalier 
SET status = 'brouillon', completion_percentage = 0, last_updated = now()
WHERE status IS NULL OR completion_percentage IS NULL;

-- Vérifier que les colonnes ont été ajoutées
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'rapport_journalier' 
AND column_name IN ('status', 'completion_percentage', 'last_updated')
ORDER BY column_name;
