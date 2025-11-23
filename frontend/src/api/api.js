// API client for communicating with FastAPI backend
import axios from 'axios';

// Use an explicit VITE_API_URL when provided (for dev or remote deployments).
// If not set, default to contacting the backend on the host at port 8000.
// Using 'http://localhost:8000' is the most compatible default when serving
// the frontend from a different origin (e.g., port 3000 in Docker).
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Q&A Tutor API: Handles question submission and answer retrieval
export const qaAPI = {
  askQuestion: async (question) => {
    const response = await api.post('/api/qa/ask', {
      question,
    });
    return response.data;
  },
};

// Quiz API: Handles quiz generation and grading
export const quizAPI = {
  generateQuiz: async (mode, topic = null, numQuestions = 5, questionTypes = null) => {
    const response = await api.post('/api/quiz/generate', {
      mode,
      topic,
      num_questions: numQuestions,
      question_types: questionTypes || ['multiple_choice', 'true_false', 'open_ended'],
    });
    return response.data;
  },
  
  gradeQuiz: async (quizId, submissions) => {
    const response = await api.post(`/api/quiz/grade?quiz_id=${quizId}`, submissions);
    return response.data;
  },
};

// Document API: Handles document upload and management
export const documentAPI = {
  uploadDocument: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        if (onProgress) onProgress(percentCompleted);
      },
    });
    return response.data;
  },
  
  ingestDirectory: async (directoryPath = null) => {
    const response = await api.post('/api/documents/ingest-directory', null, {
      params: { directory_path: directoryPath },
    });
    return response.data;
  },
  
  getDocumentCount: async () => {
    const response = await api.get('/api/documents/count');
    return response.data;
  },
  
  clearDocuments: async () => {
    const response = await api.delete('/api/documents/clear');
    return response.data;
  },
};

// Health API
export const healthAPI = {
  checkHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
