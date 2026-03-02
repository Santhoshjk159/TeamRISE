import { useState, useCallback } from 'react';

export function useApi(apiFunc) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFunc(...args);
      setData(response.data);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Request failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFunc]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}

// Default process parameter values
export const DEFAULT_PARAMS = {
  granulation_time: 25.0,
  binder_amount: 5.0,
  drying_temp: 55.0,
  drying_time: 40.0,
  compression_force: 18.0,
  machine_speed: 35.0,
  lubricant_conc: 1.0,
  moisture_content: 3.0,
};

// Parameter metadata (label, min, max, unit, step)
export const PARAM_META = {
  granulation_time:  { label: 'Granulation Time',  min: 10, max: 60,  unit: 'min',  step: 0.5 },
  binder_amount:     { label: 'Binder Amount',     min: 1,  max: 10,  unit: '%',    step: 0.1 },
  drying_temp:       { label: 'Drying Temp',       min: 30, max: 80,  unit: '°C',   step: 0.5 },
  drying_time:       { label: 'Drying Time',       min: 15, max: 90,  unit: 'min',  step: 1 },
  compression_force: { label: 'Compression Force', min: 5,  max: 30,  unit: 'kN',   step: 0.5 },
  machine_speed:     { label: 'Machine Speed',     min: 10, max: 60,  unit: 'rpm',  step: 1 },
  lubricant_conc:    { label: 'Lubricant Conc',     min: 0.1, max: 3, unit: '%',    step: 0.05 },
  moisture_content:  { label: 'Moisture Content',  min: 0.5, max: 8,  unit: '%',    step: 0.1 },
};

export const QUALITY_COLORS = {
  Hardness: '#6366f1',
  Dissolution_Rate: '#10b981',
  Content_Uniformity: '#f59e0b',
  Energy_kWh: '#ef4444',
  CO2_kg: '#8b5cf6',
};
