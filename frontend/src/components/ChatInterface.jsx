import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';
import { api } from '../services/api';
import './ChatInterface.css';

const ChatInterface = ({ documentId, documentName }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    const trimmedInput = inputValue.trim();
    if (!trimmedInput || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: trimmedInput,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await api.queryDocument(documentId, trimmedInput);

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.answer,
        citations: response.citations,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error querying document:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: error.message || 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="chat-header-content">
          <div className="doc-indicator">
            <span className="doc-icon">📄</span>
            <div>
              <h3>Chatting with</h3>
              <p className="doc-name">{documentName}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <h3>Start a Conversation</h3>
            <p>Ask questions about your document and get citation-backed answers</p>
            <div className="example-questions">
              <p className="example-label">Try asking:</p>
              <button className="example-btn" onClick={() => setInputValue('What is the main topic of this document?')}>
                "What is the main topic of this document?"
              </button>
              <button className="example-btn" onClick={() => setInputValue('Summarize the key findings')}>
                "Summarize the key findings"
              </button>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="loading-message">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            placeholder="Ask a question about your document..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={isLoading}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
          >
            <span className="send-icon">➤</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
