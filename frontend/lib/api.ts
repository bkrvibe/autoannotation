import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// CSRF token storage (in-memory, set after login)
let csrfToken: string | null = null;

export const setCsrfToken = (token: string) => {
  csrfToken = token;
};

export const getCsrfToken = () => csrfToken;

export const clearCsrfToken = () => {
  csrfToken = null;
};

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Send HttpOnly cookies with requests
});

// Add CSRF token to mutating requests
axiosInstance.interceptors.request.use((config) => {
  // Add CSRF token to state-changing methods
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method?.toUpperCase() || '')) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});

// Handle 401 responses (session expired)
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear CSRF token and redirect to login
      clearCsrfToken();
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth response types
export interface AuthResponse {
  csrf_token: string;
  user: {
    id: string;
    email: string;
    full_name: string | null;
    role: string;
  };
  tenant: {
    id: string;
    name: string;
    slug: string;
  };
}

export interface MeResponse {
  user: {
    id: string;
    email: string;
    full_name: string | null;
    role: string;
  };
  tenant: {
    id: string;
    name: string;
    slug: string;
  };
  tenants: Array<{
    tenant_id: string;
    tenant_name: string;
    tenant_slug: string;
    role_in_tenant: string;
    is_default: boolean;
  }>;
}

// Hybrid API object to support both legacy direct calls (like Login) and domain methods
export const api = {
  // Proxy standard axios methods
  get: axiosInstance.get.bind(axiosInstance),
  post: axiosInstance.post.bind(axiosInstance),
  put: axiosInstance.put.bind(axiosInstance),
  delete: axiosInstance.delete.bind(axiosInstance),

  // Auth methods
  auth: {
    login: async (email: string, password: string): Promise<AuthResponse> => {
      const response = await axiosInstance.post('/auth/login', { email, password });
      setCsrfToken(response.data.csrf_token);
      return response.data;
    },
    logout: async (): Promise<void> => {
      try {
        await axiosInstance.post('/auth/logout');
      } finally {
        clearCsrfToken();
      }
    },
    me: async (): Promise<MeResponse> => {
      const response = await axiosInstance.get('/auth/me');
      return response.data;
    },
    requestMagicLink: async (email: string): Promise<{ message: string }> => {
      const response = await axiosInstance.post('/auth/magic-link', { email });
      return response.data;
    },
    verifyMagicLink: async (token: string): Promise<AuthResponse> => {
      const response = await axiosInstance.post('/auth/magic-link/verify', { token });
      setCsrfToken(response.data.csrf_token);
      return response.data;
    },
    acceptInvite: async (token: string, password: string, name: string): Promise<AuthResponse> => {
      const response = await axiosInstance.post('/auth/accept-invite', { token, password, name });
      setCsrfToken(response.data.csrf_token);
      return response.data;
    },
    forgotPassword: async (email: string): Promise<{ message: string }> => {
      const response = await axiosInstance.post('/auth/forgot-password', { email });
      return response.data;
    },
    resetPassword: async (token: string, new_password: string): Promise<{ message: string }> => {
      const response = await axiosInstance.post('/auth/reset-password', { token, new_password });
      return response.data;
    },
    switchTenant: async (tenant_id: string): Promise<AuthResponse> => {
      const response = await axiosInstance.post('/auth/switch-tenant', { tenant_id });
      setCsrfToken(response.data.csrf_token);
      return response.data;
    },
  },

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
    },
    fetchXcom: async (id: string, taskId: string = 'convert_to_calipergt') => {
        const response = await axiosInstance.get(`/jobs/${id}/xcom?task_id=${taskId}`);
        return response.data;
    },
    getTasks: async (id: string) => {
        const response = await axiosInstance.get(`/jobs/${id}/tasks`);
        return response.data;
    },
    downloadArtifact: async (id: string, format: 'calipergt' | 'coco' | 'kitti3d' = 'calipergt') => {
        const response = await axiosInstance.post(`/jobs/${id}/download?format=${format}`, null, {
            responseType: 'blob'
        });
        return response;
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
    },
    uploadMultiple: async (files: FileList | File[], onProgress?: (progress: number) => void) => {
      const formData = new FormData();

      // Append all files - for folder uploads, the webkitRelativePath contains the folder structure
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        // Use webkitRelativePath if available (folder upload), otherwise just the name
        const relativePath = (file as any).webkitRelativePath || file.name;
        formData.append('files', file, relativePath);
      }

      const response = await axiosInstance.post('/utils/upload-multiple', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 600000, // 10 minute timeout for large uploads
        onUploadProgress: (progressEvent) => {
            if (onProgress && progressEvent.total) {
                // Cap at 95% during upload, the last 5% is for server processing
                const percentCompleted = Math.min(95, Math.round((progressEvent.loaded * 95) / progressEvent.total));
                onProgress(percentCompleted);
            }
        }
      });
      // Signal completion
      if (onProgress) {
        onProgress(100);
      }
      return response.data; // { gcs_path: string, file_count: number, files: [...], validation: {...} }
    },
    getDataStructureGuide: async (pipelineType: string = '2d') => {
      const response = await axiosInstance.get(`/utils/data-structure-guide?pipeline_type=${pipelineType}`);
      return response.data;
    },
    validateUpload: async (file: File, pipelineType?: string) => {
      const formData = new FormData();
      formData.append('file', file);

      const url = pipelineType
        ? `/utils/validate-upload?pipeline_type=${pipelineType}`
        : '/utils/validate-upload';

      const response = await axiosInstance.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    validateGcsData: async (gcsPath: string, pipelineType: string = '3d') => {
      const response = await axiosInstance.post(
        `/utils/validate-gcs-data?gcs_path=${encodeURIComponent(gcsPath)}&pipeline_type=${pipelineType}`
      );
      return response.data;
    },
    uploadAdditional: async (
      file: File,
      baseGcsPath: string,
      targetPath: string,
      onProgress?: (progress: number) => void
    ) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axiosInstance.post(
        `/utils/upload-additional?base_gcs_path=${encodeURIComponent(baseGcsPath)}&target_path=${encodeURIComponent(targetPath)}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (onProgress && progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              onProgress(percentCompleted);
            }
          }
        }
      );
      return response.data;
    }
  }
};

// Types for validation responses
export interface DataValidationResponse {
  is_valid: boolean;
  format_detected: string;
  pipeline_type: string;
  errors: string[];
  warnings: string[];
  suggestions: string[];
  file_counts: Record<string, number>;
  structure_help?: {
    pipeline: string;
    formats: Record<string, {
      structure: string[];
      description: string;
    }>;
    supported_formats?: string[];
  };
}

export interface MissingFile {
  file_type: string;
  expected_names: string[];
  description: string;
  required: boolean;
}

export interface UploadValidation {
  detected_type: string;
  is_valid_structure: boolean;
  warnings: string[];
  suggestions: string[];
  file_counts: Record<string, number>;
  missing_files?: MissingFile[];
  found_candidates?: Record<string, string[]>;
  needs_user_input?: boolean;
}



