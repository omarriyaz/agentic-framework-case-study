import React, { useState } from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";

function App() {
  const [rememberedModel, setRememberedModel] = useState(null);
  const [mode, setMode] = useState("homeowner");

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-brand">
          <div className="header-title">
            <span className="header-title-main">PartSelect</span>
            <span className="header-title-sub">AI Assistant</span>
          </div>
        </div>
        <div className="header-right">
          <div className="mode-toggle" role="group" aria-label="User mode">
            <button
              className={`mode-btn ${mode === "homeowner" ? "mode-btn--active" : ""}`}
              onClick={() => setMode("homeowner")}
            >
              Homeowner
            </button>
            <button
              className={`mode-btn ${mode === "technician" ? "mode-btn--active" : ""}`}
              onClick={() => setMode("technician")}
            >
              Technician
            </button>
          </div>
          {rememberedModel ? (
            <div className="model-pill">
              <span className="model-pill-label">Your appliance:</span>
              <span className="model-pill-value">{rememberedModel}</span>
              <button className="model-pill-clear" onClick={() => setRememberedModel(null)}>✕</button>
            </div>
          ) : null}
        </div>
      </header>
      <ChatWindow rememberedModel={rememberedModel} onModelDetected={setRememberedModel} mode={mode} />
    </div>
  );
}

export default App;
