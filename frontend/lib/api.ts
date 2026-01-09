import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the auth token
axiosInstance.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Hybrid API object to support both legacy direct calls (like Login) and domain methods
export const api = {
  // Proxy standard axios methods
  get: axiosInstance.get.bind(axiosInstance),
  post: axiosInstance.post.bind(axiosInstance),
  put: axiosInstance.put.bind(axiosInstance),
  delete: axiosInstance.delete.bind(axiosInstance),

  // Domain specific methods
  pipelines: {
    list: async () => {
        const response = await axiosInstance.get('/pipelines/');
        return response.data;
    },
    get: async (id: string) => {
        const response = await axiosInstance.get(`/pipelines/${id}`);
        return response.data;
    }
  },
  jobs: {
    create: async (data: any) => {
        const response = await axiosInstance.post('/jobs/', data);
        return response.data;
    },
    list: async () => {
        const response = await axiosInstance.get('/jobs/');
        return response.data;
    },
    get: async (id: string) => {
        const response = await axiosInstance.get(`/jobs/${id}`);
        return response.data;
    }
  },
  utils: {
    upload: async (file: File, onProgress?: (progress: number) => void) => {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axiosInstance.post('/utils/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
            if (onProgress && progressEvent.total) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                onProgress(percentCompleted);
            }
        }
      });
      return response.data; // { gcs_path: string }
    }
  }
};



