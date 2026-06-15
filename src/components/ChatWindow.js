import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage } from "../api/api";
import { marked } from "marked";

function ChatWindow() {

  const defaultMessage = [{
    role: "assistant",
    content: "Hi, how can I help you today?"
  }];

  const [messages, setMessages] = useState(defaultMessage);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
      scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (input.trim() === "") return;

    const userText = input;
    setMessages(prev => [...prev, { role: "user", content: userText }]);
    setInput("");

    try {
      setIsLoading(true);
      const newMessage = await getAIMessage(userText);
      setMessages(prev => [...prev, newMessage]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, something went wrong. Please try again." }]);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
      <div className="messages-container">
          {messages.map((message, index) => (
            <div key={index} className={`message-row ${message.role}-row`}>
              {message.role === "assistant" && (
                <div className="avatar assistant-avatar">PS</div>
              )}
              <div className={`message ${message.role}-message`}>
                <div dangerouslySetInnerHTML={{ __html: marked(message.content).replace(/<p>|<\/p>/g, "") }} />
              </div>
              {message.role === "user" && (
                <div className="avatar user-avatar">O</div>
              )}
            </div>
          ))}
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
