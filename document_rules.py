"""Règles de détection des documents requis pour les appels d'offre."""

GENERIC_RULES = [
    {"label": "Acte d'engagement (AE)", "keywords": ["acte d'engagement", "ae"], "category": "Offre"},
    {"label": "Règlement de consultation (RC)", "keywords": ["règlement de consultation", "rc"], "category": "Offre"},
    {"label": "CCAP", "keywords": ["ccap", "clauses administratives"], "category": "Contrat"},
    {"label": "CCTP", "keywords": ["cctp", "clauses techniques"], "category": "Contrat"},
    {"label": "BPU", "keywords": ["bpu", "bordereau des prix"], "category": "Financier"},
    {"label": "DQE", "keywords": ["dqe", "quantitatif estimatif"], "category": "Financier"},
    {"label": "DC1", "keywords": ["dc1", "lettre de candidature"], "category": "Candidature"},
    {"label": "DC2", "keywords": ["dc2", "déclaration du candidat"], "category": "Candidature"},
    {"label": "Déclaration sur l'honneur", "keywords": ["déclaration sur l'honneur", "interdiction"], "category": "Candidature"},
]

SECTOR_RULES = {
    "alimentaire": [
        {"label": "Certification Bio", "keywords": ["bio", "egalim", "agriculture biologique"], "category": "Certification"},
        {"label": "Certificat ISO / HACCP", "keywords": ["iso", "haccp"], "category": "Certification"},
        {"label": "Fiches techniques des produits", "keywords": ["fiche technique", "produit"], "category": "Technique"},
    ],
    "travaux": [
        {"label": "Attestation décennale", "keywords": ["décennale", "assurance décennale"], "category": "Assurance"},
        {"label": "PPSPS", "keywords": ["ppsps", "sécurité chantier"], "category": "Sécurité"},
    ],
    "informatique": [
        {"label": "Matrice de conformité fonctionnelle", "keywords": ["matrice", "conformité"], "category": "Technique"},
        {"label": "Plan d'assurance sécurité", "keywords": ["sécurité", "cybersécurité"], "category": "Sécurité"},
    ]
}


