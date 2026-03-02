import { useEffect, useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, XAxis,
  YAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, Legend
} from 'recharts';
import {
  Zap, Factory, Leaf, Target, Brain, TrendingUp,
  Activity, ShieldCheck, BarChart3, Gauge, Sparkles,
  ArrowUpRight, ArrowDownRight, Timer, Cpu
} from 'lucide-react';
import { MetricCard, SectionHeader, StatusDot, LoadingSpinner } from '../components/ui';
import { getHealth, getSystemSummary, getCarbonDashboard } from '../services/api';

const CHART_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

// Simulated real-time data for demonstration
function generateBatchData() {
  return Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    energy: 40 + Math.random() * 30 + (i > 6 && i < 20 ? 15 : 0),
    quality: 85 + Math.random() * 12,
    yield: 88 + Math.random() * 10,
    carbon: 15 + Math.random() * 10 + (i > 8 && i < 18 ? 5 : 0),
  }));
}

function generateRadarData() {
  return [
    { metric: 'Quality', current: 92, golden: 95 },
    { metric: 'Yield', current: 88, golden: 93 },
    { metric: 'Energy Eff.', current: 85, golden: 91 },
    { metric: 'Carbon', current: 78, golden: 88 },
    { metric: 'Reliability', current: 90, golden: 94 },
    { metric: 'Throughput', current: 87, golden: 90 },
  ];
}

function generatePhaseData() {
  return [
    { name: 'Granulation', energy: 28, time: 25 },
    { name: 'Drying', energy: 42, time: 40 },
    { name: 'Blending', energy: 15, time: 15 },
    { name: 'Compression', energy: 35, time: 30 },
    { name: 'Coating', energy: 22, time: 20 },
  ];
}

function generatePieData() {
  return [
    { name: 'Drying', value: 35 },
    { name: 'Compression', value: 25 },
    { name: 'Granulation', value: 20 },
    { name: 'Coating', value: 12 },
    { name: 'Blending', value: 8 },
  ];
}

