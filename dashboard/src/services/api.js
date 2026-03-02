import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Health & System ─────────────────────────────────────────
export const getHealth = () => api.get('/health');
export const getSystemSummary = () => api.get('/system/summary');

// ── Prediction ──────────────────────────────────────────────
export const predictQuality = (params) =>
  api.post('/predict/quality', {
    parameters: params,
    include_physics: true,
    include_explainability: true,
  });

export const batchForecast = (params) =>
  api.post('/predict/batch_forecast', { parameters: params });

// ── Optimization ────────────────────────────────────────────
export const runOptimization = (payload) =>
  api.post('/optimize/run', payload);

export const getOptimizationMethods = () =>
  api.get('/optimize/methods');

// ── Golden Signature ────────────────────────────────────────
export const getCurrentSignature = () =>
  api.get('/golden-signature/current');

export const getAllSignatures = () =>
  api.get('/golden-signature/all');

export const approveSignature = (signatureId, approved, feedback = '') =>
  api.post('/golden-signature/approve', {
    signature_id: signatureId,
    approved,
    feedback,
  });

export const reprioritizeTargets = (targets) =>
  api.post('/golden-signature/reprioritize', targets);

// ── Carbon ──────────────────────────────────────────────────
export const computeCarbonTarget = (payload) =>
  api.post('/carbon/target', payload);

export const getCarbonDashboard = () =>
  api.get('/carbon/dashboard');

export const getOptimalWindow = () =>
  api.get('/carbon/optimal-window');

// ── Decision Engine ─────────────────────────────────────────
export const monitorBatch = (payload) =>
  api.post('/decision/monitor', payload);

export const getAlerts = () =>
  api.get('/decision/alerts');

export const acknowledgeAlert = (decisionId) =>
  api.post(`/decision/acknowledge/${decisionId}`);

// ── Digital Twin ────────────────────────────────────────────
export const simulate = (payload) =>
  api.post('/digital-twin/simulate', payload);

export const whatIf = (payload) =>
  api.post('/digital-twin/what-if', payload);

export const validateOptimization = (payload) =>
  api.post('/digital-twin/validate-optimization', payload);

export const getOptimalStart = () =>
  api.get('/digital-twin/energy/optimal-start');

export const getMaintenanceForecast = () =>
  api.get('/digital-twin/maintenance-forecast');

// ── Validation ──────────────────────────────────────────────
export const calculateROI = (payload) =>
  api.post('/validation/roi', payload);

export const sensitivityAnalysis = (payload) =>
  api.post('/validation/sensitivity', payload);

export const replayBatches = (payload) =>
  api.post('/validation/replay', payload);

export const paretoAnalysis = (payload) =>
  api.post('/validation/pareto-analysis', payload);

export default api;
