import React, { useEffect, useMemo, useState } from "react";
import JSZip from "jszip";

const STORAGE_KEY = "ao-last-result";
const DEFAULT_EMAIL_BODY =
  "Bonjour Madame, Monsieur,\n\nVeuillez trouver ci-joint notre dossier de réponse à votre appel d'offres.\n\nCordialement,";

const formatSize = (bytes) => {
  if (!Number.isFinite(bytes)) return "0 o";
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
};

export function ExportStep({ companyFiles = [], companyFolderInfo, onFolderSelect }) {
  const [emailTo, setEmailTo] = useState("");
  const [emailBody, setEmailBody] = useState(DEFAULT_EMAIL_BODY);
  const [copyStatus, setCopyStatus] = useState("");
  const [zipStatus, setZipStatus] = useState({ loading: false, message: "", error: "" });

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed?.email_to) {
          setEmailTo(parsed.email_to);
        }
        if (parsed?.buyer || parsed?.detected_sector) {
          setEmailBody(
            `Bonjour ${parsed?.buyer || "Madame, Monsieur"},\n\nSuite à votre appel d'offres${
              parsed?.detected_sector ? ` (${parsed.detected_sector})` : ""
            }, vous trouverez ci-joint notre dossier complet de réponse.\n\nCordialement,`
          );
        }
      }
    } catch (error) {
      // Ignore
    }
  }, []);

  const files = companyFiles;
  const folderName = companyFolderInfo?.name || "";
  const totalSize = useMemo(
    () => files.reduce((sum, file) => sum + file.size, 0),
    [files]
  );
  const filePreview = useMemo(
    () => files.slice(0, 8).map((file) => ({ name: file.name, size: formatSize(file.size) })),
    [files]
  );

  const handleCopyEmail = async () => {
    try {
      await navigator.clipboard.writeText(emailBody);
      setCopyStatus("✅ Email copié dans le presse-papiers");
      setTimeout(() => setCopyStatus(""), 3000);
    } catch (error) {
      setCopyStatus("⚠️ Impossible de copier automatiquement. Copiez manuellement.");
    }
  };

  const handleFolderChange = (event) => {
    const selected = Array.from(event.target.files || []);
    if (!selected.length) {
      onFolderSelect?.([], null);
      return;
    }
    const sample = selected[0];
    const relative = sample.webkitRelativePath || sample.name;
    const selectedFolder = relative.includes("/") ? relative.split("/")[0] : sample.name;
    onFolderSelect?.(selected, {
      name: selectedFolder,
      fileCount: selected.length,
      selectedAt: new Date().toISOString(),
    });
  };

  const handleZipDownload = async () => {
    if (!files.length) {
      setZipStatus({
        loading: false,
        message: "",
        error: "Sélectionnez d'abord un dossier contenant vos documents.",
      });
      return;
    }

    setZipStatus({ loading: true, message: "", error: "" });

    try {
      const zip = new JSZip();

      files.forEach((file) => {
        const relativePath =
          file.webkitRelativePath ||
          (folderName ? `${folderName}/${file.name}` : file.name);
        zip.file(relativePath, file);
      });

      const blob = await zip.generateAsync({ type: "blob" });
      const downloadName = folderName
        ? `${folderName}_submission.zip`
        : "dossier_submission.zip";
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = downloadName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 4000);

      setZipStatus({
        loading: false,
        message: `ZIP téléchargé (${formatSize(blob.size)})`,
        error: "",
      });
    } catch (error) {
      console.error(error);
      setZipStatus({
        loading: false,
        message: "",
        error: "Impossible de générer le ZIP. Réessayez ou sélectionnez à nouveau le dossier.",
      });
    }
  };

  const mailtoLink =
    emailTo.trim().length > 0
      ? `mailto:${encodeURIComponent(emailTo)}?subject=${encodeURIComponent(
          "Dossier de réponse à votre appel d'offres"
        )}`
      : "#";

  const folderHint = companyFolderInfo
    ? `Dossier "${companyFolderInfo.name}" (${companyFolderInfo.fileCount || files.length} fichier(s))`
    : "Sélectionnez le dossier 'submission' généré lors de l'étape Assemblage.";

  return (
    <div className="panel">
      <h2>3. Email &amp; export</h2>
      <p className="panel-intro">
        Prévisualisez votre email, vérifiez les pièces jointes et générez un ZIP prêt pour la plateforme de dépôt.
      </p>

      <div className="panel-grid panel-grid--two">
        <section className="panel-card">
          <h3>Brouillon d&apos;email</h3>
          <label className="field-label" htmlFor="email-to">
            Destinataire
          </label>
          <input
            id="email-to"
            type="email"
            className="text-input"
            placeholder="exemple@collectivite.fr"
            value={emailTo}
            onChange={(event) => setEmailTo(event.target.value)}
          />

          <label className="field-label" htmlFor="email-body">
            Contenu
          </label>
          <textarea
            id="email-body"
            className="text-area"
            rows={10}
            value={emailBody}
            onChange={(event) => setEmailBody(event.target.value)}
          />

          <div className="button-row">
            <button type="button" className="secondary-button" onClick={handleCopyEmail}>
              Copier l&apos;email
            </button>
            <a
              href={mailtoLink}
              style={{ textDecoration: "none", flex: 1 }}
              onClick={(event) => {
                if (mailtoLink === "#") {
                  event.preventDefault();
                }
              }}
            >
              <button
                type="button"
                className="primary-button"
                style={{ width: "100%" }}
                disabled={!emailTo}
              >
                Ouvrir dans Outlook/Gmail
              </button>
            </a>
          </div>
          {copyStatus && <p className="hint">{copyStatus}</p>}
          <p className="hint">
            Ce brouillon est une base : ajustez l&apos;objet, signez et joignez le ZIP généré ci-dessous.
          </p>
        </section>

        <section className="panel-card">
          <h3>Export du dossier</h3>
          <p className="hint">{folderHint}</p>
          <label className="upload-dropzone upload-dropzone--folder">
            <input
              type="file"
              webkitdirectory="true"
              directory="true"
              multiple
              className="visually-hidden"
              onChange={handleFolderChange}
            />
            <span>📁 Sélectionner le dossier &quot;submission&quot;</span>
          </label>

          {files.length > 0 ? (
            <>
              <div className="summary-cards" style={{ marginTop: "1rem" }}>
                <div className="summary-card">
                  <span className="summary-label">Fichiers</span>
                  <strong className="summary-value">{files.length}</strong>
                </div>
                <div className="summary-card">
                  <span className="summary-label">Poids total</span>
                  <strong className="summary-value">{formatSize(totalSize)}</strong>
                </div>
              </div>

              <ul className="bullet-list" style={{ marginTop: "0.75rem" }}>
                {filePreview.map((file) => (
                  <li key={file.name}>
                    {file.name} <span className="hint">({file.size})</span>
                  </li>
                ))}
                {files.length > filePreview.length && <li>…</li>}
              </ul>

              <button
                type="button"
                className="primary-button"
                style={{ marginTop: "1rem" }}
                onClick={handleZipDownload}
                disabled={zipStatus.loading}
              >
                {zipStatus.loading ? "Compression en cours..." : "Télécharger le ZIP"}
              </button>
            </>
          ) : (
            <p className="hint" style={{ marginTop: "1rem" }}>
              Aucun fichier sélectionné pour le moment.
            </p>
          )}

          {zipStatus.message && (
            <p className="hint" style={{ color: "#047857", marginTop: "0.5rem" }}>
              {zipStatus.message}
            </p>
          )}
          {zipStatus.error && (
            <p className="hint" style={{ color: "#b91c1c", marginTop: "0.5rem" }}>
              {zipStatus.error}
            </p>
          )}
          <p className="hint" style={{ marginTop: "0.75rem" }}>
            Aucun fichier n&apos;est envoyé sur un serveur : la compression se fait localement dans votre navigateur.
          </p>
        </section>
      </div>
    </div>
  );
}





