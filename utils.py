"""Fonctions utilitaires pour l'analyse de documents d'appel d'offre."""

import datetime as dt
import io
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


def load_pdf_text(raw: bytes) -> str:
    """Extrait le texte d'un PDF avec plusieurs méthodes de secours."""
    if not raw:
        return ""
    
    text = ""
    
    # Méthode 1 : pypdf (méthode principale)
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        
        pages = []
        for page in reader.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
            except Exception:
                continue
        
        if pages:
            text = "\n".join(pages)
            if len(text.strip()) > 50:  # Au moins 50 caractères trouvés
                return text
    except Exception:
        pass
    
    # Méthode 2 : PyMuPDF (fitz) - souvent meilleur pour extraire le texte
    try:
        import fitz
        doc = fitz.open(stream=raw, filetype="pdf")
        pages = []
        for page in doc:
            try:
                page_text = page.get_text()
                if page_text:
                    pages.append(page_text)
            except Exception:
                continue
        doc.close()
        
        if pages:
            text = "\n".join(pages)
            if len(text.strip()) > 50:
                return text
    except Exception:
        pass
    
    # Méthode 3 : pdfplumber (alternative)
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            pages = []
            for page in pdf.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        pages.append(page_text)
                except Exception:
                    continue
            
            if pages:
                text = "\n".join(pages)
                if len(text.strip()) > 50:
                    return text
    except Exception:
        pass
    
    return text


