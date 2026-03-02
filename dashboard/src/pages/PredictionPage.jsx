import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, AreaChart, Area, ResponsiveContainer,
  XAxis, YAxis, Tooltip, CartesianGrid, Cell, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import {
  Brain, Sparkles, Send, RefreshCw, FlaskConical,
  TrendingUp, AlertTriangle, CheckCircle2
} from 'lucide-react';
import { SectionHeader, ParamSlider, LoadingSpinner, ErrorBanner, MetricCard } from '../components/ui';
import { useApi, DEFAULT_PARAMS, PARAM_META, QUALITY_COLORS } from '../hooks/useApi';
import { predictQuality } from '../services/api';

export default function PredictionPage() {
  const [params, setParams] = useState({ ...DEFAULT_PARAMS });
  const { data, loading, error, execute } = useApi(predictQuality);

  const handleChange = (name, value) => setParams(prev => ({ ...prev, [name]: value }));
  const handlePredict = () => execute(params);
  const handleReset = () => setParams({ ...DEFAULT_PARAMS });

  // Build chart data from predictions
  const predictionBars = data?.predictions
    ? Object.entries(data.predictions).map(([key, val]) => ({
        name: key.replace(/_/g, ' '),
        value: typeof val === 'number' ? val : 0,
        fill: QUALITY_COLORS[key] || '#6366f1',
      }))
    : [];

  // SHAP / explainability
  const shapData = data?.explanations?.feature_importance
    ? Object.entries(data.explanations.feature_importance)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
        .map(([feature, importance]) => ({
          feature: feature.replace(/_/g, ' '),
          importance: (importance * 100).toFixed(1),
        }))
    : [];

  // Physics vs ML comparison
  const comparisonData = data?.predictions && data?.physics_predictions
    ? Object.keys(data.predictions).map(key => ({
        metric: key.replace(/_/g, ' '),
        ML: typeof data.predictions[key] === 'number' ? data.predictions[key] : 0,
        Physics: typeof data.physics_predictions?.[key] === 'number' ? data.physics_predictions[key] : 0,
      }))
    : [];

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Brain}
        title="Multi-Target Prediction Engine"
        subtitle="Physics-informed ML with SHAP explainability — predict Quality, Yield, Performance & Energy simultaneously"
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Parameter Controls */}
        <motion.div
          initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
          className="xl:col-span-4 glass-card p-6 space-y-5"
        >
          <div className="flex items-center justify-between">
            <h3 className="section-title"><FlaskConical className="w-4 h-4 text-primary-400" /> Process Parameters</h3>
            <button onClick={handleReset} className="text-xs text-surface-400 hover:text-white flex items-center gap-1 transition-colors">
              <RefreshCw className="w-3 h-3" /> Reset
            </button>
          </div>

          <div className="space-y-4">
            {Object.entries(PARAM_META).map(([key, meta]) => (
              <ParamSlider
                key={key}
                name={key}
                meta={meta}
                value={params[key]}
                onChange={handleChange}
              />
            ))}
          </div>

          <button
            onClick={handlePredict}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {loading ? 'Running Prediction...' : 'Predict Batch Outcomes'}
          </button>
        </motion.div>

        {/* Results */}
        <div className="xl:col-span-8 space-y-6">
          {error && <ErrorBanner message={error} onRetry={handlePredict} />}

          {loading && <LoadingSpinner text="Running multi-target prediction with physics constraints..." />}

          {data && !loading && (
            <>
              {/* Prediction Metrics */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {predictionBars.map((p, i) => (
                  <MetricCard
                    key={p.name}
                    icon={i === 0 ? CheckCircle2 : i === 1 ? TrendingUp : i === 2 ? Sparkles : AlertTriangle}
                    label={p.name}
                    value={p.value.toFixed(2)}
                    color={['primary', 'accent', 'amber', 'rose'][i % 4]}
                    delay={i}
                  />
                ))}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Predicted Values Bar Chart */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  className="glass-card p-6"
                >
                  <h3 className="section-title mb-4"><TrendingUp className="w-4 h-4 text-accent-400" /> Predicted Values</h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={predictionBars} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} />
                      <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
                      <Bar dataKey="value" radius={[8, 8, 0, 0]} name="Predicted">
                        {predictionBars.map((entry, idx) => (
                          <Cell key={idx} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </motion.div>

                {/* Feature Importance / SHAP */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                  className="glass-card p-6"
                >
                  <h3 className="section-title mb-4"><Sparkles className="w-4 h-4 text-amber-400" /> Feature Importance (SHAP)</h3>
                  {shapData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={shapData} layout="vertical" margin={{ left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                        <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
                        <YAxis dataKey="feature" type="category" tick={{ fill: '#94a3b8', fontSize: 10 }} tickLine={false} axisLine={false} width={100} />
                        <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
                        <Bar dataKey="importance" radius={[0, 6, 6, 0]} fill="#f59e0b" name="Importance %" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-sm text-surface-500 text-center py-16">Feature importance will appear after prediction</p>
                  )}
                </motion.div>
              </div>

              {/* Physics vs ML Comparison */}
              {comparisonData.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                  className="glass-card p-6"
                >
                  <h3 className="section-title mb-4"><FlaskConical className="w-4 h-4 text-violet-400" /> ML vs Physics Model Comparison</h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <RadarChart data={comparisonData} outerRadius="70%">
                      <PolarGrid stroke="#1e293b" />
                      <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <PolarRadiusAxis tick={{ fill: '#475569', fontSize: 10 }} />
                      <Radar name="ML Model" dataKey="ML" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
                      <Radar name="Physics" dataKey="Physics" stroke="#10b981" fill="#10b981" fillOpacity={0.1} strokeWidth={2} strokeDasharray="4 4" />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
                    </RadarChart>
                  </ResponsiveContainer>
                </motion.div>
              )}

              {/* Confidence */}
              {data.confidence && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
                  className="glass-card p-6"
                >
                  <h3 className="section-title mb-4"><CheckCircle2 className="w-4 h-4 text-accent-400" /> Model Confidence</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(data.confidence).map(([key, val]) => (
                      <div key={key} className="bg-surface-800/50 rounded-xl p-4 text-center">
                        <p className="text-[10px] uppercase tracking-wider text-surface-400 mb-1">{key.replace(/_/g, ' ')}</p>
                        <p className="text-2xl font-bold text-white">{(val * 100).toFixed(1)}%</p>
                        <div className="w-full bg-surface-700 rounded-full h-1 mt-2">
                          <div
                            className="h-1 rounded-full bg-accent-500"
                            style={{ width: `${val * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </>
          )}

          {/* Empty state */}
          {!data && !loading && !error && (
            <div className="glass-card p-16 text-center">
              <Brain className="w-16 h-16 text-surface-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-surface-300">Configure & Predict</h3>
              <p className="text-sm text-surface-500 mt-1 max-w-md mx-auto">
                Adjust process parameters on the left and click "Predict Batch Outcomes" to see multi-target predictions with physics-informed ML, SHAP explainability, and confidence intervals.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
