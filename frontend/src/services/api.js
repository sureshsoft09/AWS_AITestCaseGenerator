import axios from 'axios';

// Base URL from environment variable or default to localhost
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8002';

// Create axios instance with default config
const apiInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 1200000, // 10 minutes for long-running agent operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiInstance.interceptors.request.use(
  (config) => {
    // Add any auth headers if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API object with methods that use the axios instance
const api = {
  // Direct axios methods
  get: (url, config) => apiInstance.get(url, config),
  post: (url, data, config) => apiInstance.post(url, data, config),
  put: (url, data, config) => apiInstance.put(url, data, config),
  delete: (url, config) => apiInstance.delete(url, config),
  patch: (url, data, config) => apiInstance.patch(url, data, config),
  
  // Dashboard APIs
  getDashboardSummary: () => apiInstance.get('/dashboard_summary'),
  getProjectHierarchy: () => apiInstance.get('/project_hierarchy'),
  
  // Test Case Generation APIs
  uploadRequirementFile: (formData) => apiInstance.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  
  reviewRequirementSpecifications: (data) => apiInstance.post('/api/generate/review', data),
  requirementClarificationChat: (data) => apiInstance.post('/api/generate/chat', data),
  
  generateTestCases: (data) => apiInstance.post('/api/generate/execute', data),
  
  exportTestCases: (data) => apiInstance.post('/export_testcases', data, {
    responseType: 'blob', // For file downloads
  }),
  
  // Enhancement APIs
  enhanceTestCases: (data) => apiInstance.post('/enhance_test_cases', data),
  enhanceTestCasesChat: (data) => apiInstance.post('/enhance_test_cases_chat', data),
  applyEnhancement: (data) => apiInstance.post('/enhance_test_cases_chat', {
    prompt: data.prompt
  }),
  
  // Migration APIs
  migrateTestCases: (formData) => apiInstance.post('/migrate_test_cases', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  
  // Analytics APIs
  getAnalyticsSummary: () => apiInstance.get('/analytics_summary'),
  
  // Agent Session APIs
  resetAgentSession: () => apiInstance.post('/reset_agentsession'),
  
  // Project Management APIs
  generateProjectId: (data) => apiInstance.post('/api/generate-project-id', data),
  
  // Generic API call method
  call: (method, endpoint, data = null, config = {}) => {
    return apiInstance[method.toLowerCase()](endpoint, data, config);
  },
};

export default api;