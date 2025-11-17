import React, { useState, useEffect } from "react";

const API_URL = "http://localhost:8000/analyze";
const API_HEALTH_URL = "http://localhost:8000/health";

export function AnalyseStep() {
  // États simples (sans typage TypeScript car on est en JSX)
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [apiStatus, setApiStatus] = useState("checking"); // "checking", "online", "offline"

  // Vérifier la santé de l'API au chargement du composant
  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // Timeout de 3 secondes
        
        const response = await fetch(API_HEALTH_URL, {
          method: "GET",
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          setApiStatus("online");
        } else {
          setApiStatus("offline");
        }
      } catch (e) {
        setApiStatus("offline");
      }
    };

    checkApiHealth();
    // Vérifier toutes les 10 secondes si l'API est toujours disponible
    const interval = setInterval(checkApiHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleFilesChange = (event) => {
    const selected = event.target.files;
    if (!selected) return;
    setFiles(Array.from(selected));
    setResult(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!files.length) {
      setError("Ajoutez au moins un document avant de lancer l'analyse.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));

      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!data.success) {
        setError(data.message || "Erreur lors de l'analyse des documents.");
        setResult(null);
        try {
          window.localStorage.removeItem("ao-last-result");
        } catch (storageError) {
          // Ignorer les erreurs de stockage (mode navigation privée, etc.)
        }
      } else {
        setResult(data);
        try {
          window.localStorage.setItem("ao-last-result", JSON.stringify(data));
        } catch (storageError) {
          // Ignorer les erreurs de stockage (quota dépassé, etc.)
        }
      }
    } catch (e) {
      setError(
        "Impossible de joindre l'API. Vérifiez que le serveur Python (FastAPI) tourne sur http://localhost:8000."
      );
      try {
        window.localStorage.removeItem("ao-last-result");
      } catch (storageError) {
        // Ignorer
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2>1. Analyse des documents</h2>
      <p className="panel-intro">
        Importez vos documents d&apos;appel d&apos;offres (RC, CCAP, CCTP, etc.).
        La logique métier reste fournie par votre code Python, exposé ici via une API FastAPI.
      </p>

      {/* Indicateur de statut de l'API */}
      {apiStatus === "checking" && (
        <div style={{ 
          padding: "0.75rem", 
          backgroundColor: "#fef3c7", 
          border: "1px solid #fbbf24",
          borderRadius: "0.5rem",
          marginBottom: "1rem"
        }}>
          <strong>⏳ Vérification de la connexion à l'API...</strong>
        </div>
      )}
      {apiStatus === "offline" && (
        <div style={{ 
          padding: "0.75rem", 
          backgroundColor: "#fee2e2", 
          border: "1px solid #ef4444",
          borderRadius: "0.5rem",
          marginBottom: "1rem"
        }}>
          <strong>⚠️ L'API FastAPI n'est pas accessible</strong>
          <p style={{ margin: "0.5rem 0 0 0", fontSize: "0.9rem" }}>
            Assurez-vous que le serveur Python (FastAPI) tourne sur http://localhost:8000.
            <br />
            Utilisez le script <code>start.bat</code> ou <code>start.ps1</code> pour lancer automatiquement les deux serveurs.
          </p>
        </div>
      )}
      {apiStatus === "online" && (
        <div style={{ 
          padding: "0.75rem", 
          backgroundColor: "#d1fae5", 
          border: "1px solid #10b981",
          borderRadius: "0.5rem",
          marginBottom: "1rem"
        }}>
          <strong>✅ API FastAPI connectée</strong>
        </div>
      )}

      <div className="panel-grid">
        <section className="panel-card">
          <h3>Documents AO</h3>
          <p>Déposez ici les documents à analyser.</p>
          <label className="upload-dropzone">
            <input
              type="file"
              multiple
              className="visually-hidden"
              onChange={handleFilesChange}
            />
            <span>
              Glissez-déposez vos fichiers ou cliquez pour parcourir
              {files.length > 0 && ` (${files.length} fichier(s) sélectionné(s))`}
            </span>
          </label>
          <p className="hint">
            Formats recommandés : <strong>PDF</strong>, <strong>DOCX</strong>,{" "}
            <strong>TXT</strong>.
          </p>
          <button
            type="button"
            className="primary-button"
            onClick={handleAnalyze}
            disabled={loading || apiStatus !== "online"}
          >
            {loading ? "Analyse en cours..." : "Lancer l'analyse"}
          </button>
          {error && <p className="hint" style={{ color: "#b91c1c" }}>{error}</p>}
        </section>

        <section className="panel-card">
          <h3>Résultats</h3>
          {!result && !error && (
            <p className="hint">
              Les documents requis, le secteur, l&apos;email, l&apos;acheteur et la date limite
              s&apos;afficheront ici après l&apos;analyse.
            </p>
          )}
          {result && (
            <div className="analysis-result">
              <p>
                <strong>Secteur détecté :</strong>{" "}
                {result.sector ? result.sector : "Aucun secteur spécifique"}
              </p>
              <p>
                <strong>Email :</strong>{" "}
                {result.email_to || "Non trouvé"}
              </p>
              <p>
                <strong>Acheteur :</strong>{" "}
                {result.buyer || "Non trouvé"}
              </p>
              <p>
                <strong>Date limite :</strong>{" "}
                {result.deadline ? result.deadline : "Non trouvée"}
              </p>
              <h4 style={{ marginTop: "0.7rem" }}>
                Documents requis ({result.required_documents?.length || 0})
              </h4>
              <ul className="bullet-list">
                {(result.required_documents || []).map((doc) => (
                  <li key={doc.key}>
                    <strong>{doc.label}</strong> — {doc.category} (score{" "}
                    {doc.score})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
