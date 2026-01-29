import React from 'react';
import Citation from './Citation';
import './Message.css';

const Message = ({ message }) => {
  const { type, content, citations, timestamp, isError } = message;

  return (
    <div className={`message ${type} ${isError ? 'error' : ''}`}>
      <div className="message-avatar">
        {type === 'user' ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        <div className="message-bubble">
          <p>{content}</p>
        </div>
        {citations && citations.length > 0 && (
          <div className="citations-container">
            <p className="citations-label">📚 Sources:</p>
            <div className="citations-list">
              {citations.map((citation, index) => (
                <Citation key={index} citation={citation} />
              ))}
            </div>
          </div>
        )}
        <span className="message-time">
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
};

export default Message;
