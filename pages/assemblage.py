"""Page d'assemblage du dossier."""

import datetime as dt
import json
from pathlib import Path
from typing import List

import streamlit as st

from config import OUTPUT_ROOT
from utils import (
    ChecklistRow,
    copy_if_found,
    find_all_matching_docs,
    find_best_doc,
    load_pdf_text,
    load_docx_text,
    now_utc,
    slugify,
    write_email_draft,
    write_markdown_table,
)

try:
    import pandas as pd  # type: ignore
except ImportError:
    pd = None


def _build_search_patterns(label: str, doc: dict) -> List[str]:
    """Construit la liste des patterns de recherche à partir du label et des mots-clés."""
    patterns: List[str] = []

    # Ajoute les mots significatifs du label
    label_words = [w.lower() for w in label.split() if len(w) > 2]
    patterns.extend(label_words[:3])  # Prend les 3 premiers mots significatifs

    # Ajoute les mots-clés éventuels du document
    for kw in doc.get("keywords", []):
        if isinstance(kw, str) and len(kw) > 2:
            patterns.append(kw.lower())

    return patterns


def render():
    """Affiche la page d'assemblage."""
    st.header("📦 Assemblage du dossier")
    
    if not st.session_state.get("ao_files"):
        st.info("ℹ️ Analysez d'abord les documents dans l'onglet 'Analyse'.")
        return
    
    if not st.session_state.get("required_documents"):
        st.warning("⚠️ Aucune liste de documents disponible. Analysez d'abord les documents dans l'onglet 'Analyse'.")
        return
    
    required_docs = st.session_state["required_documents"]
    
    # Configuration du dossier des documents d'entreprise
    st.subheader("📁 Configuration du dossier de recherche")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        company_docs_root = st.text_input(
            "Dossier contenant vos documents d'entreprise",
            value=st.session_state.get("company_docs_root", str(Path.cwd())),
            help="Indiquez le chemin du dossier où se trouvent vos documents d'entreprise. L'application cherchera automatiquement les documents correspondants dans ce dossier et ses sous-dossiers."
        )
        st.session_state["company_docs_root"] = company_docs_root
        company_docs_path = Path(company_docs_root)
        
        if not company_docs_path.exists():
            st.warning(f"⚠️ Le dossier '{company_docs_root}' n'existe pas.")
        else:
            st.success(f"✅ Dossier trouvé : {company_docs_root}")
            # Affiche le nombre de fichiers dans le dossier
            try:
                file_count = sum(1 for _ in company_docs_path.rglob("*") if _.is_file())
                st.caption(f"📄 {file_count} fichier(s) trouvé(s) dans le dossier et ses sous-dossiers")
            except Exception:
                pass
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Espacement
        if st.button("🔄 Rechercher", help="Relance la recherche de tous les documents"):
            st.rerun()
    
    st.divider()
    
    if "manual_doc_selections" not in st.session_state:
        st.session_state["manual_doc_selections"] = {}
    
    st.info(f"📋 **{len(required_docs)} document(s)** à intégrer dans le dossier de soumission")
    
    st.divider()
    
    # Liste des documents avec sélection
    document_selections = {}
    
    for idx, doc in enumerate(required_docs, 1):
        key = doc.get("key", f"doc_{idx}")
        label = doc.get("label", f"Document {idx}")
        category = doc.get("category", "Autre")
        
        st.subheader(f"{idx}. {label}")
        st.caption(f"Catégorie : {category}")
        
        # Création de patterns à partir du label et des keywords
        patterns = _build_search_patterns(label, doc)
        
        # Recherche automatique de TOUS les documents correspondants
        matching_docs = []
        if company_docs_path.exists():
            matching_docs = find_all_matching_docs(company_docs_path, patterns, max_age_days=None)
        
        # Document sélectionné (manuel ou automatique)
        current_selection = st.session_state["manual_doc_selections"].get(key)
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Affichage des résultats de recherche
            if matching_docs:
                if len(matching_docs) == 1:
                    # Un seul document trouvé - sélection automatique
                    auto_selected = str(matching_docs[0])
                    if not current_selection:
                        st.session_state["manual_doc_selections"][key] = auto_selected
                        current_selection = auto_selected
                    st.success(f"✅ 1 document trouvé : `{Path(matching_docs[0]).name}`")
                    st.caption(f"📍 Chemin : {matching_docs[0]}")
                else:
                    # Plusieurs documents trouvés - permettre le choix
                    st.info(f"🔍 {len(matching_docs)} document(s) correspondant(s) trouvé(s)")
                    
                    # Liste des documents trouvés avec sélection
                    doc_options = [f"{Path(doc).name} ({doc})" for doc in matching_docs]
                    selected_index = 0
                    
                    # Trouve l'index du document actuellement sélectionné
                    if current_selection:
                        try:
                            current_path = Path(current_selection)
                            for i, doc in enumerate(matching_docs):
                                if doc == current_path:
                                    selected_index = i
                                    break
                        except Exception:
                            pass
                    
                    # Sélecteur de document
                    selected_doc_str = st.selectbox(
                        f"Choisir le document pour {label}",
                        options=doc_options,
                        index=selected_index,
                        key=f"select_{key}",
                        help="Sélectionnez le document approprié parmi les options trouvées"
                    )
                    
                    # Extrait le chemin du document sélectionné
                    selected_doc_path = matching_docs[doc_options.index(selected_doc_str)]
                    st.session_state["manual_doc_selections"][key] = str(selected_doc_path)
                    current_selection = str(selected_doc_path)
                    
                    st.caption(f"📍 Document sélectionné : {selected_doc_path}")
                    
                    # Affiche les autres options
                    with st.expander(f"📋 Voir les {len(matching_docs)} options trouvées"):
                        for i, doc in enumerate(matching_docs, 1):
                            size = doc.stat().st_size
                            size_str = f"{size / 1024:.1f} Ko" if size < 1024 * 1024 else f"{size / (1024*1024):.1f} Mo"
                            mod_time = dt.datetime.fromtimestamp(doc.stat().st_mtime)
                            is_selected = "✅" if str(doc) == current_selection else "  "
                            st.write(f"{is_selected} {i}. **{doc.name}** - {size_str} - Modifié le {mod_time.strftime('%d/%m/%Y %H:%M')}")
                            st.caption(f"   {doc}")
            else:
                st.warning("❌ Aucun document correspondant trouvé dans le dossier")
                if current_selection and Path(current_selection).exists():
                    st.info(f"📄 Document sélectionné manuellement : `{Path(current_selection).name}`")
                    st.caption(f"📍 Chemin : {current_selection}")
        
        with col2:
            # Sélection manuelle de fichier (toujours disponible)
            uploaded_file = st.file_uploader(
                f"Ou sélectionner un fichier",
                type=None,
                key=f"upload_{key}",
                help="Sélectionnez un fichier depuis votre ordinateur si aucun document correspondant n'a été trouvé"
            )
            
            if uploaded_file:
                # Sauvegarde temporaire du fichier uploadé
                temp_dir = Path.cwd() / "temp_uploads"
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / uploaded_file.name
                temp_path.write_bytes(uploaded_file.getvalue())
                st.session_state["manual_doc_selections"][key] = str(temp_path)
                st.success(f"✅ {uploaded_file.name} sélectionné")
                st.rerun()
            
            # Bouton pour réinitialiser la sélection
            if current_selection:
                if st.button("🔄 Réinitialiser", key=f"reset_{key}"):
                    st.session_state["manual_doc_selections"].pop(key, None)
                    st.rerun()
        
        # Utilise le document sélectionné
        final_doc = current_selection if current_selection and Path(current_selection).exists() else None
        
        document_selections[key] = {
            'doc': final_doc,
            'label': label,
            'item': doc,
        }
        
        st.divider()
    
    st.divider()
    
    # Informations du dossier
    ao_id_value = st.text_input(
        "Identifiant de l'appel d'offre",
        value=st.session_state.get("ao_id", ""),
        help="Ex: AO-2024-001"
    )
    st.session_state["ao_id"] = ao_id_value
    
    # Bouton d'assemblage
    if st.button("📦 Assembler le dossier", type="primary", use_container_width=True):
        ao_folder = OUTPUT_ROOT / f"{slugify(ao_id_value or 'ao')}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ao_folder.mkdir(parents=True, exist_ok=True)

        # Sauvegarde des fichiers AO source
        (ao_folder / "source").mkdir(exist_ok=True)
        for filename, raw in st.session_state["ao_files"]:
            (ao_folder / "source" / filename).write_bytes(raw)

        # Extraction des métadonnées
        texts = []
        for filename, raw in st.session_state["ao_files"]:
            if filename.lower().endswith('.pdf'):
                texts.append(load_pdf_text(raw))
            elif filename.lower().endswith('.docx'):
                texts.append(load_docx_text(raw))
            else:
                texts.append(raw.decode('utf-8', errors='ignore'))
        combined_text = "\n".join(texts)
        
        from utils import guess_buyer, guess_deadline
        buyer = guess_buyer(combined_text) or st.session_state.get("buyer")
        deadline = guess_deadline(combined_text) or (
            dt.datetime.fromisoformat(st.session_state["deadline"]) 
            if st.session_state.get("deadline") else None
        )

        # Copie des documents dans le dossier de soumission
        submission_dir = ao_folder / "submission"
        submission_dir.mkdir(exist_ok=True)
        rows: List[ChecklistRow] = []

        for sel_key, selection in document_selections.items():
            item = selection['item']
            label = selection['label']
            found_doc = selection['doc']
            # Utilise la clé de l'item si disponible, sinon utilise sel_key
            if isinstance(item, dict):
                key = item.get("key", sel_key)
            else:
                key = sel_key

            if found_doc and Path(found_doc).exists():
                submission_path = str(copy_if_found(Path(found_doc), submission_dir))
                status = "OK"
            else:
                submission_path = ""
                status = "MISSING"

            rows.append(ChecklistRow(
                key=key,
                label=label,
                status=status,
                source=str(found_doc) if found_doc else "",
                submission_path=submission_path,
                max_age_days="",
            ))

        # Génération des fichiers
        if pd:
            pd.DataFrame([row.__dict__ for row in rows]).to_excel(submission_dir / "checklist.xlsx", index=False)
        else:
            (submission_dir / "checklist.csv").write_text(
                "key,label,status,source,submission_path,max_age_days\n" + "\n".join(
                    f"{row.key},{row.label},{row.status},{row.source},{row.submission_path},{row.max_age_days}"
                    for row in rows
                ), encoding="utf-8"
            )

        (ao_folder / "README.md").write_text(write_markdown_table(rows), encoding="utf-8")
        (ao_folder / "meta.json").write_text(json.dumps({
            "ao_id": ao_id_value,
            "buyer": buyer,
            "deadline": deadline.isoformat() if isinstance(deadline, dt.datetime) else None,
            "created_at": now_utc().isoformat(),
            "sector": st.session_state.get("detected_sector"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        # Génération du brouillon d'email
        write_email_draft(
            ao_folder, buyer, deadline, rows,
            st.session_state.get("email_to"), ao_id_value
        )

        st.session_state["ao_folder"] = str(ao_folder)
        st.session_state["checklist_rows"] = [row.__dict__ for row in rows]
        
        if pd:
            st.dataframe(pd.DataFrame([row.__dict__ for row in rows]), use_container_width=True)
        else:
            st.table([row.__dict__ for row in rows])
        
        st.success(f"✅ Dossier assemblé : {ao_folder}")
        st.info("💡 Passez à l'onglet 'Email & Export' pour voir le brouillon d'email et exporter le dossier.")

