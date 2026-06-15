import React, { useState } from "react";
import "./DiagnosticCard.css";

function FlowCard({ flow, onQuery, onStep }) {
  const [localInput, setLocalInput] = useState("");
  const step = flow.steps[flow.currentStep];

  const submitInput = () => {
    const val = localInput.trim();
    if (!val) return;

    const newValues = { ...flow.values, [step.inputKey]: val };

    if (step.queryFn) {
      onQuery(step.queryFn(newValues));
    } else if (step.next) {
      setLocalInput("");
      onStep(step.next, newValues);
    }
  };

  return (
    <div className="diagnostic-card">
      <div className="diagnostic-prompt">{step.prompt}</div>

      {step.type === "buttons" && (
        <div className="diagnostic-options">
          {step.options.map((opt) => (
            <button
              key={opt.label}
              className="diagnostic-option"
              onClick={() => opt.query ? onQuery(opt.query) : onStep(opt.next, flow.values)}
            >
              <span className="diagnostic-icon">{opt.icon}</span>
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      )}

      {step.type === "input" && (
        <div className="flow-input-row">
          <input
            className="flow-input"
            value={localInput}
            onChange={(e) => setLocalInput(e.target.value)}
            placeholder={step.placeholder}
            onKeyPress={(e) => {
              if (e.key === "Enter") submitInput();
            }}
            autoFocus
          />
          <button className="flow-submit" onClick={submitInput}>
            {step.next ? "Next →" : "Search"}
          </button>
        </div>
      )}
    </div>
  );
}

export default FlowCard;
