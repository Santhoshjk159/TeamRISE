import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ScatterChart, Scatter, BarChart, Bar, ResponsiveContainer,
  XAxis, YAxis, Tooltip, CartesianGrid, Cell, ZAxis, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import {
  Settings2, Target, Play, RefreshCw, Layers,
  TrendingDown, Sparkles, Award, Gauge
} from 'lucide-react';
import { SectionHeader, ParamSlider, LoadingSpinner, ErrorBanner, MetricCard } from '../components/ui';
import { useApi, DEFAULT_PARAMS, PARAM_META } from '../hooks/useApi';
import { runOptimization } from '../services/api';

const OBJECTIVES = [
  { value: 'balanced', label: 'Balanced', desc: 'All objectives equally weighted' },
  { value: 'quality', label: 'Quality First', desc: 'Prioritize product quality' },
  { value: 'energy', label: 'Energy Minimal', desc: 'Minimize energy consumption' },
  { value: 'carbon', label: 'Low Carbon', desc: 'Minimize CO₂ emissions' },
];

const METHODS = [
  { value: 'nsga2', label: 'NSGA-II', desc: 'Multi-objective genetic algorithm' },
  { value: 'bayesian', label: 'Bayesian', desc: 'Probabilistic optimization' },
  { value: 'rl', label: 'RL Policy', desc: 'Reinforcement learning agent' },
];

const PARETO_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f472b6', '#a3e635'];

