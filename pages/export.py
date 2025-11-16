"""Page d'export et email."""

import datetime as dt
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from utils import zip_dir


def render():
    """Affiche la page d'export."""
    st.header("📧 Email et Export")
    
    if "ao_folder" not in st.session_state:
        st.info("ℹ️ Assemblez d'abord le dossier dans l'onglet 'Assemblage'.")
        return
    
    ao_folder = Path(st.session_state["ao_folder"])
    
    # Récupération des informations
    email_to = st.session_state.get("email_to", "")
    buyer = st.session_state.get("buyer", "")
    deadline_str = st.session_state.get("deadline")
    deadline = None
    if deadline_str:
        try:
            deadline = dt.datetime.fromisoformat(deadline_str)
        except Exception:
            pass
    
    # Récupération de la checklist
    checklist_rows = st.session_state.get("checklist_rows", [])
    
    # Vérification des documents manquants
    missing_docs = [row for row in checklist_rows if row.get("status") == "MISSING"]
    ok_docs = [row for row in checklist_rows if row.get("status") == "OK"]
    
    # Section Email
    st.subheader("📧 Brouillon d'email")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Champ email (éditable)
        email_recipient = st.text_input(
            "À :",
            value=email_to,
            help="Adresse email de destination pour l'envoi du dossier (modifiable)"
        )
        
        if email_recipient != email_to:
            st.session_state["email_to"] = email_recipient
    
    with col2:
        if deadline:
            st.metric("Date limite", deadline.strftime("%d/%m/%Y"))
        if missing_docs:
            st.error(f"⚠️ {len(missing_docs)} document(s) manquant(s)")
        else:
            st.success(f"✅ {len(ok_docs)} document(s) prêt(s)")
    
    # Affichage et édition du brouillon d'email
    email_draft = ao_folder / "email_draft.txt"
    if email_draft.exists():
        email_content = email_draft.read_text(encoding="utf-8")
        
        # Édition du contenu de l'email
        edited_email = st.text_area(
            "Contenu de l'email",
            value=email_content,
            height=400,
            help="Vous pouvez modifier le contenu de l'email avant de l'envoyer."
        )
        
        if edited_email != email_content:
            email_draft.write_text(edited_email, encoding="utf-8")
            st.success("✅ Email mis à jour")
        
        # Alerte si documents manquants
        if missing_docs:
            st.warning(f"⚠️ **ATTENTION** : {len(missing_docs)} document(s) manquant(s) dans le dossier :")
            for row in missing_docs:
                st.write(f"- ❌ {row.get('label', 'Document inconnu')}")
            st.info("💡 Complétez le dossier dans l'onglet 'Assemblage' avant l'envoi final.")
        
        # Liste des documents intégrés dans le dossier
        submission_dir = ao_folder / "submission"
        if submission_dir.exists():
            st.subheader("📋 Documents intégrés dans le dossier")
            
            files = list(submission_dir.rglob("*"))
            files = [f for f in files if f.is_file() and f.name != "checklist.xlsx" and f.name != "checklist.csv"]
            
            if files:
                st.info(f"**{len(files)} document(s)** prêt(s) pour l'envoi :")
                for file in files:
                    size = file.stat().st_size
                    size_str = f"{size / 1024:.1f} Ko" if size < 1024 * 1024 else f"{size / (1024*1024):.1f} Mo"
                    st.write(f"- ✅ {file.name} ({size_str})")
            
            # Affichage de la checklist
            if checklist_rows:
                st.subheader("📝 Checklist des documents")
                try:
                    import pandas as pd
                    df = pd.DataFrame(checklist_rows)
                    st.dataframe(df[['label', 'status']], use_container_width=True, hide_index=True)
                except Exception:
                    st.table(checklist_rows)
        
        # Boutons d'action pour l'email
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copier l'email", use_container_width=True):
                st.write("📋 Email copié dans le presse-papier (copiez manuellement)")
                st.code(edited_email, language=None)
        
        with col2:
            if email_recipient:
                mailto_link = f"mailto:{email_recipient}?subject={quote('Dossier de réponse AO')}"
                st.markdown(f'<a href="{mailto_link}" style="text-decoration: none;"><button style="width: 100%; padding: 0.5rem; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">📨 Ouvrir dans Outlook/Gmail</button></a>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ Indiquez une adresse email")
        
        with col3:
            st.download_button(
                "💾 Télécharger l'email",
                data=edited_email,
                file_name=f"email_{ao_folder.name}.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.warning("⚠️ Le brouillon d'email n'existe pas encore. Assemblez le dossier d'abord.")
    
    st.divider()
    
    # Section Export
    st.subheader("📦 Export du dossier")
    
    submission_dir = ao_folder / "submission"
    if submission_dir.exists():
        # Affichage des fichiers
        st.info(f"📁 Dossier de soumission : {submission_dir}")
        
        files = list(submission_dir.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        if files:
            st.write(f"**{len(files)} fichier(s) dans le dossier :**")
            for file in files:
                size = file.stat().st_size
                size_str = f"{size / 1024:.1f} Ko" if size < 1024 * 1024 else f"{size / (1024*1024):.1f} Mo"
                st.write(f"- {file.name} ({size_str})")
        
        # Bouton de téléchargement ZIP
        zipped = zip_dir(submission_dir)
        st.download_button(
            label="📦 Télécharger le dossier submission (ZIP)",
            data=zipped,
            file_name=f"{ao_folder.name}_submission.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )
        
        st.info("💡 **Pour envoyer** : Utilisez le lien 'Ouvrir dans Outlook/Gmail' ci-dessus pour créer un email avec le dossier ZIP en pièce jointe.")
    else:
        st.warning("⚠️ Le dossier de soumission n'existe pas encore.")
    
    st.divider()
    
    # Informations additionnelles
    st.caption("ℹ️ **Rappel** : Le dépôt sur la plateforme officielle reste manuel (signature électronique, etc.).")
    
    # Métadonnées du dossier
    meta_file = ao_folder / "meta.json"
    if meta_file.exists():
        with st.expander("📋 Métadonnées du dossier"):
            try:
                import json
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                st.json(meta)
            except Exception:
                st.text(meta_file.read_text(encoding="utf-8"))


