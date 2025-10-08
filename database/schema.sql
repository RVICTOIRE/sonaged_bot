CREATE TABLE IF NOT EXISTS agents (
  id SERIAL PRIMARY KEY,
  nom VARCHAR(100),
  matricule VARCHAR(50) UNIQUE,
  zone_affectation VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS rapports (
  id SERIAL PRIMARY KEY,
  agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
  date_rapport DATE,
  heure_rapport TIME,
  zone TEXT,
  type_activite TEXT,
  activites TEXT[],
  photo_url TEXT,
  latitude FLOAT,
  longitude FLOAT,
  commentaire TEXT,
  status VARCHAR(20) DEFAULT 'en_attente',
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rapports_date ON rapports(date_rapport);
CREATE INDEX IF NOT EXISTS idx_rapports_agent ON rapports(agent_id);
CREATE INDEX IF NOT EXISTS idx_rapports_zone ON rapports USING gin (to_tsvector('simple', coalesce(zone,'')));

-- Daily Report Schema (journalier)
CREATE TABLE IF NOT EXISTS rapport_journalier (
  id SERIAL PRIMARY KEY,
  date_rapport DATE NOT NULL,
  unite_commune TEXT, -- ex: Medina
  agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
  observation_rh TEXT,
  status VARCHAR(20) DEFAULT 'brouillon' CHECK (status IN ('brouillon', 'partiel', 'complet', 'finalise')),
  completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
  last_updated TIMESTAMP DEFAULT now(),
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS effectifs_jour (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  periode VARCHAR(20) NOT NULL CHECK (periode IN ('matin','apres_midi')),
  categorie TEXT NOT NULL, -- Collecteurs, Balayeurs, etc.
  effectifs INTEGER,
  presents INTEGER,
  absents INTEGER,
  malades INTEGER,
  conges INTEGER,
  remplacement INTEGER
);

CREATE TABLE IF NOT EXISTS collecte_indicateurs (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  circuits_planifies INTEGER,
  circuits_collectes INTEGER,
  tonnage NUMERIC(10,2),
  depots_recurrents INTEGER,
  depots_recurrents_leves INTEGER,
  depots_sauvages_identifies TEXT,
  depots_sauvages_traites TEXT
);

CREATE TABLE IF NOT EXISTS collecte_circuits (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  nom TEXT,
  numero_porte TEXT,
  heure_debut TIME,
  heure_fin TIME,
  duree TEXT,
  poids TEXT,
  observation TEXT
);

CREATE TABLE IF NOT EXISTS polybenne (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  sites_caisse INTEGER,
  nb_caisses INTEGER,
  nb_caisses_levees INTEGER,
  poids_collecte NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS nettoiement (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  circuits_planifies TEXT,
  circuits_balayes TEXT,
  km_planifie TEXT,
  km_balayes TEXT,
  km_desensables NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS bacs_indicateurs (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  libelle TEXT, -- PRN, PP, Bacs de rue
  sites INTEGER,
  nb_bacs INTEGER,
  nb_bacs_leves INTEGER,
  observation TEXT
);

CREATE TABLE IF NOT EXISTS moyens_equipements (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  nb_agents INTEGER,
  nb_pelles_mecaniques INTEGER,
  nb_tasseuses INTEGER,
  nb_camions_ouvert INTEGER,
  sites_quartiers TEXT
);

CREATE TABLE IF NOT EXISTS sites_intervention (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  nom_site TEXT
);

CREATE TABLE IF NOT EXISTS difficultes (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  contenu TEXT
);

CREATE TABLE IF NOT EXISTS recommandations (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  contenu TEXT
);

CREATE TABLE IF NOT EXISTS rapport_photos (
  id SERIAL PRIMARY KEY,
  rapport_id INTEGER REFERENCES rapport_journalier(id) ON DELETE CASCADE,
  photo_url TEXT
);


