import React, { useState } from 'react';
import Header from './components/Header';
import UploadZone from './components/UploadZone';
import ChatInterface from './components/ChatInterface';
import { api } from './services/api';
import './App.css';

function App() {
  const [currentDocument, setCurrentDocument] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async (files) => {
    setIsUploading(true);
    try {
      const response = await api.uploadDocument(files);
      setCurrentDocument({
        id: response.document_id,
        name: response.filename,
        numPages: response.num_pages,
        numChunks: response.num_chunks,
      });
    } catch (error) {
      console.error('Error uploading document workspace:', error);
      alert(error.message || 'Failed to upload workspace. Please try again.');
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
        <div className="container" id="home">
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

      {/* About Section */}
      <section id="about" className="about-section fade-in-up" style={{ padding: '80px 20px', textAlign: 'center', backgroundColor: 'var(--surface-color)', marginTop: '80px', borderTop: '1px solid #333' }}>
        <div className="container">
          <h2>About This Project</h2>
          <p style={{ maxWidth: '800px', margin: '20px auto', lineHeight: '1.8', color: '#aaa', fontSize: '1.1rem' }}>
            DocQuery is an advanced Universal Document Workspace built as my academic dissertation at VIT. 
            It leverages robust Retrieval-Augmented Generation (RAG) architectures, scalable dynamic chunking engines, 
            and the formidable intelligence of the Google Gemini API to democratize complex document exploration.
          </p>
          <div style={{ marginTop: '40px', fontSize: '1.2rem', fontWeight: 'bold' }}>
            Conceptualized & Developed by <br />
            <span className="gradient-text" style={{ fontSize: '1.5rem', display: 'inline-block', marginTop: '10px' }}>Komal Chakravarthy</span>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <p>DocQuery - Intelligent Document Chat Assistant | VIT Dissertation Project 2026</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
