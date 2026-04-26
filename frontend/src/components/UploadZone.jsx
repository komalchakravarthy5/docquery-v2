import React, { useState, useCallback } from 'react';
import './UploadZone.css';

const SUPPORTED_EXTS = ['.pdf', '.docx', '.pptx', '.xlsx', '.csv', '.xls'];

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

  const processFiles = (fileList) => {
    if (!fileList || fileList.length === 0) return;
    
    const filesArray = Array.from(fileList);
    
    // Validate types natively
    const validFiles = filesArray.filter(f => {
      return SUPPORTED_EXTS.some(ext => f.name.toLowerCase().endsWith(ext));
    });

    if (validFiles.length === 0) {
      alert(`Please upload supported document formats: ${SUPPORTED_EXTS.join(', ')}`);
      return;
    }

    if (validFiles.length !== filesArray.length) {
      alert(`Some files were skipped. Supported formats: ${SUPPORTED_EXTS.join(', ')}`);
    }

    onUpload(validFiles);
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  }, [onUpload]);

  const handleFileInput = (e) => {
    processFiles(e.target.files);
    // Reset file input so same file can be selected again if needed
    e.target.value = null;
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
        accept=".pdf,.docx,.pptx,.xlsx,.xls,.csv"
        multiple
        onChange={handleFileInput}
        disabled={isUploading}
        style={{ display: 'none' }}
      />

      <div className="upload-content">
        <div className="upload-icon">📄</div>
        <h3>{isUploading ? 'Processing Workspace...' : 'Upload Documents'}</h3>
        <p className="upload-text">
          {isUploading
            ? 'Extracting text and generating multi-document workspace...'
            : 'Drag and drop or click to browse your documents'}
        </p>
        <label htmlFor="file-upload" className="btn btn-primary" style={{ cursor: isUploading ? 'not-allowed' : 'pointer' }}>
          {isUploading ? 'Uploading...' : 'Choose Files'}
        </label>
        <p className="upload-hint">Supports PDF, DOCX, PPTX, Excel, and CSV.</p>
      </div>
    </div>
  );
};

export default UploadZone;
