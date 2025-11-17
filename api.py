"""API FastAPI pour exposer la logique d'analyse des AO au front React."""

from __future__ import annotations

import datetime as dt
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from extract_required_documents import detect_sector, extract_required_documents
from utils import (
    extract_email,
    extract_postal_address,
    guess_buyer,
    guess_deadline,
    load_docx_text,
    load_pdf_text,
)

app = FastAPI(title="AO Analyzer API", version="1.0.0")

# Autorise le front React en dev (tous les ports locaux courants)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_file_text(name: str, raw: bytes) -> str:
    """Utilise les mêmes fonctions utilitaires que Streamlit pour extraire le texte."""
    lower = name.lower()
    if lower.endswith(".pdf"):
        return load_pdf_text(raw)
    if lower.endswith(".docx"):
        return load_docx_text(raw)
    if lower.endswith(".txt"):
        return raw.decode("utf-8", errors="ignore")
    return ""


@app.post("/analyze")
async def analyze_ao(files: List[UploadFile] = File(...)):
    """Analyse les fichiers d'appel d'offre et renvoie les mêmes infos que la page Streamlit."""
    texts: List[str] = []
    files_data: List[tuple[str, bytes]] = []

    for f in files:
        raw = await f.read()
        files_data.append((f.filename, raw))
        text = _read_file_text(f.filename, raw)
        if text:
            texts.append(text)

    if not texts:
        return {
            "success": False,
            "message": "Aucun texte n'a pu être extrait des documents.",
        }

    combined_text = "\n\n".join(texts)

    # Détection du secteur
    sector: Optional[str] = detect_sector(combined_text)

    # Documents requis
    required_docs = extract_required_documents(combined_text, files_data)

    # Informations complémentaires
    email_to = extract_email(combined_text)
    postal_address = extract_postal_address(combined_text)
    buyer = guess_buyer(combined_text)
    deadline_dt: Optional[dt.datetime] = guess_deadline(combined_text)
    deadline = deadline_dt.isoformat() if deadline_dt else None

    return {
        "success": True,
        "sector": sector,
        "required_documents": required_docs,
        "email_to": email_to,
        "postal_address": postal_address,
        "buyer": buyer,
        "deadline": deadline,
    }


@app.get("/health")
def health():
    """Endpoint simple de santé pour vérifier que l'API tourne."""
    return {"status": "ok"}






