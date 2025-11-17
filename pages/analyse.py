"""Page d'analyse des documents d'appel d'offre."""

import streamlit as st

from extract_required_documents import extract_required_documents, detect_sector
from utils import (
    extract_email,
    extract_postal_address,
    extract_urls,
    guess_buyer,
    guess_deadline,
    load_docx_text,
    load_pdf_text,
)


def _render_intro() -> None:
    """Affiche l'en-tête et le texte d'introduction."""
    st.header("🔍 Analyse des documents d'appel d'offre")
    st.markdown(
        """
        **Uploadez un ou plusieurs documents** d'appel d'offre.

        L'application analysera automatiquement le contenu pour identifier **les documents requis** pour répondre à cet appel d'offre.

        La détection se base sur :
        - Des règles génériques (AE, RC, CCAP, CCTP, BPU, DQE, DC1, DC2, etc.)
        - La détection automatique du secteur (alimentaire, travaux, informatique)
        - Des règles spécifiques au secteur détecté
        """
    )


def _extract_texts_from_uploads(uploaded_files):
    """Extrait les textes et les données brutes depuis les fichiers uploadés."""
    all_texts = []
    files_data = []

    with st.spinner("📖 Extraction du texte des documents..."):
        for uploaded_file in uploaded_files:
            try:
                raw = uploaded_file.read()
                files_data.append((uploaded_file.name, raw))

                filename = uploaded_file.name.lower()
                if filename.endswith(".pdf"):
                    text = load_pdf_text(raw)
                elif filename.endswith(".docx"):
                    text = load_docx_text(raw)
                elif filename.endswith(".txt"):
                    text = raw.decode("utf-8", errors="ignore")
                else:
                    text = ""

                if text:
                    all_texts.append(text)
                else:
                    st.warning(
                        f"⚠️ Impossible d'extraire le texte de {uploaded_file.name}"
                    )
            except Exception as e:  # pragma: no cover - affichage utilisateur
                st.error(
                    f"❌ Erreur lors de l'extraction de {uploaded_file.name}: {e}"
                )

    return all_texts, files_data


def _detect_and_store_sector(combined_text: str) -> None:
    """Détecte le secteur et met à jour le session_state."""
    sector = detect_sector(combined_text)
    if sector:
        st.session_state["detected_sector"] = sector
        st.success(f"🏷️ **Secteur détecté** : **{sector.capitalize()}**")
        st.info(
            f"Les règles spécifiques au secteur **{sector}** ont été appliquées pour la détection des documents requis."
        )
    else:
        st.session_state["detected_sector"] = None
        st.info(
            "ℹ️ Aucun secteur spécifique détecté. Seules les règles génériques sont appliquées."
        )


def _analyze_and_store_metadata(combined_text: str, files_data):
    """Analyse les documents et enregistre les résultats dans le session_state."""
    with st.spinner("🔍 Analyse des documents pour identifier les documents requis..."):
        required_docs = extract_required_documents(combined_text, files_data)

        # Extraction des informations complémentaires
        email_to = extract_email(combined_text)
        postal_address = extract_postal_address(combined_text)
        buyer = guess_buyer(combined_text)
        deadline = guess_deadline(combined_text)
        
        # Extraction des URLs depuis les PDFs
        all_urls = []
        for filename, raw in files_data:
            # Extraire le texte de ce fichier spécifique
            if filename.lower().endswith('.pdf'):
                file_text = load_pdf_text(raw)
                urls = extract_urls(file_text, pdf_raw=raw)
                all_urls.extend(urls)
            elif filename.lower().endswith('.docx'):
                file_text = load_docx_text(raw)
                urls = extract_urls(file_text, pdf_raw=None)
                all_urls.extend(urls)
            else:
                # Pour les autres formats, utiliser le texte combiné
                urls = extract_urls(combined_text, pdf_raw=None)
                all_urls.extend(urls)
        
        # Supprimer les doublons
        unique_urls = list(dict.fromkeys(all_urls))

        # Sauvegarde dans session_state
        if email_to:
            st.session_state["email_to"] = email_to
        if postal_address:
            st.session_state["postal_address"] = postal_address
        if buyer:
            st.session_state["buyer"] = buyer
        if deadline:
            st.session_state["deadline"] = deadline.isoformat()
        if unique_urls:
            st.session_state["urls"] = unique_urls

        # Sauvegarde des fichiers uploadés et des documents requis
        st.session_state["ao_files"] = files_data
        st.session_state["required_documents"] = required_docs

    return required_docs, email_to, postal_address, buyer, deadline, unique_urls


