import React, { useState } from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";

function App() {
  const [rememberedModel, setRememberedModel] = useState(null);

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
          {rememberedModel ? (
            <div className="model-pill">
              <span className="model-pill-label">Your appliance:</span>
              <span className="model-pill-value">{rememberedModel}</span>
              <button className="model-pill-clear" onClick={() => setRememberedModel(null)}>✕</button>
            </div>
          ) : (
            <div className="header-badge">Refrigerator &amp; Dishwasher Parts</div>
          )}
        </div>
      </header>
      <ChatWindow rememberedModel={rememberedModel} onModelDetected={setRememberedModel} />
    </div>
  );
}

export default App;
