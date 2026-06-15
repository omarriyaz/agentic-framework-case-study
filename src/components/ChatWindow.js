import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage } from "../api/api";
import { marked } from "marked";
import PartCard from "./PartCard";


function ChatWindow({ rememberedModel, onModelDetected }) {

  const defaultMessage = [{
    role: "assistant",
    content: "Hi! I can help you find refrigerator and dishwasher parts, check compatibility, and troubleshoot issues. What do you need help with?",
    parts: [],
  }];

  const [messages, setMessages] = useState(defaultMessage);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

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

  return (
    <div className="messages-container">
      {messages.map((message, index) => {
        const isLastAssistant = message.role === "assistant" && index === lastAssistantIndex;
        const chips = isLastAssistant && !isLoading && index > 0 ? (message.chips || []) : [];

        return (
          <div key={index} className={`message-row ${message.role}-row`}>
            {message.role === "assistant" && (
              <div className="avatar assistant-avatar">PS</div>
            )}
            <div className="message-col">
              <div className={`message ${message.role}-message`}>
                <div dangerouslySetInnerHTML={{ __html: marked(message.content).replace(/<p>|<\/p>/g, "") }} />
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
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about parts, compatibility, or troubleshooting..."
          disabled={isLoading}
          onKeyPress={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              handleSend();
              e.preventDefault();
            }
          }}
        />
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
  );
}

export default ChatWindow;
