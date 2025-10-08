import json
import os
import re
from datetime import datetime


_INTENTIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "intentions.json")
try:
    with open(_INTENTIONS_PATH, "r", encoding="utf-8") as f:
        INTENTIONS = json.load(f)
except Exception:
    INTENTIONS = {}


MONTHS_FR = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}


def _parse_date(text: str):
    text_norm = text.strip()
    # formats: 18/07/25 or 18-07-2025
    m = re.search(r"(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})", text_norm)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = 2000 + y if y < 100 else y
        return datetime(y, mth, d).date().isoformat()
    # format: 18 juillet 2025
    m = re.search(r"(\d{1,2})\s+([a-zA-Zéèêàùîôâç]+)\s+(\d{4})", text_norm, re.IGNORECASE)
    if m:
        d = int(m.group(1))
        month_name = m.group(2).lower()
        y = int(m.group(3))
        mth = MONTHS_FR.get(month_name)
        if mth:
            return datetime(y, mth, d).date().isoformat()
    return None


def _extract_type_activite(text: str):
    lowered = text.lower()
    for type_key in INTENTIONS.keys():
        if type_key.replace("_", " ") in lowered or type_key in lowered:
            return type_key.replace("_", " ").title()
    # heuristic keywords
    if "mobilier" in lowered:
        return "Mobilier urbain"
    if "collecte" in lowered:
        return "Collecte"
    if "anomal" in lowered:
        return "Anomalies"
    if "opérations spéciales" in lowered or "operations speciales" in lowered or "operation speciale" in lowered:
        return "Opérations spéciales"
    return None


def _extract_zone(text: str):
    # Heuristic: take the segment after '-' and before ':'
    m = re.search(r"-\s*([^:]+):", text)
    if m:
        candidate = m.group(1).strip()
        # If the candidate starts with a known type label, strip it (case-insensitive)
        m2 = re.match(r"^(mobilier\s+urbain|collecte|anomalies|op[ée]rations?\s+sp[ée]ciales?)\s+(.+)$", candidate, re.IGNORECASE)
        if m2:
            return m2.group(2).strip(" \t-:\u00a0")
        return candidate
    # fallback: city-like word + optional segment after 'au/à'
    m = re.search(r"\b(Kaolack|Dakar|Thies|Thiès|Ziguinchor|Saint[- ]Louis)\b([^\.]*)", text, re.IGNORECASE)
    if m:
        return (m.group(1) + (m.group(2) or "")).strip()
    return None


def _extract_activites(text: str):
    activities = []
    lowered = text.lower()
    for type_key, phrases in INTENTIONS.items():
        for p in phrases:
            if p.lower() in lowered:
                activities.append(p)
    # fallbacks based on common verbs
    if not activities:
        candidates = re.split(r"[,;]", text)
        for c in candidates:
            c = c.strip()
            if len(c) > 3 and any(v in c.lower() for v in ["nettoy", "réfect", "refect", "install", "peint", "collect", "panne", "dépôt", "depot", "inaccessible"]):
                activities.append(c)
    # deduplicate
    seen = set()
    unique = []
    for a in activities:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique or None


def parse_message_text(text: str):
    if not text:
        return {}
    date = _parse_date(text)
    type_activite = _extract_type_activite(text)
    zone = _extract_zone(text)
    activites = _extract_activites(text)
    # Extract optional time like (14:00)
    heure = None
    m_time = re.search(r"\((\d{1,2}:\d{2})\)", text)
    if m_time:
        hhmm = m_time.group(1)
        try:
            heure = datetime.strptime(hhmm, "%H:%M").time().isoformat()
        except Exception:
            heure = None

    # Try to extract a free-form comment after ':' and remove time token
    commentaire = None
    m = re.search(r":\s*(.+)$", text, re.DOTALL)
    if m:
        commentaire = m.group(1).strip()
        # remove time token if present
        if m_time:
            commentaire = re.sub(r"\s*\(\d{1,2}:\d{2}\)\s*", " ", commentaire).strip()
        # if commentaire equals or basically duplicates an activity phrase, drop it
        if activites and commentaire:
            comm_norm = commentaire.strip().rstrip('.').lower()
            for a in activites:
                a_norm = a.strip().rstrip('.').lower()
                if comm_norm == a_norm or comm_norm.startswith(a_norm):
                    commentaire = None
                    break

    return {
        "date": date,
        "zone": zone,
        "type_activite": type_activite,
        "activites": activites,
        "commentaire": commentaire,
        "heure": heure,
    }



