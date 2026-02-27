import React, { useState } from 'react';
import Header from './components/Header';
import UploadZone from './components/UploadZone';
import ChatInterface from './components/ChatInterface';
import { api } from './services/api';
import './App.css';

function App() {
  const [currentDocument, setCurrentDocument] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async (file) => {
    setIsUploading(true);
    try {
      const response = await api.uploadDocument(file);
      setCurrentDocument({
        id: response.document_id,
        name: response.filename,
        numPages: response.num_pages,
        numChunks: response.num_chunks,
      });
    } catch (error) {
      console.error('Error uploading document:', error);
      alert(error.message || 'Failed to upload document. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleNewDocument = () => {
    setCurrentDocument(null);
  };

  return (
    <div className="app">
      <Header />

      <main className="main-content">
        <div className="container">
          {!currentDocument ? (
            <div className="hero-section">
              <div className="hero-text fade-in-up">
                <h1>
                  Chat with Your <span className="gradient-text">Documents</span>
                </h1>
                <p className="hero-subtitle">
                  Upload a PDF and ask questions. Get accurate, citation-backed answers powered by AI.
                </p>
              </div>
              <div className="upload-section fade-in-up">
                <UploadZone onUpload={handleUpload} isUploading={isUploading} />
              </div>
            </div>
          ) : (
            <div className="chat-section fade-in-up">
              <div className="chat-header-actions">
                <button className="btn btn-secondary" onClick={handleNewDocument}>
                  ← Upload New Document
                </button>
                <div className="doc-info">
                  <span className="doc-stat">{currentDocument.numPages} pages</span>
                  <span className="doc-stat">{currentDocument.numChunks} chunks</span>
                </div>
              </div>
              <ChatInterface
                documentId={currentDocument.id}
                documentName={currentDocument.name}
              />
            </div>
          )}
        </div>
      </main>

      <footer className="footer">
        <div className="container">
          <p>DocQuery - Intelligent Document Chat Assistant | VIT Dissertation Project 2026</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
