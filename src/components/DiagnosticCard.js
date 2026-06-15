import React from "react";
import "./DiagnosticCard.css";

const FLOW = {
  start: {
    prompt: "What type of appliance are you having trouble with?",
    options: [
      { label: "Refrigerator", icon: "🧊", next: "refrigerator" },
      { label: "Dishwasher", icon: "🍽️", next: "dishwasher" },
    ],
  },
  refrigerator: {
    prompt: "What's the issue with your refrigerator?",
    options: [
      { label: "Not cooling", icon: "🌡️", query: "My refrigerator is not cooling or staying cold" },
      { label: "Ice maker not working", icon: "🧊", query: "The ice maker on my refrigerator is not working" },
      { label: "Leaking water", icon: "💧", query: "My refrigerator is leaking water" },
      { label: "Making noise", icon: "🔊", query: "My refrigerator is making loud or unusual noises" },
      { label: "Door not sealing", icon: "🚪", query: "My refrigerator door is not sealing or closing properly" },
    ],
  },
  dishwasher: {
    prompt: "What's the issue with your dishwasher?",
    options: [
      { label: "Not draining", icon: "💧", query: "My dishwasher is not draining, water is pooling at the bottom" },
      { label: "Dishes not clean", icon: "🍽️", query: "My dishwasher is not cleaning dishes properly" },
      { label: "Won't start", icon: "⚡", query: "My dishwasher won't start or turn on" },
      { label: "Leaking water", icon: "🚿", query: "My dishwasher is leaking water" },
      { label: "Making noise", icon: "🔊", query: "My dishwasher is making loud or unusual noises" },
    ],
  },
};

function DiagnosticCard({ step, onSelect, onQuery }) {
  const current = FLOW[step];

  return (
    <div className="diagnostic-card">
      <div className="diagnostic-prompt">{current.prompt}</div>
      <div className="diagnostic-options">
        {current.options.map((opt) => (
          <button
            key={opt.label}
            className="diagnostic-option"
            onClick={() => opt.query ? onQuery(opt.query) : onSelect(opt.next)}
          >
            <span className="diagnostic-icon">{opt.icon}</span>
            <span>{opt.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default DiagnosticCard;
