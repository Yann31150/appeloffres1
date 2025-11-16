import React from "react";

export function AssemblageStep() {
  return (
    <div className="panel">
      <h2>2. Assemblage du dossier</h2>
      <p className="panel-intro">
        Visualisez les documents requis et indiquez où se trouvent vos pièces
        d&apos;entreprise (assurances, DC1, DC2, attestations…).
      </p>

      <div className="panel-grid">
        <section className="panel-card">
          <h3>Dossier d&apos;entreprise</h3>
          <label className="field-label" htmlFor="company-root">
            Dossier racine des documents d&apos;entreprise
          </label>
          <input
            id="company-root"
            type="text"
            className="text-input"
            placeholder="Ex : D:\Documents\Entreprise\AO"
          />
          <p className="hint">
            Dans votre application Python, ce champ correspond à{" "}
            <code>company_docs_root</code>.
          </p>
        </section>

        <section className="panel-card">
          <h3>Checklist (aperçu maquette)</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Document</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Acte d&apos;engagement (AE)</td>
                <td>
                  <span className="badge badge-ok">OK</span>
                </td>
              </tr>
              <tr>
                <td>Règlement de consultation (RC)</td>
                <td>
                  <span className="badge badge-ok">OK</span>
                </td>
              </tr>
              <tr>
                <td>Déclaration sur l&apos;honneur</td>
                <td>
                  <span className="badge badge-missing">Manquant</span>
                </td>
              </tr>
            </tbody>
          </table>
          <p className="hint">
            Cette table reflète les données générées en Python (classe{" "}
            <code>ChecklistRow</code>) et exportées en Excel/Markdown.
          </p>
        </section>
      </div>
    </div>
  );
}