def _display_required_documents(required_docs):
    """Affiche les documents requis regroupés par catégorie."""
    st.subheader("📋 Documents requis identifiés")

    # Grouper par catégorie
    categories = {}
    for doc in required_docs:
        cat = doc.get("category", "Autre")
        categories.setdefault(cat, []).append(doc)

    # Afficher par catégorie
    for category, docs in categories.items():
        st.markdown(f"### 📁 {category}")

        for i, doc in enumerate(docs, 1):
            label = doc.get("label", f"Document {i}")
            summary = doc.get("summary", "")
            score = doc.get("score", 0)
            source = doc.get("source_section", "")

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{label}**")
                if summary:
                    st.caption(f"{summary} (score: {score})")

            with col2:
                st.metric("Score", score)

            if source and source.strip():
                with st.expander(f"📍 Contexte de détection - {label}"):
                    preview = source[:500]
                    suffix = "..." if len(source) > 500 else ""
                    st.text(preview + suffix)

            st.divider()

    return categories


def _display_summary(
    required_docs, categories, email_to, buyer, deadline, postal_address, urls
) -> None:
    """Affiche le résumé des informations extraites et les statistiques."""
    st.subheader("📊 Informations extraites")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Email", email_to or "Non trouvé")

    with col2:
        buyer_display = (
            buyer[:30] + "..." if buyer and len(buyer) > 30 else buyer or "Non trouvé"
        )
        st.metric("Acheteur", buyer_display)

    with col3:
        if deadline:
            date_display = deadline.strftime("%d/%m/%Y")
            time_display = deadline.strftime("%H:%M")
            st.metric("Date limite", f"{date_display} à {time_display}")
        else:
            st.metric("Date limite", "Non trouvée")

    with col4:
        if postal_address:
            # Afficher un aperçu de l'adresse (tronqué si trop long)
            address_preview = postal_address[:40] + "..." if len(postal_address) > 40 else postal_address
            st.metric("Adresse postale", address_preview)
        else:
            st.metric("Adresse postale", "Non trouvée")

    with st.expander("📝 Détails des informations extraites"):
        if email_to:
            st.write(f"**Email** : {email_to}")
        if buyer:
            st.write(f"**Acheteur** : {buyer}")
        if deadline:
            date_str = deadline.strftime('%d/%m/%Y')
            time_str = deadline.strftime('%H:%M')
            st.write(f"**Date et heure limite de réception** : {date_str} à {time_str}")
        if postal_address:
            st.write(f"**Adresse postale** : {postal_address}")
        if urls:
            st.write("**URLs trouvées** :")
            for url in urls:
                st.write(f"- [{url}]({url})")

    st.divider()

    st.subheader("📈 Statistiques")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total documents", len(required_docs))

    with col2:
        st.metric("Catégories", len(categories))

    with col3:
        avg_score = (
            sum(d.get("score", 0) for d in required_docs) / len(required_docs)
            if required_docs
            else 0
        )
        st.metric("Score moyen", f"{avg_score:.1f}")


def render():
    """Affiche la page d'analyse."""
    _render_intro()

    # Upload de documents
    st.subheader("📄 Upload des documents")
    uploaded_files = st.file_uploader(
        "Sélectionnez un ou plusieurs fichiers (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("👆 Uploadez un ou plusieurs documents pour commencer l'analyse.")
        return

    st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")

    if not st.button("🔍 Analyser les documents", type="primary"):
        return

    all_texts, files_data = _extract_texts_from_uploads(uploaded_files)
    if not all_texts:
        st.error("❌ Aucun texte n'a pu être extrait des documents.")
        return

    combined_text = "\n\n".join(all_texts)

    _detect_and_store_sector(combined_text)

    (
        required_docs,
        email_to,
        postal_address,
        buyer,
        deadline,
        urls,
    ) = _analyze_and_store_metadata(combined_text, files_data)

    if not required_docs:
        st.warning("⚠️ Aucun document requis trouvé dans les documents analysés.")
        st.info(
            "💡 Vérifiez que les documents contiennent bien des références aux documents standards (AE, RC, CCAP, CCTP, etc.)"
        )
        return

    st.success(f"✅ **{len(required_docs)} document(s) requis** identifié(s)")
    st.divider()

    categories = _display_required_documents(required_docs)
    _display_summary(required_docs, categories, email_to, buyer, deadline, postal_address, urls)
