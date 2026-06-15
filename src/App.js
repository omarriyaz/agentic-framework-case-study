import React from "react";
import "./App.css";
import ChatWindow from "./components/ChatWindow";

function App() {
  return (
    <div className="App">
      <header className="app-header">
        <div className="header-brand">
          <div className="header-title">
            <span className="header-title-main">PartSelect</span>
            <span className="header-title-sub">AI Assistant</span>
          </div>
        </div>
        <div className="header-badge">Refrigerator &amp; Dishwasher Parts</div>
      </header>
      <ChatWindow />
    </div>
  );
}

export default App;
