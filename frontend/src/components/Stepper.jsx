import React from "react";

export function Stepper({ steps, activeStep, onChange }) {
  return (
    <nav className="stepper" aria-label="Étapes du processus">
      {steps.map((label, index) => {
        const isActive = index === activeStep;
        const isDone = index < activeStep;

        return (
          <button
            key={label}
            type="button"
            className={[
              "stepper-item",
              isActive && "stepper-item--active",
              isDone && "stepper-item--done"
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onChange(index)}
          >
            <span className="stepper-index">{index + 1}</span>
            <span className="stepper-label">{label}</span>
          </button>
        );
      })}
    </nav>
  );
}





