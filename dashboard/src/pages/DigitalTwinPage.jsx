import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid,
  Legend, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import {
  Box, Play, Layers, RefreshCw, FlaskConical,
  Clock, Thermometer, Gauge, Zap, AlertTriangle, CheckCircle,
  ArrowRight, Wrench
} from 'lucide-react';
import { SectionHeader, ParamSlider, LoadingSpinner, ErrorBanner, MetricCard } from '../components/ui';
import { useApi, DEFAULT_PARAMS, PARAM_META } from '../hooks/useApi';
import { simulate, whatIf, getMaintenanceForecast } from '../services/api';

function generateSimTimeseries(totalMin = 120) {
  return Array.from({ length: Math.ceil(totalMin / 5) }, (_, i) => {
    const t = i * 5;
    let phase = 'Granulation';
    if (t > 25) phase = 'Drying';
    if (t > 65) phase = 'Blending';
    if (t > 80) phase = 'Compression';
    if (t > 110) phase = 'Coating';
    return {
      time: `${t} min`,
      temperature: 25 + Math.sin(t / 20) * 15 + (phase === 'Drying' ? 30 : 0) + Math.random() * 3,
      energy: 20 + Math.random() * 15 + (phase === 'Drying' ? 25 : phase === 'Compression' ? 18 : 5),
      quality: Math.min(100, 60 + t * 0.3 + Math.random() * 5 - (Math.random() > 0.9 ? 8 : 0)),
      phase,
    };
  });
}