export default function DashboardPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const batchData = useMemo(() => generateBatchData(), []);
  const radarData = useMemo(() => generateRadarData(), []);
  const phaseData = useMemo(() => generatePhaseData(), []);
  const pieData = useMemo(() => generatePieData(), []);
  const [liveEnergy, setLiveEnergy] = useState(52.3);

  useEffect(() => {
    getHealth()
      .then(r => setHealth(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Simulate live energy fluctuation
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveEnergy(prev => Math.max(30, Math.min(80, prev + (Math.random() - 0.5) * 3)));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const moduleCount = health ? Object.keys(health.modules_loaded || {}).length : 0;

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary-950 via-surface-900 to-surface-950 border border-primary-500/10 p-8"
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary-500/10 via-transparent to-transparent" />
        <div className="absolute top-4 right-4 flex items-center gap-2">
          <StatusDot status="online" />
          <span className="text-xs text-surface-400">System Online</span>
        </div>
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-primary-400" />
            <span className="text-xs font-semibold text-primary-400 uppercase tracking-widest">AI-Driven Manufacturing Intelligence</span>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Adaptive Multi-Objective Optimization
          </h1>
          <p className="text-surface-400 max-w-2xl text-sm leading-relaxed">
            Real-time batch process optimization, energy pattern analytics, golden signature management,
            and carbon emission tracking — powered by physics-informed ML and multi-objective optimization.
          </p>
          <div className="flex items-center gap-6 mt-5">
            <div className="flex items-center gap-2 text-xs text-surface-400">
              <Cpu className="w-3.5 h-3.5 text-primary-400" /> {moduleCount} Modules Active
            </div>
            <div className="flex items-center gap-2 text-xs text-surface-400">
              <Timer className="w-3.5 h-3.5 text-accent-400" /> Uptime: {health?.uptime_seconds ? `${(health.uptime_seconds / 3600).toFixed(1)}h` : '--'}
            </div>
            <div className="flex items-center gap-2 text-xs text-surface-400">
              <Activity className="w-3.5 h-3.5 text-amber-400" /> Batch #2847 In Progress
            </div>
          </div>
        </div>
      </motion.div>

      {/* KPI Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        <MetricCard icon={Gauge}       label="Live Energy"      value={`${liveEnergy.toFixed(1)} kW`}  sub="Current draw" color="primary" delay={0} trend={-4.2} />
        <MetricCard icon={Target}      label="Quality Score"    value="94.7%"      sub="Batch avg"     color="accent"  delay={1} trend={2.1} />
        <MetricCard icon={TrendingUp}  label="Yield"            value="91.2%"      sub="Output rate"   color="amber"   delay={2} trend={1.8} />
        <MetricCard icon={Leaf}        label="CO₂ Saved"        value="127 kg"     sub="This shift"    color="accent"  delay={3} trend={15.3} />
        <MetricCard icon={Factory}     label="Batches Today"    value="14"         sub="3 in progress" color="violet"  delay={4} />
        <MetricCard icon={Zap}         label="Energy Saved"     value="342 kWh"    sub="vs baseline"   color="rose"    delay={5} trend={-8.5} />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Energy + Quality Trend */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="lg:col-span-2 glass-card p-6"
        >
          <SectionHeader icon={BarChart3} title="Energy & Quality — 24h Trend" subtitle="Real-time batch telemetry" />
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={batchData} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
              <defs>
                <linearGradient id="gEnergy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gQuality" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Area type="monotone" dataKey="energy" stroke="#6366f1" fill="url(#gEnergy)" strokeWidth={2} name="Energy (kW)" />
              <Area type="monotone" dataKey="quality" stroke="#10b981" fill="url(#gQuality)" strokeWidth={2} name="Quality (%)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Radar — Current vs Golden */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass-card p-6"
        >
          <SectionHeader icon={Sparkles} title="Current vs Golden" subtitle="Multi-objective radar" />
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData} outerRadius="70%">
              <PolarGrid stroke="#1e293b" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <PolarRadiusAxis tick={{ fill: '#475569', fontSize: 10 }} domain={[0, 100]} />
              <Radar name="Current" dataKey="current" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
              <Radar name="Golden" dataKey="golden" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.1} strokeWidth={2} strokeDasharray="4 4" />
              <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Phase Energy Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
          className="glass-card p-6"
        >
          <SectionHeader icon={Zap} title="Phase Energy Consumption" subtitle="kWh per process phase" />
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={phaseData} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis dataKey="name" type="category" tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} width={90} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
              <Bar dataKey="energy" radius={[0, 6, 6, 0]} name="Energy (kWh)">
                {phaseData.map((_, idx) => (
                  <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Energy Distribution Pie */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
          className="glass-card p-6"
        >
          <SectionHeader icon={Factory} title="Energy Distribution" subtitle="By process stage" />
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={90}
                paddingAngle={3} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {pieData.map((_, idx) => (
                  <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Live Batch Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}
          className="glass-card p-6"
        >
          <SectionHeader icon={Activity} title="Active Batches" subtitle="Real-time status" />
          <div className="space-y-3">
            {[
              { id: 'B-2847', phase: 'Drying', progress: 72, status: 'healthy', energy: '48.2 kW' },
              { id: 'B-2848', phase: 'Granulation', progress: 35, status: 'healthy', energy: '32.7 kW' },
              { id: 'B-2849', phase: 'Compression', progress: 88, status: 'warning', energy: '55.1 kW' },
            ].map((batch) => (
              <div key={batch.id} className="bg-surface-800/50 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <StatusDot status={batch.status} />
                    <span className="text-sm font-semibold text-white">{batch.id}</span>
                  </div>
                  <span className="badge-primary">{batch.phase}</span>
                </div>
                <div className="w-full bg-surface-700 rounded-full h-1.5">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${batch.progress}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className={`h-1.5 rounded-full ${batch.status === 'warning' ? 'bg-amber-500' : 'bg-primary-500'}`}
                  />
                </div>
                <div className="flex justify-between text-xs text-surface-400">
                  <span>{batch.progress}% complete</span>
                  <span className="flex items-center gap-1"><Zap className="w-3 h-3" />{batch.energy}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Module Status Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
        className="glass-card p-6"
      >
        <SectionHeader icon={ShieldCheck} title="System Modules" subtitle="Health overview" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { name: 'Prediction Engine', icon: Brain, status: 'online' },
            { name: 'Optimization', icon: Target, status: 'online' },
            { name: 'Golden Signature', icon: Sparkles, status: 'online' },
            { name: 'Carbon Manager', icon: Leaf, status: 'online' },
            { name: 'Decision Engine', icon: Activity, status: 'online' },
            { name: 'Digital Twin', icon: Factory, status: 'online' },
            { name: 'Energy Analytics', icon: Zap, status: 'online' },
            { name: 'Validation', icon: ShieldCheck, status: 'online' },
          ].map((mod) => (
            <div key={mod.name} className="flex items-center gap-3 bg-surface-800/40 rounded-xl p-3">
              <div className="w-8 h-8 rounded-lg bg-surface-700/80 flex items-center justify-center flex-shrink-0">
                <mod.icon className="w-4 h-4 text-surface-300" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-white truncate">{mod.name}</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <StatusDot status={mod.status} />
                  <span className="text-[10px] text-surface-400 capitalize">{mod.status}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
