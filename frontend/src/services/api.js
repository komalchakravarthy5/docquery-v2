import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health check
  health: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Upload PDF
  uploadDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Query document
  queryDocument: async (documentId, query) => {
    const response = await apiClient.post('/query', {
      document_id: documentId,
      query: query,
    });
    return response.data;
  },

  // List documents
  listDocuments: async () => {
    const response = await apiClient.get('/documents');
    return response.data;
  },
};

export default api;
