import React, { useState, useCallback } from 'react';
import './UploadZone.css';

const UploadZone = ({ onUpload, isUploading }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragOut = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        onUpload(file);
      } else {
        alert('Please upload a PDF file');
      }
    }
  }, [onUpload]);

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.type === 'application/pdf') {
        onUpload(file);
      } else {
        alert('Please upload a PDF file');
      }
    }
  };

  return (
    <div
      className={`upload-zone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="file-upload"
        accept=".pdf"
        onChange={handleFileInput}
        disabled={isUploading}
        style={{ display: 'none' }}
      />

      <div className="upload-content">
        <div className="upload-icon">📄</div>
        <h3>{isUploading ? 'Processing...' : 'Upload Your Document'}</h3>
        <p className="upload-text">
          {isUploading
            ? 'Extracting text and generating embeddings...'
            : 'Drag and drop your PDF here or click to browse'}
        </p>
        <label htmlFor="file-upload" className="btn btn-primary">
          {isUploading ? 'Uploading...' : 'Choose PDF File'}
        </label>
        <p className="upload-hint">Supports PDF files up to 50MB</p>
      </div>
    </div>
  );
};

export default UploadZone;
