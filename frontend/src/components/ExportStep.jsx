import React from "react";

export function ExportStep() {
  return (
    <div className="panel">
      <h2>3. Email &amp; export</h2>
      <p className="panel-intro">
        Prévisualisez votre email, vérifiez les pièces jointes et prévoyez
        l&apos;export ZIP pour la plateforme de dépôt.
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
          />

          <label className="field-label" htmlFor="email-body">
            Contenu
          </label>
          <textarea
            id="email-body"
            className="text-area"
            rows={10}
            defaultValue={
              "Bonjour Madame, Monsieur,\n\nVeuillez trouver ci-joint notre dossier de réponse à votre appel d'offres.\n\nCordialement,"
            }
          />

          <div className="button-row">
            <button type="button" className="secondary-button" disabled>
              Copier l&apos;email (maquette)
            </button>
            <button type="button" className="primary-button" disabled>
              Ouvrir dans Outlook/Gmail (maquette)
            </button>
          </div>
          <p className="hint">
            Dans votre application actuelle, ce contenu est généré dans le
            fichier <code>email_draft.txt</code>.
          </p>
        </section>

        <section className="panel-card">
          <h3>Export du dossier</h3>
          <p>
            Ici vous pourrez déclencher la génération d&apos;un ZIP contenant le
            dossier <code>submission</code> produit par votre back-end.
          </p>
          <button type="button" className="primary-button" disabled>
            Télécharger le ZIP (maquette)
          </button>
          <ul className="bullet-list">
            <li>Vérifiez la complétude des pièces avant l&apos;envoi.</li>
            <li>Conservez le ZIP comme preuve de votre dépôt.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}