def load_docx_text(raw: bytes) -> str:
    """Extrait le texte d'un fichier DOCX."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(raw))
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception:
        return ""


def extract_email(text: str) -> Optional[str]:
    """Extrait l'adresse email de contact pour l'envoi du dossier depuis le texte."""
    if not text:
        return None
    
    lines = text.split('\n')
    
    # Priorité 1 : Cherche dans la section "Conditions d'envoi ou de remise des plis"
    sections_conditions_envoi = []
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if re.search(r'conditions?\s+d\'?envoi\s+(?:ou\s+de\s+)?remise\s+des\s+plis?', line_lower):
            # Prend toute la section (jusqu'à la prochaine section majeure ou 150 lignes)
            end_idx = i + 150
            for j in range(i + 1, min(len(lines), i + 150)):
                if re.search(r'^(chapitre|section|partie|titre)\s+', lines[j].lower()):
                    if j > i + 10:
                        end_idx = j
                        break
            section = '\n'.join(lines[max(0, i-1):end_idx])
            sections_conditions_envoi.append(section)
    
    # Cherche dans les sections pertinentes
    email_keywords = [
        r'adresse\s+electronique[^\w]',
        r'adresse\s+email[^\w]',
        r'adresse\s+mail[^\w]',
        r'courrier\s+electronique[^\w]',
        r'contact[^\w]',
        r'envoyer\s+à[^\w]',
        r'destinataire[^\w]',
        r'depot\s+(?:electronique|numerique)[^\w]',
    ]
    
    relevant_sections = []
    
    # Cherche d'abord dans la section "Conditions d'envoi ou de remise des plis"
    if sections_conditions_envoi:
        for section in sections_conditions_envoi:
            section_lower = section.lower()
            for keyword in email_keywords:
                if re.search(keyword, section_lower):
                    relevant_sections.insert(0, section)
                    break
    
    # Cherche ensuite dans le reste du document
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for keyword in email_keywords:
            if re.search(keyword, line_lower):
                section = '\n'.join(lines[max(0, i-1):min(len(lines), i+5)])
                if section not in relevant_sections:
                    relevant_sections.append(section)
                break
    
    text_to_search = '\n'.join(relevant_sections) if relevant_sections else text
    
    # Pattern amélioré pour les emails - plus robuste
    # Supporte les formats : user@domain.com, user.name@domain.co.uk, user+tag@domain.fr
    email_patterns = [
        r'\b[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Z|a-z]{2,}\b',
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
    ]
    
    emails = []
    for pattern in email_patterns:
        found = re.findall(pattern, text_to_search, re.IGNORECASE)
        if found:
            # Si le pattern retourne un tuple (groupe capturé), prendre le groupe
            if isinstance(found[0], tuple):
                emails.extend([f[0] if f[0] else f for f in found])
            else:
                emails.extend(found)
    
    if not emails:
        # Si pas trouvé dans les sections, cherche dans tout le texte
        for pattern in email_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                if isinstance(found[0], tuple):
                    emails.extend([f[0] if f[0] else f for f in found])
                else:
                    emails.extend(found)
    
    if not emails:
        return None
    
    # Filtre les emails courants à éviter
    excluded = ['example.com', 'test.com', 'noreply', 'no-reply', 'webmaster', 'admin@localhost']
    for email in emails:
        email_lower = email.lower().strip()
        # Vérifier que c'est un email valide
        if '@' in email_lower and '.' in email_lower.split('@')[1]:
            if not any(exc in email_lower for exc in excluded):
                return email_lower
    
    return emails[0].lower().strip() if emails else None


def extract_urls(text: str, pdf_raw: Optional[bytes] = None) -> List[str]:
    """Extrait les URLs depuis le texte et/ou directement depuis le PDF."""
    urls = []
    
    # Méthode 1 : Extraire les liens directement depuis le PDF (plus fiable)
    if pdf_raw:
        try:
            import fitz
            doc = fitz.open(stream=pdf_raw, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Récupère tous les liens de la page
                links = page.get_links()
                for link in links:
                    if 'uri' in link:
                        url = link['uri']
                        if url and url not in urls:
                            urls.append(url)
            doc.close()
        except Exception:
            pass
    
    # Méthode 2 : Extraire les URLs depuis le texte avec des patterns regex
    if text:
        # Patterns pour différents types d'URLs
        url_patterns = [
            # URLs complètes avec http/https
            r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?',
            # URLs sans protocole mais avec www
            r'www\.(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?',
            # URLs mailto
            r'mailto:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',
        ]
        
        for pattern in url_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            for url in found:
                url_clean = url.strip().rstrip('.,;:!?)')
                # Normaliser les URLs www sans http
                if url_clean.startswith('www.'):
                    url_clean = 'http://' + url_clean
                if url_clean and url_clean not in urls:
                    urls.append(url_clean)
    
    # Filtrer et nettoyer les URLs
    filtered_urls = []
    excluded_domains = ['localhost', '127.0.0.1', 'example.com', 'test.com']
    
    for url in urls:
        url_lower = url.lower()
        # Exclure les URLs non pertinentes
        if not any(exc in url_lower for exc in excluded_domains):
            # Nettoyer l'URL
            url_clean = url.strip().rstrip('.,;:!?)')
            if url_clean and url_clean not in filtered_urls:
                filtered_urls.append(url_clean)
    
    return filtered_urls


def extract_postal_address(text: str) -> Optional[str]:
    """Extrait une adresse postale du texte, en priorité depuis la première page."""
    if not text:
        return None
    
    # Prendre les 2000 premiers caractères (première page généralement)
    first_page_text = text[:2000]
    
    # Patterns pour les adresses françaises - plusieurs variantes
    address_patterns = [
        # Format complet : numéro + rue + ville + code postal
        r'(?:\d+[,\s]+)?(?:[A-Za-zÀ-ÿ\s]+(?:rue|avenue|boulevard|place|chemin|route|impasse|allée|passage)[A-Za-zÀ-ÿ\s,]+(?:\d{5}|[A-Za-zÀ-ÿ\s]+))',
        # Format avec code postal en fin
        r'[A-Za-zÀ-ÿ\s]+(?:rue|avenue|boulevard|place|chemin|route|impasse|allée|passage)[A-Za-zÀ-ÿ\s,]+(?:\d{5})',
        # Format avec numéro de rue
        r'\d+[,\s]+(?:rue|avenue|boulevard|place|chemin|route|impasse|allée|passage)[A-Za-zÀ-ÿ\s,]+(?:\d{5}|[A-Za-zÀ-ÿ\s]+)',
        # Format simple avec code postal
        r'[A-Za-zÀ-ÿ\s]{10,}(?:,\s*)?\d{5}\s+[A-Za-zÀ-ÿ\s]+',
    ]
    
    # Chercher d'abord dans la première page
    for pattern in address_patterns:
        matches = re.findall(pattern, first_page_text, re.IGNORECASE)
        if matches:
            # Prendre la première correspondance et nettoyer
            address = matches[0].strip()
            # Nettoyer les espaces multiples
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 10:  # Au moins 10 caractères pour être valide
                return address
    
    # Si pas trouvé dans la première page, chercher dans tout le texte
    for pattern in address_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            address = matches[0].strip()
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 10:
                return address
    
    return None


def guess_buyer(text: str) -> Optional[str]:
    """Tente de deviner le nom de l'acheteur."""
    # Recherche de patterns communs
    patterns = [
        r'acheteur[:\s]+([A-Z][A-Za-zÀ-ÿ\s]+)',
        r'commande[:\s]+([A-Z][A-Za-zÀ-ÿ\s]+)',
        r'maître[:\s]+d\'?ouvrage[:\s]+([A-Z][A-Za-zÀ-ÿ\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def guess_deadline(text: str):
    """Tente de deviner la date et heure limite de dépôt/réception des offres."""
    import datetime as dt
    
    if not text:
        return None
    
    # Prendre les 5000 premiers caractères (pour capturer plus de contexte)
    first_page_text = text[:5000]
    
    # PRIORITÉ 1 : Patterns spécifiques pour "remise des offres", "dépôt des offres", etc.
    # Ces patterns sont prioritaires car ils indiquent clairement la date limite
    priority_patterns_with_time = [
        # "Remise des offres le 24/11/2025 à 12h00"
        r'(?:remise[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]+(?:le|au|avant|au[:\s]+plus[:\s]+tard)[:\s]+)?(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})[:\s]*(?:à|avant)[:\s]*(\d{1,2})[:hH.](\d{2})',
        # "Remise des offres : 24/11/2025 à 12h00"
        r'remise[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]*:?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})[:\s]*(?:à|avant)[:\s]*(\d{1,2})[:hH.](\d{2})',
        # "Dépôt des offres le 24/11/2025 à 12h00"
        r'(?:d[ée]p[ôo]t[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]+(?:le|au|avant|au[:\s]+plus[:\s]+tard)[:\s]+)?(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})[:\s]*(?:à|avant)[:\s]*(\d{1,2})[:hH.](\d{0,2})',
        # "Date limite de remise des offres : 24/11/2025 à 12h00"
        r'date[:\s]+limite[:\s]+(?:de[:\s]+)?(?:remise|d[ée]p[ôo]t)[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]*:?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})[:\s]*(?:à|avant)[:\s]*(\d{1,2})[:hH.](\d{2})',
    ]
    
    # PRIORITÉ 2 : Patterns généraux pour capturer date ET heure
    patterns_with_time = [
        # "Date et heure limites de réception des offres : lundi 24 novembre 2025 à 12:00"
        # Pattern flexible - peut avoir ou non le jour de la semaine
        r'(?:(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)[\s,]+)?(\d{1,2})[\s,]+(janvier|f[ée]vrier|fevrier|mars|avril|mai|juin|juillet|ao[ûu]t|aout|septembre|octobre|novembre|d[ée]cembre|decembre)[\s,]+(\d{4})[\s,]*[àa]?\s*(\d{1,2})[:hH.](\d{2})',
        # "Date limite de réception des offres : 24/11/2025 à 12h00"
        r'(?:date[:\s]+limite[:\s]+(?:de[:\s]+)?(?:r[ée]ception|d[ée]p[ôo]t|remise)[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]+)?(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})[:\s]*(?:à|avant|avant\s+le)[:\s]*(\d{1,2})[hH:.]?(\d{0,2})',
        # "Réception des offres le 24/11/2025 à 12h00"
        r'(?:r[ée]ception[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]+(?:le|au|avant)[:\s]+)?(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})[:\s]*(?:à|avant)[:\s]*(\d{1,2})[hH:.]?(\d{0,2})',
        # "Date limite : 24/11/2025 12:00"
        r'(?:date[:\s]+limite[:\s]*:?[:\s]*)?(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})[:\s]+(\d{1,2})[hH:.](\d{2})',
    ]
    
    # Mapping des mois en français
    mois_fr = {
        'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
    }
    
    # PRIORITÉ 1 : Chercher d'abord les patterns prioritaires (remise/dépôt des offres)
    for pattern in priority_patterns_with_time:
        match = re.search(pattern, first_page_text, re.IGNORECASE)
        if match:
            try:
                jour = int(match.group(1))
                mois = int(match.group(2))
                annee_str = match.group(3)
                annee = int(annee_str) if len(annee_str) == 4 else (2000 + int(annee_str) if int(annee_str) < 100 else int(annee_str))
                heure_str = match.group(4) if len(match.groups()) >= 4 else "23"
                minute_str = match.group(5) if len(match.groups()) >= 5 and match.group(5) else "00"
                
                heure = int(heure_str) if heure_str and heure_str.isdigit() else 23
                minute = int(minute_str) if minute_str and minute_str.isdigit() else 0
                if heure > 23:
                    heure = 23
                if minute > 59:
                    minute = 59
                return dt.datetime(annee, mois, jour, heure, minute, 0, 0)
            except (ValueError, IndexError, AttributeError):
                continue
    
    # PRIORITÉ 2 : Chercher ensuite les patterns généraux avec heure dans la première page
    for i, pattern in enumerate(patterns_with_time):
        match = re.search(pattern, first_page_text, re.IGNORECASE)
        if match:
            try:
                # Pattern 0 : Format avec mois en lettres (ex: "lundi 24 novembre 2025 à 12:00")
                if i == 0 and len(match.groups()) >= 5:
                    jour = int(match.group(1))
                    mois_nom = match.group(2).lower()
                    annee = int(match.group(3))
                    heure = int(match.group(4))
                    minute = int(match.group(5))
                    
                    if mois_nom in mois_fr:
                        mois = mois_fr[mois_nom]
                        if heure > 23:
                            heure = 23
                        if minute > 59:
                            minute = 59
                        return dt.datetime(annee, mois, jour, heure, minute, 0, 0)
                
                # Patterns avec format numérique (ex: "24/11/2025 à 12:00")
                elif len(match.groups()) >= 3:
                    if i == 1 or i == 2:  # Patterns avec format DD/MM/YYYY
                        jour = int(match.group(1))
                        mois = int(match.group(2))
                        annee_str = match.group(3)
                        annee = int(annee_str) if len(annee_str) == 4 else (2000 + int(annee_str) if int(annee_str) < 100 else int(annee_str))
                        heure_str = match.group(4) if len(match.groups()) >= 4 else "23"
                        minute_str = match.group(5) if len(match.groups()) >= 5 and match.group(5) else "59"
                        
                        heure = int(heure_str) if heure_str else 23
                        minute = int(minute_str) if minute_str and minute_str.isdigit() else 59
                        if heure > 23:
                            heure = 23
                        if minute > 59:
                            minute = 59
                        return dt.datetime(annee, mois, jour, heure, minute, 0, 0)
                    else:  # Pattern avec format direct
                        jour = int(match.group(1))
                        mois = int(match.group(2))
                        annee_str = match.group(3)
                        annee = int(annee_str) if len(annee_str) == 4 else (2000 + int(annee_str) if int(annee_str) < 100 else int(annee_str))
                        heure = int(match.group(4)) if len(match.groups()) >= 4 else 23
                        minute = int(match.group(5)) if len(match.groups()) >= 5 else 59
                        if heure > 23:
                            heure = 23
                        if minute > 59:
                            minute = 59
                        return dt.datetime(annee, mois, jour, heure, minute, 0, 0)
            except (ValueError, IndexError, AttributeError) as e:
                continue
    
    # PRIORITÉ 3 : Patterns sans heure (date seulement) - mais prioriser ceux avec "remise/dépôt"
    priority_date_patterns = [
        r'remise[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]+(?:le|au|avant)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'd[ée]p[ôo]t[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]+(?:avant|le|au)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'date[:\s]+limite[:\s]+(?:de[:\s]+)?(?:remise|d[ée]p[ôo]t)[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]+(?:le|au|avant)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    
    date_patterns = [
        r'(?:date[:\s]+limite[:\s]+(?:de[:\s]+)?(?:r[ée]ception|d[ée]p[ôo]t|remise)[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:r[ée]ception[:\s]+(?:des[:\s]+)?(?:offres?|plis?)[:\s]+(?:le|au|avant)[:\s]+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'd[ée]p[ôo]t[:\s]+(?:avant|le|au)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})[:\s]+(?:date[:\s]+limite|d[ée]p[ôo]t|r[ée]ception)',
    ]
    
    # Chercher d'abord les patterns prioritaires (remise/dépôt)
    for pattern in priority_date_patterns:
        match = re.search(pattern, first_page_text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                    try:
                        date_obj = dt.datetime.strptime(date_str, fmt)
                        # Par défaut, mettre 23:59 si pas d'heure trouvée
                        return date_obj.replace(hour=23, minute=59, second=0, microsecond=0)
                    except ValueError:
                        continue
            except Exception:
                pass
    
    # Chercher dans la première page d'abord
    for pattern in date_patterns:
        match = re.search(pattern, first_page_text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                    try:
                        date_obj = dt.datetime.strptime(date_str, fmt)
                        # Par défaut, mettre 23:59 si pas d'heure trouvée
                        return date_obj.replace(hour=23, minute=59, second=0, microsecond=0)
                    except ValueError:
                        continue
            except Exception:
                pass
    
    # Si pas trouvé dans la première page, chercher dans tout le texte avec les mêmes priorités
    # PRIORITÉ 1 : Patterns prioritaires dans tout le texte
    for pattern in priority_patterns_with_time:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                jour = int(match.group(1))
                mois = int(match.group(2))
                annee_str = match.group(3)
                annee = int(annee_str) if len(annee_str) == 4 else (2000 + int(annee_str) if int(annee_str) < 100 else int(annee_str))
                heure_str = match.group(4) if len(match.groups()) >= 4 else "23"
                minute_str = match.group(5) if len(match.groups()) >= 5 and match.group(5) else "00"
                
                heure = int(heure_str) if heure_str and heure_str.isdigit() else 23
                minute = int(minute_str) if minute_str and minute_str.isdigit() else 0
                if heure > 23:
                    heure = 23
                if minute > 59:
                    minute = 59
                return dt.datetime(annee, mois, jour, heure, minute, 0, 0)
            except (ValueError, IndexError, AttributeError):
                continue
    
    # PRIORITÉ 2 : Patterns généraux dans tout le texte
    for i, pattern in enumerate(patterns_with_time):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                # Pattern 0 : Format avec mois en lettres
                if i == 0 and len(match.groups()) >= 5:
                    jour = int(match.group(1))
                    mois_nom = match.group(2).lower()
                    annee = int(match.group(3))
                    heure = int(match.group(4))
                    minute = int(match.group(5))
                    
                    if mois_nom in mois_fr:
                        mois = mois_fr[mois_nom]
                        if heure > 23:
                            heure = 23
                        if minute > 59:
                            minute = 59
                        return dt.datetime(annee, mois, jour, heure, minute, 0, 0)
                
                # Patterns avec format numérique
                elif len(match.groups()) >= 3:
                    if i == 1 or i == 2:
                        jour = int(match.group(1))
                        mois = int(match.group(2))
                        annee_str = match.group(3)
                        annee = int(annee_str) if len(annee_str) == 4 else (2000 + int(annee_str) if int(annee_str) < 100 else int(annee_str))
                        heure_str = match.group(4) if len(match.groups()) >= 4 else "23"
                        minute_str = match.group(5) if len(match.groups()) >= 5 and match.group(5) else "59"
                        
                        heure = int(heure_str) if heure_str else 23
                        minute = int(minute_str) if minute_str and minute_str.isdigit() else 59
                        if heure > 23:
                            heure = 23
                        if minute > 59:
                            minute = 59
                        return dt.datetime(annee, mois, jour, heure, minute, 0, 0)
                    else:
                        jour = int(match.group(1))
                        mois = int(match.group(2))
                        annee_str = match.group(3)
                        annee = int(annee_str) if len(annee_str) == 4 else (2000 + int(annee_str) if int(annee_str) < 100 else int(annee_str))
                        heure = int(match.group(4)) if len(match.groups()) >= 4 else 23
                        minute = int(match.group(5)) if len(match.groups()) >= 5 else 59
                        if heure > 23:
                            heure = 23
                        if minute > 59:
                            minute = 59
                        return dt.datetime(annee, mois, jour, heure, minute, 0, 0)
            except (ValueError, IndexError, AttributeError):
                continue
    
    # PRIORITÉ 3 : Patterns prioritaires (remise/dépôt) dans tout le texte
    for pattern in priority_date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                    try:
                        date_obj = dt.datetime.strptime(date_str, fmt)
                        return date_obj.replace(hour=23, minute=59, second=0, microsecond=0)
                    except ValueError:
                        continue
            except Exception:
                pass
    
    # Dernière tentative : patterns généraux dans tout le texte
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                    try:
                        date_obj = dt.datetime.strptime(date_str, fmt)
                        return date_obj.replace(hour=23, minute=59, second=0, microsecond=0)
                    except ValueError:
                        continue
            except Exception:
                pass
    
    return None


@dataclass
class ChecklistRow:
    """Représente une ligne de la checklist."""
    
    key: str
    label: str
    status: str
    source: str
    submission_path: str
    max_age_days: str = ""


def now_utc() -> dt.datetime:
    """Retourne la date/heure actuelle en UTC."""
    return dt.datetime.now(dt.timezone.utc)


def slugify(value: str) -> str:
    """Convertit une chaîne en slug (format URL-safe)."""
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-").lower()
    return slug or "ao"


def find_best_doc(base: Path, patterns: Sequence[str], max_age_days: Optional[int]) -> Optional[Path]:
    """Trouve le meilleur document correspondant aux critères."""
    if not base.exists():
        return None
    normalized = [p.lower() for p in patterns if p]
    best: Optional[Path] = None
    best_mtime = None
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if normalized and not all(term in name for term in normalized):
            continue
        stat = path.stat()
        if max_age_days is not None:
            age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
            if age > dt.timedelta(days=max_age_days):
                continue
        if best is None or stat.st_mtime > (best_mtime or 0):
            best = path
            best_mtime = stat.st_mtime
    return best


def find_all_matching_docs(base: Path, patterns: Sequence[str], max_age_days: Optional[int]) -> List[Path]:
    """Trouve tous les documents correspondant aux critères, triés par date de modification (plus récent d'abord).
    
    La recherche est flexible : si plusieurs patterns sont fournis, au moins un doit correspondre.
    Si un seul pattern est fourni, il doit correspondre.
    """
    if not base.exists():
        return []
    normalized = [p.lower() for p in patterns if p]
    if not normalized:
        return []
    
    matching_docs = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        
        # Recherche flexible : au moins un terme doit correspondre
        matches_count = sum(1 for term in normalized if term in name)
        if matches_count == 0:
            continue
        
        stat = path.stat()
        if max_age_days is not None:
            age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
            if age > dt.timedelta(days=max_age_days):
                continue
        matching_docs.append((path, stat.st_mtime, matches_count))
    
    # Trie par nombre de correspondances (plus de correspondances d'abord), puis par date (plus récent d'abord)
    matching_docs.sort(key=lambda x: (x[2], x[1]), reverse=True)
    return [doc[0] for doc in matching_docs]


def copy_if_found(source: Path, destination_dir: Path) -> Path:
    """Copie un fichier dans le répertoire de destination."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    target = destination_dir / source.name
    shutil.copy2(source, target)
    return target


def write_markdown_table(rows: Iterable[ChecklistRow]) -> str:
    """Génère un tableau Markdown à partir des lignes."""
    header = "| Key | Label | Status | Source | Submission |\n| --- | --- | --- | --- | --- |\n"
    body_lines = []
    for row in rows:
        body_lines.append(
            f"| {row.key} | {row.label} | {row.status} | {row.source} | {row.submission_path} |"
        )
    return header + "\n".join(body_lines)


def zip_dir(folder: Path) -> bytes:
    """Crée un fichier ZIP du contenu d'un dossier."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in folder.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(folder))
    buffer.seek(0)
    return buffer.read()


def write_email_draft(
    folder: Path,
    buyer: Optional[str],
    deadline: Optional[dt.datetime],
    rows: Sequence[ChecklistRow],
    email_to: Optional[str] = None,
    ao_id: Optional[str] = None
) -> Path:
    """Génère un brouillon d'email avec indication des documents manquants."""
    subject = f"Dossier de reponse{' - ' + ao_id if ao_id else ''}"
    
    missing_docs = [row for row in rows if row.status == "MISSING"]
    ok_docs = [row for row in rows if row.status == "OK"]
    draft_docs = [row for row in rows if row.status == "DRAFT"]
    
    lines = [
        f"À: {email_to if email_to else '[EMAIL À COMPLÉTER]'}",
        f"Sujet: {subject}",
        "",
        f"Bonjour {buyer or 'Madame, Monsieur'},",
        "",
        "Veuillez trouver ci-joint notre dossier de reponse à votre appel d'offre.",
        "",
    ]
    
    if ok_docs:
        lines.append("Les pieces suivantes sont incluses :")
        for row in ok_docs:
            lines.append(f"- ✅ {row.label}")
        lines.append("")
    
    if draft_docs:
        lines.append("Les pieces suivantes sont en brouillon (à compléter) :")
        for row in draft_docs:
            lines.append(f"- 📝 {row.label}")
        lines.append("")
    
    if missing_docs:
        lines.append("⚠️ ATTENTION : Les pieces suivantes sont MANQUANTES :")
        for row in missing_docs:
            lines.append(f"- ❌ {row.label}")
        lines.append("")
        lines.append("Veuillez compléter le dossier avant l'envoi final.")
        lines.append("")
    
    if deadline:
        time_str = deadline.strftime('%H:%M') if (deadline.hour or deadline.minute) else '23:59'
        lines.extend(
            [
                f"Pour rappel, la date limite de depot est le {deadline.strftime('%d/%m/%Y')} à {time_str}.",
                "",
            ]
        )
    
    lines.extend(
        [
            "Nous restons à votre disposition pour tout complement d'information.",
            "",
            "Cordialement,",
            "",
        ]
    )
    path = folder / "email_draft.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

