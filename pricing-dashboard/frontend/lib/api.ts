import axios from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────
export const authApi = {
  signup: (data: { org_name: string; slug: string; full_name: string; email: string; password: string }) =>
    api.post('/auth/signup', data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  join: (data: { invite_code: string; full_name: string; email: string; password: string }) =>
    api.post('/auth/join', data),
  me: () => api.get('/auth/me'),
};

// ── Products ──────────────────────────────────────────
export const productsApi = {
  list: (params?: { page?: number; page_size?: number; search?: string; category_id?: string }) =>
    api.get('/products', { params }),
  get: (id: string) => api.get(`/products/${id}`),
  create: (data: any) => api.post('/products', data),
  update: (id: string, data: any) => api.put(`/products/${id}`, data),
  delete: (id: string) => api.delete(`/products/${id}`),
  listCategories: () => api.get('/products/categories/all'),
  createCategory: (data: { name: string; margin_floor_pct: number }) =>
    api.post('/products/categories/create', data),
};

// ── Recommendations ───────────────────────────────────
export const recommendationsApi = {
  list: (params?: { page?: number; status_filter?: string; min_confidence?: number }) =>
    api.get('/recommendations', { params }),
  get: (id: string) => api.get(`/recommendations/${id}`),
  generate: (product_ids: string[]) =>
    api.post('/recommendations/generate', { product_ids }),
  approve: (id: string) => api.post(`/recommendations/${id}/approve`),
  reject: (id: string, reason: string) =>
    api.post(`/recommendations/${id}/reject`, { reason }),
  modify: (id: string, new_price: number) =>
    api.post(`/recommendations/${id}/modify`, { new_price }),
};

// ── Audit ─────────────────────────────────────────────
export const auditApi = {
  list: (params?: { page?: number; product_id?: string; status_filter?: string; date_from?: string; date_to?: string }) =>
    api.get('/audit', { params }),
};

// ── Config ────────────────────────────────────────────
export const configApi = {
  get: () => api.get('/config'),
  update: (data: { auto_execute_threshold?: number; margin_floor_default?: number; escalation_rules?: any }) =>
    api.put('/config', data),
  orgInfo: () => api.get('/config/org-info'),
};

export default api;
