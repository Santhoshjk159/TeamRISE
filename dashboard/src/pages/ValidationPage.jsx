import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid,
  Cell, Legend, PieChart, Pie, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import {
  ShieldCheck, DollarSign, TrendingUp, BarChart3,
  Play, RefreshCw, Award, Zap, Leaf, Target,
  FileText, ArrowRight
} from 'lucide-react';
import { SectionHeader, MetricCard, LoadingSpinner, ErrorBanner, DataTable } from '../components/ui';
import { useApi } from '../hooks/useApi';
import { calculateROI, sensitivityAnalysis, replayBatches, paretoAnalysis } from '../services/api';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

function generateROIBreakdown() {
  return [
    { category: 'Energy Savings', value: 45200, pct: 35 },
    { category: 'Quality Improvement', value: 32800, pct: 25 },
    { category: 'Yield Increase', value: 28500, pct: 22 },
    { category: 'Carbon Credits', value: 12400, pct: 10 },
    { category: 'Maintenance Reduction', value: 10600, pct: 8 },
  ];
}

function generatePaybackCurve() {
  let cumulative = -85000;
  return Array.from({ length: 24 }, (_, i) => {
    const monthly = 5200 + Math.random() * 1500 + i * 200;
    cumulative += monthly;
    return {
      month: `M${i + 1}`,
      cumulative: Math.round(cumulative),
      monthly: Math.round(monthly),
      breakeven: 0,
    };
  });
}

function generateReplayData() {
  return Array.from({ length: 20 }, (_, i) => ({
    batch: `B-${2800 + i}`,
    original_energy: 55 + Math.random() * 20,
    optimized_energy: 40 + Math.random() * 15,
    original_quality: 82 + Math.random() * 10,
    optimized_quality: 88 + Math.random() * 8,
    savings_kwh: 8 + Math.random() * 12,
    savings_pct: 10 + Math.random() * 20,
  }));
}