export default function OptimizationPage() {
  const [params, setParams] = useState({ ...DEFAULT_PARAMS });
  const [objective, setObjective] = useState('balanced');
  const [method, setMethod] = useState('nsga2');
  const [iterations, setIterations] = useState(100);
  const { data, loading, error, execute } = useApi(runOptimization);

  const handleChange = (name, value) => setParams(prev => ({ ...prev, [name]: value }));

  const handleOptimize = () => {
    execute({
      objective,
      method,
      n_iterations: iterations,
      current_parameters: params,
      constraints: {
        max_energy_kwh: 100,
        min_quality_score: 85,
      },
    });
  };

  // Pareto front scatter data
  const paretoData = data?.pareto_front?.map((sol, i) => ({
    quality: sol.quality_score || sol.expected_quality || 85 + Math.random() * 12,
    energy: sol.energy_kwh || sol.expected_energy_kwh || 40 + Math.random() * 40,
    carbon: sol.co2_kg || sol.expected_co2_kg || 10 + Math.random() * 20,
    index: i + 1,
  })) || [];

  // Best solution params
  const bestParams = data?.best_solution?.parameters || data?.best_solution;

  // Comparison radar
  const comparisonRadar = bestParams
    ? Object.keys(PARAM_META).map(key => ({
        param: PARAM_META[key].label,
        current: ((params[key] - PARAM_META[key].min) / (PARAM_META[key].max - PARAM_META[key].min)) * 100,
        optimized: ((bestParams[key] ?? params[key]) - PARAM_META[key].min) / (PARAM_META[key].max - PARAM_META[key].min) * 100,
      }))
    : [];

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Settings2}
        title="Multi-Objective Optimization Engine"
        subtitle="NSGA-II, Bayesian & RL-based Pareto optimization for conflicting manufacturing objectives"
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
          className="xl:col-span-4 space-y-4"
        >
          {/* Objective Selection */}
          <div className="glass-card p-5 space-y-3">
            <h3 className="section-title"><Target className="w-4 h-4 text-accent-400" /> Optimization Objective</h3>
            <div className="grid grid-cols-2 gap-2">
              {OBJECTIVES.map(obj => (
                <button
                  key={obj.value}
                  onClick={() => setObjective(obj.value)}
                  className={`p-3 rounded-xl text-left transition-all duration-200 ${
                    objective === obj.value
                      ? 'bg-primary-500/20 border border-primary-500/40 text-white'
                      : 'bg-surface-800/50 border border-surface-700/30 text-surface-400 hover:text-white hover:bg-surface-800'
                  }`}
                >
                  <p className="text-xs font-semibold">{obj.label}</p>
                  <p className="text-[10px] mt-0.5 opacity-70">{obj.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Method Selection */}
          <div className="glass-card p-5 space-y-3">
            <h3 className="section-title"><Layers className="w-4 h-4 text-violet-400" /> Algorithm</h3>
            <div className="space-y-2">
              {METHODS.map(m => (
                <button
                  key={m.value}
                  onClick={() => setMethod(m.value)}
                  className={`w-full p-3 rounded-xl text-left flex items-center justify-between transition-all duration-200 ${
                    method === m.value
                      ? 'bg-primary-500/20 border border-primary-500/40 text-white'
                      : 'bg-surface-800/50 border border-surface-700/30 text-surface-400 hover:text-white hover:bg-surface-800'
                  }`}
                >
                  <div>
                    <p className="text-xs font-semibold">{m.label}</p>
                    <p className="text-[10px] mt-0.5 opacity-70">{m.desc}</p>
                  </div>
                  {method === m.value && <Sparkles className="w-3 h-3 text-primary-400" />}
                </button>
              ))}
            </div>
          </div>

          {/* Iterations */}
          <div className="glass-card p-5 space-y-3">
            <h3 className="section-title"><Gauge className="w-4 h-4 text-amber-400" /> Iterations</h3>
            <input
              type="range" min={10} max={500} step={10} value={iterations}
              onChange={(e) => setIterations(parseInt(e.target.value))}
              className="w-full h-1.5 bg-surface-700 rounded-full appearance-none cursor-pointer
                [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-amber-500
                [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:cursor-pointer"
            />
            <div className="flex justify-between text-xs text-surface-400">
              <span>10</span>
              <span className="font-mono text-white">{iterations} iters</span>
              <span>500</span>
            </div>
          </div>

          {/* Current Params */}
          <div className="glass-card p-5 space-y-3">
            <h3 className="section-title">Current Parameters</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
              {Object.entries(PARAM_META).map(([key, meta]) => (
                <ParamSlider key={key} name={key} meta={meta} value={params[key]} onChange={handleChange} />
              ))}
            </div>
          </div>

          <button
            onClick={handleOptimize}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {loading ? 'Optimizing...' : 'Run Optimization'}
          </button>
        </motion.div>

        {/* Results */}
        <div className="xl:col-span-8 space-y-6">
          {error && <ErrorBanner message={error} onRetry={handleOptimize} />}
          {loading && <LoadingSpinner text={`Running ${method.toUpperCase()} optimization with ${iterations} iterations...`} />}

          {data && !loading && (
            <>
              {/* Summary Metrics */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard icon={Award} label="Method" value={data.method?.toUpperCase() || method.toUpperCase()} color="primary" delay={0} />
                <MetricCard icon={Layers} label="Solutions" value={data.n_solutions || paretoData.length} color="violet" delay={1} />
                <MetricCard icon={Target} label="Best Quality" value={`${(data.expected_quality || 0).toFixed(1)}%`} color="accent" delay={2} />
                <MetricCard icon={TrendingDown} label="Best Energy" value={`${(data.expected_energy_kwh || 0).toFixed(1)} kWh`} color="amber" delay={3} />
              </div>

              {/* Pareto Front */}
              <motion.div
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                className="glass-card p-6"
              >
                <h3 className="section-title mb-4"><Sparkles className="w-4 h-4 text-primary-400" /> Pareto Front — Quality vs Energy</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="energy" name="Energy (kWh)" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false}
                      label={{ value: 'Energy (kWh)', position: 'bottom', fill: '#64748b', fontSize: 11 }} />
                    <YAxis dataKey="quality" name="Quality (%)" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false}
                      label={{ value: 'Quality (%)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                    <ZAxis dataKey="carbon" range={[40, 200]} name="CO₂ (kg)" />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }}
                      formatter={(val, name) => [typeof val === 'number' ? val.toFixed(2) : val, name]}
                    />
                    <Scatter name="Pareto Solutions" data={paretoData}>
                      {paretoData.map((_, idx) => (
                        <Cell key={idx} fill={PARETO_COLORS[idx % PARETO_COLORS.length]} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </motion.div>

              {/* Current vs Optimized Radar */}
              {comparisonRadar.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                  className="glass-card p-6"
                >
                  <h3 className="section-title mb-4"><Settings2 className="w-4 h-4 text-cyan-400" /> Current vs Optimized Parameters</h3>
                  <ResponsiveContainer width="100%" height={350}>
                    <RadarChart data={comparisonRadar} outerRadius="70%">
                      <PolarGrid stroke="#1e293b" />
                      <PolarAngleAxis dataKey="param" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <PolarRadiusAxis tick={{ fill: '#475569', fontSize: 9 }} domain={[0, 100]} />
                      <Radar name="Current" dataKey="current" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} strokeWidth={2} />
                      <Radar name="Optimized" dataKey="optimized" stroke="#10b981" fill="#10b981" fillOpacity={0.2} strokeWidth={2} />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
                    </RadarChart>
                  </ResponsiveContainer>
                </motion.div>
              )}

              {/* Best Solution Detail */}
              {bestParams && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                  className="glass-card p-6"
                >
                  <h3 className="section-title mb-4"><Award className="w-4 h-4 text-amber-400" /> Best Solution Parameters</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(PARAM_META).map(([key, meta]) => {
                      const optimized = bestParams[key];
                      const current = params[key];
                      const diff = optimized != null ? optimized - current : 0;
                      return (
                        <div key={key} className="bg-surface-800/50 rounded-xl p-4">
                          <p className="text-[10px] text-surface-400 uppercase tracking-wider">{meta.label}</p>
                          <p className="text-lg font-bold text-white mt-1">
                            {optimized != null ? optimized.toFixed(1) : current.toFixed(1)} <span className="text-xs text-surface-400">{meta.unit}</span>
                          </p>
                          {diff !== 0 && (
                            <p className={`text-xs mt-0.5 ${diff > 0 ? 'text-accent-400' : 'text-rose-400'}`}>
                              {diff > 0 ? '+' : ''}{diff.toFixed(1)} from current
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </>
          )}

          {!data && !loading && !error && (
            <div className="glass-card p-16 text-center">
              <Settings2 className="w-16 h-16 text-surface-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-surface-300">Configure & Optimize</h3>
              <p className="text-sm text-surface-500 mt-1 max-w-md mx-auto">
                Select your optimization objective, algorithm, and parameters. Then click "Run Optimization" to find Pareto-optimal solutions.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
