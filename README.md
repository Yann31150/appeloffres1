# Analyseur d'Appels d'Offres (AO)

Application pour analyser automatiquement les documents d'appels d'offres, extraire les documents requis et préparer les dossiers de réponse.

## 📋 Fonctionnalités

1. **Analyse** : Analyse automatique des documents AO pour détecter :
   - Le secteur d'activité
   - Les documents requis
   - L'email de contact
   - L'adresse postale
   - Le donneur d'ordre
   - La date limite de dépôt

2. **Assemblage** : Création automatique du dossier complet de réponse

3. **Email & Export** : Génération d'email pré-rempli et export ZIP du dossier

## 🛠️ Prérequis

- **Python** 3.8 ou supérieur
- **Node.js** 16 ou supérieur et npm
- **Git** (pour cloner le dépôt)

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/Yann31150/appeloffres1.git
cd appeloffres1
```

### 2. Configuration de l'environnement Python

#### Créer un environnement virtuel

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### Installer les dépendances Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuration du frontend React

```bash
cd frontend
npm install
cd ..
```

## 🚀 Utilisation

### Option 1 : Interface Streamlit (Recommandée)

L'application principale utilise Streamlit avec une interface en 3 onglets.

```bash
# Activer l'environnement virtuel (si pas déjà fait)
.\venv\Scripts\Activate.ps1  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Lancer l'application
streamlit run app.py
```

L'application sera accessible à l'adresse : `http://localhost:8501`

### Option 2 : API FastAPI + Frontend React

Pour utiliser l'interface React avec l'API FastAPI :

#### Terminal 1 : Démarrer l'API FastAPI

```bash
# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Lancer l'API
uvicorn api:app --reload --port 8000
```

L'API sera accessible à l'adresse : `http://localhost:8000`
Documentation API : `http://localhost:8000/docs`

#### Terminal 2 : Démarrer le frontend React

```bash
cd frontend
npm run dev
```

Le frontend sera accessible à l'adresse : `http://localhost:3000`

## 📁 Structure du projet

```
appeloffres1/
├── api.py                      # API FastAPI pour le frontend React
├── app.py                      # Application principale Streamlit
├── config.py                   # Configuration et constantes
├── document_rules.py           # Règles de détection des documents
├── extract_required_documents.py  # Extraction des documents requis
├── utils.py                    # Fonctions utilitaires
├── requirements.txt            # Dépendances Python
├── pages/                      # Pages Streamlit
│   ├── analyse.py
│   ├── assemblage.py
│   └── export.py
├── frontend/                   # Application React
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── AnalyseStep.jsx
│   │   │   ├── AssemblageStep.jsx
│   │   │   ├── ExportStep.jsx
│   │   │   └── Stepper.jsx
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.mjs
├── output/                     # Dossiers de sortie générés
└── temp_uploads/               # Fichiers temporaires
```

## 🔧 Configuration

### Variables d'environnement

Aucune variable d'environnement n'est requise pour le moment. La configuration est gérée dans `config.py`.

### Répertoires

- **output/** : Contient les dossiers générés pour chaque appel d'offres
- **temp_uploads/** : Fichiers temporaires uploadés

## 📝 Utilisation de l'application

### Étape 1 : Analyse

1. Uploadez les documents de l'appel d'offres (PDF, DOCX)
2. L'application analyse automatiquement les documents
3. Les informations extraites sont affichées :
   - Secteur détecté
   - Liste des documents requis
   - Email de contact
   - Adresse postale
   - Date limite

### Étape 2 : Assemblage

1. Sélectionnez les documents de votre entreprise à inclure
2. L'application crée automatiquement le dossier structuré
3. Les documents sont organisés dans le répertoire `output/`

### Étape 3 : Email & Export

1. Un brouillon d'email est généré automatiquement
2. Exportez le dossier complet en ZIP
3. Envoyez votre réponse à l'appel d'offres

## 🐛 Dépannage

### Problème : Module non trouvé

```bash
# Vérifiez que l'environnement virtuel est activé
# Réinstallez les dépendances
pip install -r requirements.txt
```

### Problème : Port déjà utilisé

```bash
# Pour Streamlit, changez le port :
streamlit run app.py --server.port 8502

# Pour FastAPI, changez le port :
uvicorn api:app --reload --port 8001

# Pour React, modifiez vite.config.mjs
```

### Problème : Erreur CORS (API + Frontend)

Si vous utilisez l'API FastAPI avec le frontend React, assurez-vous que :
- L'API tourne sur le port 8000
- Le frontend tourne sur le port 3000
- Le CORS est configuré dans `api.py` (déjà fait par défaut)

## 📚 Dépendances principales

### Backend Python
- **Streamlit** : Interface utilisateur principale
- **FastAPI** : API REST pour le frontend React
- **PyMuPDF / pdfplumber / pypdf** : Extraction de texte depuis PDF
- **python-docx** : Traitement des documents Word

### Frontend
- **React** 18.2.0
- **Vite** 5.0.0

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Ce projet est sous licence libre.

## 👤 Auteur

Yann31150 - [GitHub](https://github.com/Yann31150)

---

**Note** : Ce projet est en développement actif. Certaines fonctionnalités peuvent évoluer.

