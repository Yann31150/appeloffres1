#!/usr/bin/env python3
"""Application principale Streamlit pour l'analyse de documents d'appel d'offre."""

from pathlib import Path

import streamlit as st

from pages import analyse, assemblage, export


def _init_session_state() -> None:
    """Initialise les clés de session avec des valeurs par défaut si nécessaire."""
    defaults = {
        "ao_files": [],
        "required_documents": [],
        "detected_sector": None,
        "company_docs_root": str(Path.cwd()),
        "ao_id": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _render_sidebar() -> None:
    """Affiche la barre latérale avec les informations de contexte."""
    with st.sidebar:
        st.title("📋 Analyseur AO")
        st.markdown("---")
        st.markdown(
            """
            ### 🎯 Fonctionnalités

            1. **Analyse** : Analyse automatique des documents AO
            2. **Assemblage** : Création du dossier complet
            3. **Email/Export** : Email pré-rempli et export ZIP

            ---
            """
        )

        if st.session_state.get("detected_sector"):
            st.success(
                f"**Secteur détecté** : {st.session_state['detected_sector'].capitalize()}"
            )

        if st.session_state.get("required_documents"):
            st.info(
                f"**{len(st.session_state['required_documents'])} document(s)** requis détecté(s)"
            )

        if st.session_state.get("ao_id"):
            st.info(f"**AO actuel** : {st.session_state['ao_id']}")

        if st.session_state.get("email_to"):
            st.info(f"**Email** : {st.session_state['email_to']}")


def main() -> None:
    """Point d'entrée principal de l'application Streamlit."""
    # Configuration de la page
    st.set_page_config(
        page_title="Analyseur de documents AO",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_session_state()
    _render_sidebar()

    # Création des onglets
    tab1, tab2, tab3 = st.tabs(
        ["1️⃣ Analyse", "2️⃣ Assemblage", "3️⃣ Email & Export"]
    )

    # Affichage des pages
    with tab1:
        analyse.render()

    with tab2:
        assemblage.render()

    with tab3:
        export.render()


if __name__ == "__main__":
    main()
