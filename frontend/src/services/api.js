import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const getErrorMessage = (error, fallback) => {
  return (
    error?.response?.data?.detail
    || error?.message
    || fallback
  );
};

export const api = {
  // Health check
  health: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Upload Documents
  uploadDocument: async (files) => {
    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });

      const response = await apiClient.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error, 'Failed to upload document.'));
    }
  },

  // Query document
  queryDocument: async (documentId, query, sourceFilter = null) => {
    try {
      const response = await apiClient.post('/query', {
        document_id: documentId,
        query: query.trim(),
        source_filter: sourceFilter || null,
      });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error, 'Failed to query document.'));
    }
  },

  getDocumentMetrics: async (documentId) => {
    try {
      const response = await apiClient.get(`/metrics/${documentId}`);
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error, 'Failed to load metrics.'));
    }
  },

  // List documents
  listDocuments: async () => {
    try {
      const response = await apiClient.get('/documents');
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error, 'Failed to list documents.'));
    }
  },
};

export default api;