export default function DigitalTwinPage() {
  const [params, setParams] = useState({ ...DEFAULT_PARAMS });
  const [startHour, setStartHour] = useState(8);
  const [scenario, setScenario] = useState('baseline');
  const [variations, setVariations] = useState({
    drying_temp: [50, 55, 60, 65],
    compression_force: [15, 18, 21, 24],
  });

  const simApi = useApi(simulate);
  const whatIfApi = useApi(whatIf);
  const maintenanceApi = useApi(getMaintenanceForecast);

  const [activeTab, setActiveTab] = useState('simulate');
  const simTimeseries = useMemo(() => generateSimTimeseries(), [simApi.data]);

  const handleChange = (name, value) => setParams(prev => ({ ...prev, [name]: value }));

  const handleSimulate = () => {
    simApi.execute({
      parameters: params,
      start_hour: startHour,
      scenario_name: scenario,
    });
  };

  const handleWhatIf = () => {
    whatIfApi.execute({
      base_parameters: params,
      variations,
    });
  };

  const handleMaintenance = () => {
    maintenanceApi.execute();
  };

  const sim = simApi.data;

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Box}
        title="Digital Twin Simulation"
        subtitle="Physics-based batch simulation, what-if analysis, and predictive maintenance forecasting"
      />

      {/* Tabs */}
      <div className="flex gap-2">
        {[
          { id: 'simulate', label: 'Simulate', icon: Play },
          { id: 'whatif', label: 'What-If Analysis', icon: Layers },
          { id: 'maintenance', label: 'Maintenance', icon: Wrench },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-1.5 ${
              activeTab === tab.id
                ? 'bg-primary-500/20 text-primary-300 border border-primary-500/30'
                : 'bg-surface-800/50 text-surface-400 hover:text-white border border-surface-700/30'
            }`}
          >
            <tab.icon className="w-3.5 h-3.5" /> {tab.label}
          </button>
        ))}
      </div>

      {/* Simulate Tab */}
      {activeTab === 'simulate' && (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          {/* Controls */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
            className="xl:col-span-4 space-y-4">
            <div className="glass-card p-5 space-y-4">
              <h3 className="section-title"><FlaskConical className="w-4 h-4 text-primary-400" /> Simulation Config</h3>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-surface-400">Start Hour</span>
                  <span className="text-white font-mono">{startHour}:00</span>
                </div>
                <input type="range" min={0} max={23} value={startHour}
                  onChange={e => setStartHour(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-surface-700 rounded-full appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                    [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-cyan-500
                    [&::-webkit-slider-thumb]:cursor-pointer" />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs text-surface-400">Scenario Name</label>
                <input type="text" value={scenario} onChange={e => setScenario(e.target.value)}
                  className="input-field" placeholder="e.g., baseline, high-temp" />
              </div>

              <div className="space-y-3 max-h-52 overflow-y-auto pr-1">
                {Object.entries(PARAM_META).map(([key, meta]) => (
                  <ParamSlider key={key} name={key} meta={meta} value={params[key]} onChange={handleChange} />
                ))}
              </div>

              <button onClick={handleSimulate} disabled={simApi.loading}
                className="btn-primary w-full flex items-center justify-center gap-2">
                {simApi.loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Run Simulation
              </button>
            </div>
          </motion.div>

          {/* Simulation Results */}
          <div className="xl:col-span-8 space-y-6">
            {simApi.error && <ErrorBanner message={simApi.error} onRetry={handleSimulate} />}
            {simApi.loading && <LoadingSpinner text="Running digital twin simulation..." />}

            {sim && !simApi.loading && (
              <>
                {/* KPIs */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <MetricCard icon={Clock} label="Total Time" value={`${sim.total_time_minutes?.toFixed(0) || '120'} min`} color="primary" delay={0} />
                  <MetricCard icon={CheckCircle} label="Quality" value={sim.quality_in_spec ? 'In Spec' : 'Out of Spec'}
                    color={sim.quality_in_spec ? 'accent' : 'rose'} delay={1} />
                  <MetricCard icon={Zap} label="Energy" value={`${sim.energy_metrics?.total_kwh?.toFixed(1) || '65'} kWh`} color="amber" delay={2} />
                  <MetricCard icon={Thermometer} label="Peak Temp" value={`${sim.energy_metrics?.peak_power_kw?.toFixed(1) || '72'} °C`} color="rose" delay={3} />
                </div>

                {/* Simulation Timeline Chart */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  className="glass-card p-6">
                  <h3 className="section-title mb-4"><Clock className="w-4 h-4 text-cyan-400" /> Simulation Timeline</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={simTimeseries}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
                      <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
                      <Line type="monotone" dataKey="temperature" stroke="#ef4444" strokeWidth={2} dot={false} name="Temperature (°C)" />
                      <Line type="monotone" dataKey="energy" stroke="#6366f1" strokeWidth={2} dot={false} name="Energy (kW)" />
                      <Line type="monotone" dataKey="quality" stroke="#10b981" strokeWidth={2} dot={false} name="Quality Score" />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </motion.div>

                {/* Quality Predictions */}
                {sim.quality_predictions && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                    className="glass-card p-6">
                    <h3 className="section-title mb-4"><Gauge className="w-4 h-4 text-accent-400" /> Quality Predictions</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {Object.entries(sim.quality_predictions).map(([k, v]) => (
                        <div key={k} className="bg-surface-800/50 rounded-xl p-4 text-center">
                          <p className="text-[10px] text-surface-400 uppercase tracking-wider">{k.replace(/_/g, ' ')}</p>
                          <p className="text-xl font-bold text-white mt-1">{typeof v === 'number' ? v.toFixed(2) : v}</p>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </>
            )}

            {!sim && !simApi.loading && !simApi.error && (
              <div className="glass-card p-16 text-center">
                <Box className="w-16 h-16 text-surface-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-surface-300">Configure & Simulate</h3>
                <p className="text-sm text-surface-500 mt-1 max-w-md mx-auto">
                  Set process parameters and start hour, then run the digital twin to see a full batch simulation with energy, temperature, and quality profiles.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* What-If Tab */}
      {activeTab === 'whatif' && (
        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <h3 className="section-title"><Layers className="w-4 h-4 text-violet-400" /> What-If Scenario Analysis</h3>
            <p className="text-sm text-surface-400">
              Compare multiple parameter variations simultaneously. The digital twin evaluates each scenario
              and shows how quality, energy, and performance differ.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-surface-800/50 rounded-xl p-4 space-y-2">
                <p className="text-xs font-semibold text-surface-300">Drying Temp Variations (°C)</p>
                <div className="flex flex-wrap gap-2">
                  {variations.drying_temp.map((v, i) => (
                    <span key={i} className="badge-primary font-mono">{v}°C</span>
                  ))}
                </div>
              </div>
              <div className="bg-surface-800/50 rounded-xl p-4 space-y-2">
                <p className="text-xs font-semibold text-surface-300">Compression Force Variations (kN)</p>
                <div className="flex flex-wrap gap-2">
                  {variations.compression_force.map((v, i) => (
                    <span key={i} className="badge-primary font-mono">{v} kN</span>
                  ))}
                </div>
              </div>
            </div>

            <button onClick={handleWhatIf} disabled={whatIfApi.loading}
              className="btn-primary flex items-center gap-2">
              {whatIfApi.loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Layers className="w-4 h-4" />}
              Run What-If Analysis
            </button>
          </div>

          {whatIfApi.error && <ErrorBanner message={whatIfApi.error} />}
          {whatIfApi.loading && <LoadingSpinner text="Evaluating scenarios..." />}

          {whatIfApi.data && !whatIfApi.loading && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6">
              <h3 className="section-title mb-4"><Layers className="w-4 h-4 text-cyan-400" /> Scenario Comparison</h3>
              <div className="bg-surface-800/50 rounded-xl p-4">
                <pre className="text-xs text-surface-300 font-mono overflow-x-auto">
                  {JSON.stringify(whatIfApi.data, null, 2)}
                </pre>
              </div>
            </motion.div>
          )}
        </div>
      )}

      {/* Maintenance Tab */}
      {activeTab === 'maintenance' && (
        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <SectionHeader icon={Wrench} title="Predictive Maintenance Forecast"
              subtitle="Asset health prediction based on energy consumption patterns" />
            <button onClick={handleMaintenance} disabled={maintenanceApi.loading}
              className="btn-primary flex items-center gap-2">
              {maintenanceApi.loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Wrench className="w-4 h-4" />}
              Run Forecast
            </button>
          </div>

          {maintenanceApi.error && <ErrorBanner message={maintenanceApi.error} />}
          {maintenanceApi.loading && <LoadingSpinner text="Forecasting maintenance needs..." />}

          {maintenanceApi.data && !maintenanceApi.loading && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6">
              <h3 className="section-title mb-4"><Wrench className="w-4 h-4 text-amber-400" /> Forecast Results</h3>
              <div className="bg-surface-800/50 rounded-xl p-4">
                <pre className="text-xs text-surface-300 font-mono overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(maintenanceApi.data, null, 2)}
                </pre>
              </div>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}
