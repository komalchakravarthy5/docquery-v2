import React from 'react';
import './Citation.css';

const Citation = ({ citation }) => {
  const { page_number, text_snippet, relevance_score } = citation;

  return (
    <div className="citation">
      <div className="citation-header">
        <span className="citation-page">Page {page_number}</span>
        <span className="citation-score">{(relevance_score * 100).toFixed(0)}% relevant</span>
      </div>
      <p className="citation-text">"{text_snippet}"</p>
    </div>
  );
};

export default Citation;
