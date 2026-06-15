import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage } from "../api/api";
import { marked } from "marked";
import PartCard from "./PartCard";
import FlowCard from "./FlowCard";
import { FLOWS } from "../flows/flows";


function ChatWindow({ rememberedModel, onModelDetected }) {

  const defaultMessage = [{
    role: "assistant",
    content: "Hi! I can help you find refrigerator and dishwasher parts, check compatibility, and troubleshoot issues. What do you need help with?",
    parts: [],
  }];

  const [messages, setMessages] = useState(defaultMessage);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [showFlowMenu, setShowFlowMenu] = useState(false);

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const textareaRef = useRef(null);

  const handleVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input isn't supported in this browser. Try Chrome or Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;
    recognitionRef.current = recognition;

    recognition.onstart = () => setIsListening(true);

    recognition.onresult = (e) => {
      const transcript = Array.from(e.results)
        .map(r => r[0].transcript)
        .join("");
      setInput(transcript);
    };

    recognition.onend = () => setIsListening(false);

    recognition.onerror = () => setIsListening(false);

    recognition.start();
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleAddToCart = async (part) => {
    try {
      await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `Add part ${part.part_number} to my cart`,
          history: messages,
        }),
      });
    } catch (err) {
      console.error(err);
    }

    setMessages(prev => [...prev, {
      role: "assistant",
      content: `Added **${part.name}** (${part.part_number}) to your cart.`,
      parts: [],
    }]);
  };

  const handleSend = async (override) => {
    const userText = typeof override === "string" ? override : input;
    if (userText.trim() === "") return;

    setMessages(prev => [...prev, { role: "user", content: userText, parts: [] }]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    try {
      setIsLoading(true);
      const newMessage = await getAIMessage(userText, messages, rememberedModel);
      if (newMessage.detected_model && !rememberedModel) {
        onModelDetected(newMessage.detected_model);
      }
      setMessages(prev => [...prev, newMessage]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
        parts: [],
      }]);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const lastAssistantIndex = messages.map(m => m.role).lastIndexOf("assistant");

  const sendChip = (text) => handleSend(text);

  const startFlow = (flowKey) => {
    setShowFlowMenu(false);
    const flow = FLOWS[flowKey];
    setMessages(prev => [...prev, {
      role: "flow",
      flowKey,
      steps: flow.steps,
      currentStep: flow.start,
      values: {},
      parts: [],
      chips: [],
    }]);
  };

  const handleFlowStep = (nextStep, newValues, index) => {
    setMessages(prev => prev.map((m, i) =>
      i === index ? { ...m, currentStep: nextStep, values: newValues } : m
    ));
  };

  const handleFlowQuery = (query, index) => {
    setMessages(prev => prev.filter((_, i) => i !== index));
    handleSend(query);
  };

  return (
    <div className="messages-container">
      {messages.map((message, index) => {
        const isLastAssistant = message.role === "assistant" && index === lastAssistantIndex;
        const chips = isLastAssistant && !isLoading && index > 0 ? (message.chips || []) : [];

        if (message.role === "flow") {
          return (
            <div key={index} className="message-row assistant-row">
              <div className="avatar assistant-avatar">PS</div>
              <FlowCard
                flow={message}
                onStep={(nextStep, newValues) => handleFlowStep(nextStep, newValues, index)}
                onQuery={(query) => handleFlowQuery(query, index)}
              />
            </div>
          );
        }

        return (
          <div key={index} className={`message-row ${message.role}-row`}>
            {message.role === "assistant" && (
              <div className="avatar assistant-avatar">PS</div>
            )}
            <div className="message-col">
              <div className={`message ${message.role}-message`}>
                <div dangerouslySetInnerHTML={{ __html: marked(message.content || "").replace(/<p>|<\/p>/g, "") }} />
              </div>
              {message.parts?.length > 0 && (
                <div className="part-cards-grid">
                  {message.parts.map((part) => (
                    <PartCard
                      key={part.part_number}
                      part={part}
                      onAddToCart={handleAddToCart}
                    />
                  ))}
                </div>
              )}
              {chips.length > 0 && (
                <div className="chips-row">
                  {chips.map((chip) => (
                    <button key={chip} className="chip" onClick={() => sendChip(chip)}>
                      {chip}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {message.role === "user" && (
              <div className="avatar user-avatar">O</div>
            )}
          </div>
        );
      })}
      {isLoading && (
        <div className="message-row assistant-row">
          <div className="avatar assistant-avatar">PS</div>
          <div className="message assistant-message typing-indicator">
            <span /><span /><span />
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
      <div className="input-wrapper">
        <div className="input-area">
        <div className="flow-menu-wrap">
          <button
            className="flow-menu-btn"
            onClick={() => setShowFlowMenu(v => !v)}
            disabled={isLoading}
            title="Quick actions"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </button>
          {showFlowMenu && (
            <div className="flow-menu-popup">
              <div className="flow-menu-title">Quick actions</div>
              {Object.entries(FLOWS).map(([key, flow]) => (
                <button key={key} className="flow-menu-item" onClick={() => startFlow(key)}>
                  <span className="flow-menu-label">{flow.label}</span>
                  <span className="flow-menu-desc">{flow.description}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        <textarea
          ref={textareaRef}
          value={input}
          rows={1}
          onChange={(e) => {
            setInput(e.target.value);
            e.target.style.height = "auto";
            e.target.style.height = e.target.scrollHeight + "px";
          }}
          placeholder={isListening ? "Listening..." : "Ask about parts, compatibility, or troubleshooting..."}
          disabled={isLoading}
          onKeyPress={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              handleSend();
              e.preventDefault();
            }
          }}
        />
        <button
          className={`mic-button ${isListening ? "mic-active" : ""}`}
          onClick={handleVoice}
          disabled={isLoading}
          title={isListening ? "Stop listening" : "Speak your question"}
        >
          {isListening ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          )}
        </button>
        <button className="send-button" onClick={handleSend} disabled={isLoading}>
          {isLoading ? (
            <span className="btn-spinner" />
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
        </div>
      </div>
    </div>
  );
}

export default ChatWindow;
