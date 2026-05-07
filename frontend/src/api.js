import axios from 'axios';

const API = axios.create({
  baseURL: '',          // uses Vite proxy in dev, relative in prod
  timeout: 15000,
});

// ── Dashboard APIs ──────────────────────────────────────────────────
export const fetchBusinesses = () => API.get('/api/dashboard/businesses');
export const fetchAuditLogs  = (ubid) =>
  API.get('/api/dashboard/audit-logs', { params: ubid ? { ubid } : {} });
export const fetchConflicts   = () => API.get('/api/dashboard/conflicts');
export const fetchRetryQueue  = () => API.get('/api/dashboard/retry-queue');
export const fetchHealth      = () => API.get('/api/dashboard/health');
export const fetchStats       = () => API.get('/api/dashboard/stats');

// ── Demo Triggers ───────────────────────────────────────────────────
export const triggerSwsToDept  = () => API.post('/api/dashboard/demo/sws-to-departments');
export const triggerDeptToSws  = () => API.post('/api/dashboard/demo/department-to-sws');
export const triggerConflict   = () => API.post('/api/dashboard/demo/conflict');
export const triggerRetry      = () => API.post('/api/dashboard/demo/retry');
export const triggerReset      = () => API.post('/api/dashboard/demo/reset');

// ── Direct System APIs (for manual testing / interactive demo) ──────
export const updateSWS     = (data) => API.post('/api/sws/update-business', data);
export const updateFactory = (data) => API.post('/api/factory/update', data);
export const updateShop    = (data) => API.post('/api/shop/update', data);

export default API;
