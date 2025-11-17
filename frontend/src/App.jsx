import React, { useState } from "react";
import { Stepper } from "./components/Stepper.jsx";
import { AnalyseStep } from "./components/AnalyseStep.jsx";
import { AssemblageStep } from "./components/AssemblageStep.jsx";
import { ExportStep } from "./components/ExportStep.jsx";

const STEPS = ["Analyse", "Assemblage", "Email & Export"];

export default function App() {
  const [activeStep, setActiveStep] = useState(0);
  const [companyFiles, setCompanyFiles] = useState([]);
  const [companyFolderInfo, setCompanyFolderInfo] = useState(null);

  const handleFolderSelection = (files, info) => {
    setCompanyFiles(files);
    setCompanyFolderInfo(info || null);
  };

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="app-logo">AO</div>
        <div>
          <h1>Analyseur d&apos;appels d&apos;offres</h1>
          <p className="app-subtitle">
            Un parcours simple en 3 étapes pour préparer vos dossiers de réponse.
          </p>
        </div>
      </header>

      <main className="app-main">
        <aside className="app-sidebar">
          <h2 className="sidebar-title">Parcours</h2>
          <Stepper
            steps={STEPS}
            activeStep={activeStep}
            onChange={setActiveStep}
          />

          <section className="sidebar-card">
            <h3>Conseils</h3>
            <ul>
              <li>Préparez tous les documents AO avant de commencer.</li>
              <li>Suivez les étapes dans l&apos;ordre pour ne rien oublier.</li>
              <li>Gardez vos documents d&apos;entreprise dans un dossier dédié.</li>
            </ul>
          </section>
        </aside>

        <section className="app-content">
          {activeStep === 0 && <AnalyseStep />}
          {activeStep === 1 && (
            <AssemblageStep
              companyFiles={companyFiles}
              companyFolderInfo={companyFolderInfo}
              onFolderSelect={handleFolderSelection}
            />
          )}
          {activeStep === 2 && (
            <ExportStep
              companyFiles={companyFiles}
              companyFolderInfo={companyFolderInfo}
              onFolderSelect={handleFolderSelection}
            />
          )}
        </section>
      </main>

      <footer className="app-footer">
        <span>© {new Date().getFullYear()} AO Assistant</span>
        <span className="footer-separator">•</span>
        <span>Interface sobre, claire et orientée métier.</span>
      </footer>
    </div>
  );
}





