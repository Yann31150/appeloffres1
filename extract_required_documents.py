"""Extraction des documents requis à partir du texte des documents d'appel d'offre."""

import re

from document_rules import GENERIC_RULES, SECTOR_RULES


def detect_sector(text):
    """Détecte le secteur d'activité à partir du texte."""
    text = text.lower()
    
    if any(w in text for w in ["alimentaire", "denrées", "egalim"]):
        return "alimentaire"
    if any(w in text for w in ["travaux", "chantier", "btp"]):
        return "travaux"
    if any(w in text for w in ["informatique", "réseau", "logiciel"]):
        return "informatique"
    
    return None


def extract_context(text, keywords, window=250):
    """Extrait le contexte autour des mots-clés trouvés."""
    t = text.lower()
    for kw in keywords:
        pos = t.find(kw.lower())
        if pos != -1:
            return text[max(0, pos - window):pos + window]
    return ""


def extract_required_documents(text, files_data=None):
    """
    Extrait la liste des documents requis à partir du texte analysé.
    
    Args:
        text: Texte extrait des documents d'appel d'offre
        files_data: Liste optionnelle de tuples (nom_fichier, contenu_bytes)
    
    Returns:
        Liste de dictionnaires avec les informations sur les documents requis
    """
    results = []
    text_lower = text.lower()

    # 1. Règles génériques
    rules = GENERIC_RULES.copy()

    # 2. Détection automatique du secteur
    sector = detect_sector(text)
    if sector and sector in SECTOR_RULES:
        rules.extend(SECTOR_RULES[sector])

    # 3. Analyse des règles
    for rule in rules:
        score = sum(kw in text_lower for kw in rule["keywords"])

        if score > 0:
            results.append({
                "label": rule["label"],
                "category": rule["category"],
                "summary": f"Détecté via {score} mot(s)-clé",
                "key": rule["label"].lower().replace(" ", "_").replace("'", "_"),
                "keywords": rule["keywords"],  # Ajout des keywords pour la recherche
                "source_section": extract_context(text, rule["keywords"]),
                "score": score
            })

    # Tri par pertinence
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