export default function ValidationPage() {
  const roiApi = useApi(calculateROI);
  const sensitivityApi = useApi(sensitivityAnalysis);
  const replayApi = useApi(replayBatches);
  const paretoApi = useApi(paretoAnalysis);

  const [activeTab, setActiveTab] = useState('roi');

  const roiBreakdown = useMemo(() => generateROIBreakdown(), []);
  const paybackCurve = useMemo(() => generatePaybackCurve(), []);
  const replayData = useMemo(() => generateReplayData(), []);

  const handleROI = () => {
    roiApi.execute({
      baseline_metrics: {
        avg_energy_kwh: 72,
        avg_quality_score: 84,
        avg_yield: 87,
        avg_co2_kg: 28,
      },
      optimized_metrics: {
        avg_energy_kwh: 58,
        avg_quality_score: 93,
        avg_yield: 92,
        avg_co2_kg: 18,
      },
    });
  };

  const handleReplay = () => {
    replayApi.execute({
      n_batches: 20,
      scenario: 'optimized',
    });
  };

  const handleSensitivity = () => {
    sensitivityApi.execute({
      variable: 'energy_price',
      range: [0.05, 0.15],
      steps: 10,
    });
  };

  const roi = roiApi.data;

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={ShieldCheck}
        title="Validation & ROI Analysis"
        subtitle="Demonstrate business impact with batch replay, ROI calculation, sensitivity analysis, and Pareto validation"
      />

      {/* Tabs */}
      <div className="flex gap-2">
        {[
          { id: 'roi', label: 'ROI Calculator', icon: DollarSign },
          { id: 'replay', label: 'Batch Replay', icon: Play },
          { id: 'sensitivity', label: 'Sensitivity', icon: BarChart3 },
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

      {/* ROI Tab */}
      {activeTab === 'roi' && (
        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="section-title"><DollarSign className="w-4 h-4 text-accent-400" /> Calculate System ROI</h3>
              <button onClick={handleROI} disabled={roiApi.loading}
                className="btn-primary flex items-center gap-2">
                {roiApi.loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                Calculate
              </button>
            </div>

            {/* Baseline vs Optimized Comparison */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-surface-800/50 rounded-xl p-4 space-y-2">
                <p className="text-xs font-semibold text-red-400 uppercase tracking-wider">Baseline</p>
                {[
                  { label: 'Energy', value: '72 kWh/batch' },
                  { label: 'Quality', value: '84%' },
                  { label: 'Yield', value: '87%' },
                  { label: 'CO₂', value: '28 kg/batch' },
                ].map(item => (
                  <div key={item.label} className="flex justify-between text-xs">
                    <span className="text-surface-400">{item.label}</span>
                    <span className="text-surface-300 font-mono">{item.value}</span>
                  </div>
                ))}
              </div>
              <div className="bg-accent-500/5 border border-accent-500/20 rounded-xl p-4 space-y-2">
                <p className="text-xs font-semibold text-accent-400 uppercase tracking-wider">Optimized</p>
                {[
                  { label: 'Energy', value: '58 kWh/batch', change: '-19.4%' },
                  { label: 'Quality', value: '93%', change: '+10.7%' },
                  { label: 'Yield', value: '92%', change: '+5.7%' },
                  { label: 'CO₂', value: '18 kg/batch', change: '-35.7%' },
                ].map(item => (
                  <div key={item.label} className="flex justify-between text-xs">
                    <span className="text-surface-400">{item.label}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-white font-mono">{item.value}</span>
                      <span className="text-accent-400 text-[10px]">{item.change}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {roiApi.error && <ErrorBanner message={roiApi.error} />}
          {roiApi.loading && <LoadingSpinner text="Calculating comprehensive ROI..." />}

          {/* KPIs Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard icon={DollarSign}  label="Annual Savings"  value="$129,500" sub="Projected" color="accent"  delay={0} />
            <MetricCard icon={Zap}         label="Energy Saved"    value="14 kWh"   sub="Per batch avg" color="primary" delay={1} />
            <MetricCard icon={Leaf}        label="CO₂ Reduced"     value="10 kg"    sub="Per batch avg" color="amber"   delay={2} />
            <MetricCard icon={TrendingUp}  label="Payback"         value="14 mo"    sub="Break-even"   color="violet"  delay={3} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* ROI Breakdown */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6">
              <h3 className="section-title mb-4"><Award className="w-4 h-4 text-amber-400" /> Savings Breakdown</h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={roiBreakdown} layout="vertical" margin={{ left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                  <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false}
                    tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
                  <YAxis dataKey="category" type="category" tick={{ fill: '#94a3b8', fontSize: 10 }} tickLine={false} axisLine={false} width={130} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }}
                    formatter={v => [`$${v.toLocaleString()}`, 'Savings']} />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]} name="Annual Savings ($)">
                    {roiBreakdown.map((_, idx) => (
                      <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Payback Curve */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
              className="glass-card p-6">
              <h3 className="section-title mb-4"><TrendingUp className="w-4 h-4 text-accent-400" /> Payback Timeline</h3>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={paybackCurve}>
                  <defs>
                    <linearGradient id="gPayback" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false}
                    tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }}
                    formatter={v => [`$${v.toLocaleString()}`, 'Cumulative']} />
                  <Area type="monotone" dataKey="cumulative" stroke="#10b981" fill="url(#gPayback)" strokeWidth={2} name="Cumulative ROI" />
                  <Line type="monotone" dataKey="breakeven" stroke="#64748b" strokeWidth={1} strokeDasharray="4 4" dot={false} name="Break-even" />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                </AreaChart>
              </ResponsiveContainer>
            </motion.div>
          </div>

          {/* ROI API Result */}
          {roi && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
              className="glass-card p-6">
              <h3 className="section-title mb-4"><FileText className="w-4 h-4 text-primary-400" /> Executive Summary</h3>
              {roi.executive_summary ? (
                <div className="bg-surface-800/50 rounded-xl p-4">
                  <pre className="text-xs text-surface-300 font-mono whitespace-pre-wrap">{JSON.stringify(roi.executive_summary, null, 2)}</pre>
                </div>
              ) : (
                <div className="bg-surface-800/50 rounded-xl p-4">
                  <pre className="text-xs text-surface-300 font-mono whitespace-pre-wrap">{JSON.stringify(roi, null, 2)}</pre>
                </div>
              )}
            </motion.div>
          )}
        </div>
      )}

      {/* Replay Tab */}
      {activeTab === 'replay' && (
        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="section-title"><Play className="w-4 h-4 text-violet-400" /> Historical Batch Replay</h3>
                <p className="text-sm text-surface-400 mt-1">
                  Replay historical batches through the optimization engine to quantify improvement potential.
                </p>
              </div>
              <button onClick={handleReplay} disabled={replayApi.loading}
                className="btn-primary flex items-center gap-2">
                {replayApi.loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Replay 20 Batches
              </button>
            </div>
          </div>

          {replayApi.loading && <LoadingSpinner text="Replaying historical batches..." />}
          {replayApi.error && <ErrorBanner message={replayApi.error} />}

          {/* Replay Visualization */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6">
            <h3 className="section-title mb-4"><BarChart3 className="w-4 h-4 text-cyan-400" /> Original vs Optimized Energy</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={replayData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="batch" tick={{ fill: '#64748b', fontSize: 9 }} tickLine={false} axisLine={false} angle={-45} textAnchor="end" height={60} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
                <Bar dataKey="original_energy" fill="#ef4444" name="Original (kWh)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="optimized_energy" fill="#10b981" name="Optimized (kWh)" radius={[4, 4, 0, 0]} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          <div className="glass-card p-6">
            <h3 className="section-title mb-4"><Target className="w-4 h-4 text-accent-400" /> Savings Per Batch</h3>
            <DataTable
              columns={[
                { key: 'batch', label: 'Batch' },
                { key: 'original_energy', label: 'Original (kWh)', render: v => v.toFixed(1) },
                { key: 'optimized_energy', label: 'Optimized (kWh)', render: v => v.toFixed(1) },
                { key: 'savings_kwh', label: 'Saved (kWh)', render: v => (
                  <span className="text-accent-400 font-semibold">{v.toFixed(1)}</span>
                )},
                { key: 'savings_pct', label: 'Savings %', render: v => (
                  <span className="badge-success">{v.toFixed(1)}%</span>
                )},
              ]}
              rows={replayData}
            />
          </div>
        </div>
      )}

      {/* Sensitivity Tab */}
      {activeTab === 'sensitivity' && (
        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="section-title"><BarChart3 className="w-4 h-4 text-amber-400" /> Sensitivity Analysis</h3>
                <p className="text-sm text-surface-400 mt-1">
                  Evaluate how changes in key variables affect overall ROI. Test robustness of optimization benefits.
                </p>
              </div>
              <button onClick={handleSensitivity} disabled={sensitivityApi.loading}
                className="btn-primary flex items-center gap-2">
                {sensitivityApi.loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <BarChart3 className="w-4 h-4" />}
                Run Analysis
              </button>
            </div>
          </div>

          {sensitivityApi.loading && <LoadingSpinner text="Running sensitivity analysis..." />}
          {sensitivityApi.error && <ErrorBanner message={sensitivityApi.error} />}

          {sensitivityApi.data && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6">
              <h3 className="section-title mb-4">Results</h3>
              <div className="bg-surface-800/50 rounded-xl p-4">
                <pre className="text-xs text-surface-300 font-mono whitespace-pre-wrap">
                  {JSON.stringify(sensitivityApi.data, null, 2)}
                </pre>
              </div>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}
