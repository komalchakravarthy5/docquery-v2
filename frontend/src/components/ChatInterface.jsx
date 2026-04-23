import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';
import { api } from '../services/api';
import './ChatInterface.css';

const ChatInterface = ({ documentId, documentName }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [metrics, setMetrics] = useState(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  const sourceOptions = ['ALL', ...documentName.split(' | ').map((name) => name.trim())];

  const refreshMetrics = async () => {
    try {
      const data = await api.getDocumentMetrics(documentId);
      setMetrics(data);
    } catch (error) {
      console.error('Error loading metrics:', error);
    }
  };

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    refreshMetrics();
  }, [documentId]);

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
      const response = await api.queryDocument(
        documentId,
        trimmedInput,
        sourceFilter === 'ALL' ? null : sourceFilter,
      );

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.answer,
        citations: response.citations,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
      refreshMetrics();
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
          <div className="filter-controls">
            <label htmlFor="source-filter">Source</label>
            <select
              id="source-filter"
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              disabled={isLoading}
            >
              {sourceOptions.map((option) => (
                <option value={option} key={option}>{option}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {metrics && (
        <div className="metrics-panel">
          <div className="metric-card"><span>Avg Latency</span><strong>{metrics.avg_latency_ms} ms</strong></div>
          <div className="metric-card"><span>Avg Relevance</span><strong>{(metrics.avg_relevance_score * 100).toFixed(1)}%</strong></div>
          <div className="metric-card"><span>Success Rate</span><strong>{(metrics.query_success_rate * 100).toFixed(1)}%</strong></div>
          <div className="metric-card"><span>Grounding</span><strong>{((metrics.avg_grounding_score || 0) * 100).toFixed(1)}%</strong></div>
          <div className="metric-card"><span>Total Queries</span><strong>{metrics.total_queries}</strong></div>
          <div className="trend-chart">
            <p>Latency Trend (recent queries)</p>
            <div className="trend-bars">
              {metrics.trend.length === 0 ? <span className="muted">No trend yet</span> : metrics.trend.map((point, idx) => {
                const height = Math.max(8, Math.min(80, point.latency_ms / 10));
                return <div key={idx} className="trend-bar" title={`${point.latency_ms} ms`} style={{ height: `${height}px` }} />;
              })}
            </div>
          </div>
        </div>
      )}

      <div className="messages-container" ref={messagesContainerRef}>
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
