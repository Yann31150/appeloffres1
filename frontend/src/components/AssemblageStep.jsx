import React, { useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "ao-last-result";

function normalize(value) {
  return (value || "")
    .toString()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]/g, "");
}

export function AssemblageStep({
  onFolderSelect,
  companyFiles = [],
  companyFolderInfo,
}) {
  const [requiredDocs, setRequiredDocs] = useState([]);
  const [loadingFolder, setLoadingFolder] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setRequiredDocs(parsed?.required_documents || []);
        setMessage(
          "Liste récupérée depuis l'analyse précédente. Sélectionnez votre dossier pour vérifier la complétude."
        );
      } else {
        setMessage(
          "Aucun résultat d'analyse trouvé. Retournez à l'étape 1 pour détecter les documents requis."
        );
      }
    } catch (error) {
      setMessage(
        "Impossible de lire les données de l'analyse locale. Relancez l'étape 1."
      );
    }
  }, []);

  const handleFolderChange = (event) => {
    const files = Array.from(event.target.files || []);
    setLoadingFolder(true);

    let folderName = "";
    if (files.length > 0) {
      const sample = files[0];
      const relative = sample.webkitRelativePath || sample.name;
      folderName = relative.includes("/")
        ? relative.split("/")[0]
        : sample.name;
      setMessage(
        `Dossier "${folderName}" sélectionné (${files.length} fichier(s)).`
      );
    } else {
      setMessage("Aucun dossier sélectionné.");
    }

    onFolderSelect?.(files, {
      name: folderName,
      fileCount: files.length,
      selectedAt: new Date().toISOString(),
    });

    setLoadingFolder(false);
  };

  const folderFiles = companyFiles;
  const companyRoot = companyFolderInfo?.name || "";

  const checklist = useMemo(() => {
    if (!requiredDocs.length) return [];
    const files = folderFiles.map((file) => ({
      name: file.name,
      normalized: normalize(file.name),
    }));

    return requiredDocs.map((doc) => {
      const normalizedDoc = normalize(doc.key || doc.label);
      const match = files.find((file) =>
        normalizedDoc ? file.normalized.includes(normalizedDoc) : false
      );
      return {
        ...doc,
        present: Boolean(match),
        filename: match?.name || null,
      };
    });
  }, [requiredDocs, folderFiles]);

  const presentCount = checklist.filter((doc) => doc.present).length;
  const missingCount = checklist.length - presentCount;

  const extraFiles = useMemo(() => {
    if (!folderFiles.length) return [];
    const matchedNames = new Set(
      checklist
        .filter((doc) => doc.present && doc.filename)
        .map((doc) => doc.filename)
    );
    return folderFiles
      .map((file) => file.name)
      .filter((name) => !matchedNames.has(name))
      .slice(0, 10);
  }, [folderFiles, checklist]);

  return (
    <div className="panel">
      <h2>2. Assemblage du dossier</h2>
      <p className="panel-intro">
        Sélectionnez votre dossier d&apos;entreprise pour vérifier si toutes les
        pièces demandées lors de l&apos;analyse sont présentes avant de préparer
        l&apos;envoi par email.
      </p>

      <div className="panel-grid">
        <section className="panel-card">
          <h3>Dossier d&apos;entreprise</h3>
          <p className="hint">{message}</p>
          <label className="upload-dropzone upload-dropzone--folder">
            <input
              type="file"
              webkitdirectory="true"
              directory="true"
              multiple
              className="visually-hidden"
              onChange={handleFolderChange}
            />
            <span>
              📁 {loadingFolder ? "Chargement..." : "Choisir un dossier d'entreprise"}
            </span>
          </label>
          {companyRoot && (
            <p className="hint">
              Dossier sélectionné : <strong>{companyRoot}</strong>
            </p>
          )}
          <p className="hint">
            Ce dossier correspond au champ <code>company_docs_root</code> côté
            Python. Aucun fichier n&apos;est envoyé, tout reste local dans votre
            navigateur.
          </p>
        </section>

        <section className="panel-card">
          <h3>Checklist dynamique</h3>
          {!requiredDocs.length && (
            <p className="hint">
              Lancez d&apos;abord l&apos;analyse pour générer la liste des
              documents requis.
            </p>
          )}
          {requiredDocs.length > 0 && (
            <>
              <div className="summary-cards">
                <div className="summary-card">
                  <span className="summary-label">Présents</span>
                  <strong className="summary-value">{presentCount}</strong>
                </div>
                <div className="summary-card summary-card--alert">
                  <span className="summary-label">Manquants</span>
                  <strong className="summary-value">{missingCount}</strong>
                </div>
                <div className="summary-card">
                  <span className="summary-label">Total requis</span>
                  <strong className="summary-value">{requiredDocs.length}</strong>
                </div>
              </div>

              <table className="table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Catégorie</th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {checklist.map((doc) => (
                    <tr key={doc.key}>
                      <td>
                        <strong>{doc.label}</strong>
                        <br />
                        <span className="hint">Score {doc.score}</span>
                      </td>
                      <td>{doc.category || "N/A"}</td>
                      <td>
                        {doc.present ? (
                          <span className="badge badge-ok">
                            OK{doc.filename ? ` (${doc.filename})` : ""}
                          </span>
                        ) : (
                          <span className="badge badge-missing">Manquant</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {extraFiles.length > 0 && (
                <div className="hint" style={{ marginTop: "0.75rem" }}>
                  Autres fichiers détectés dans le dossier (échantillon) :
                  <ul className="bullet-list">
                    {extraFiles.map((name) => (
                      <li key={name}>{name}</li>
                    ))}
                    {folderFiles.length > extraFiles.length && (
                      <li>…</li>
                    )}
                  </ul>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}





