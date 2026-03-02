import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import {
  Leaf, Factory, Target, TrendingDown, Sun, Moon,
  Clock, Zap, Globe, Award, AlertTriangle, ArrowDown
} from 'lucide-react';
import { SectionHeader, MetricCard, LoadingSpinner, ErrorBanner } from '../components/ui';
import { useApi } from '../hooks/useApi';
import { getCarbonDashboard, getOptimalWindow, computeCarbonTarget } from '../services/api';

const COLORS = ['#10b981', '#6366f1', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

function generateHourlyCarbon() {
  return Array.from({ length: 24 }, (_, i) => {
    const gridIntensity = 300 + Math.sin((i - 6) * Math.PI / 12) * 150 + Math.random() * 30;
    return {
      hour: `${i.toString().padStart(2, '0')}:00`,
      gridIntensity: gridIntensity,
      batchCO2: gridIntensity * (0.05 + Math.random() * 0.02),
      renewable: Math.max(0, 80 - gridIntensity / 5 + Math.random() * 10),
      optimal: i >= 22 || i <= 5 || (i >= 12 && i <= 14),
    };
  });
}

function generateMonthlyTrend() {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  let baseline = 5000;
  return months.map((m, i) => {
    const actual = baseline * (1 - i * 0.012) + (Math.random() - 0.5) * 200;
    const target = baseline * (1 - i * 0.015);
    return { month: m, actual: Math.round(actual), target: Math.round(target), saved: Math.max(0, Math.round(target - actual + Math.random() * 100)) };
  });
}

function generateSourceBreakdown() {
  return [
    { name: 'Grid Electricity', value: 45 },
    { name: 'Natural Gas', value: 25 },
    { name: 'Steam', value: 15 },
    { name: 'Compressed Air', value: 10 },
    { name: 'Other', value: 5 },
  ];
}

export default function CarbonPage() {
  const dashboard = useApi(getCarbonDashboard);
  const optimalWindow = useApi(getOptimalWindow);
  const carbonTarget = useApi(computeCarbonTarget);

  const [sustainabilityWeight, setSustainabilityWeight] = useState(1.0);

  const hourlyData = useMemo(() => generateHourlyCarbon(), []);
  const monthlyData = useMemo(() => generateMonthlyTrend(), []);
  const sourceData = useMemo(() => generateSourceBreakdown(), []);

  useEffect(() => {
    dashboard.execute().catch(() => {});
    optimalWindow.execute().catch(() => {});
  }, []);

  const handleComputeTarget = () => {
    carbonTarget.execute({
      batch_energy_kwh: 65,
      grid_intensity_gco2_kwh: 400,
      sustainability_weight: sustainabilityWeight,
    });
  };

  const bestHour = hourlyData.reduce((a, b) => a.gridIntensity < b.gridIntensity ? a : b);

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Leaf}
        title="Carbon Management & Emissions Tracking"
        subtitle="Adaptive target setting, grid intensity analysis, and sustainability pathway tracking"
      />

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        <MetricCard icon={Leaf}          label="CO₂ Today"        value="847 kg"   sub="vs 920 target" color="accent"  delay={0} trend={-8.2} />
        <MetricCard icon={Target}        label="Monthly Target"   value="4,200 kg" sub="On track"      color="primary" delay={1} />
        <MetricCard icon={TrendingDown}  label="YoY Reduction"    value="14.7%"    sub="vs 15% goal"   color="amber"   delay={2} trend={-14.7} />
        <MetricCard icon={Globe}         label="Grid Intensity"   value="389"      sub="gCO₂/kWh"     color="violet"  delay={3} />
        <MetricCard icon={Sun}           label="Renewable Mix"    value="32%"      sub="Solar + Wind"  color="accent"  delay={4} trend={5.2} />
        <MetricCard icon={Award}         label="Regulatory"       value="Compliant" sub="< 200kg cap"  color="cyan"    delay={5} />
      </div>

      {/* Row 1: Grid Intensity + Optimal Window */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="lg:col-span-2 glass-card p-6"
        >
          <SectionHeader icon={Zap} title="24h Grid Carbon Intensity" subtitle="Plan production in low-carbon windows" />
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={hourlyData}>
              <defs>
                <linearGradient id="gGrid" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gRenew" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
              <Area type="monotone" dataKey="gridIntensity" stroke="#ef4444" fill="url(#gGrid)" strokeWidth={2} name="Grid Intensity (gCO₂/kWh)" />
              <Area type="monotone" dataKey="renewable" stroke="#10b981" fill="url(#gRenew)" strokeWidth={2} name="Renewable %" />
              <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Optimal Production Window */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="glass-card p-6"
        >
          <SectionHeader icon={Clock} title="Optimal Windows" subtitle="Lowest carbon production times" />
          <div className="space-y-3 mt-2">
            {[
              { time: '22:00 – 05:00', label: 'Night Shift', intensity: 'Low', color: 'accent' },
              { time: '12:00 – 14:00', label: 'Solar Peak', intensity: 'Medium', color: 'amber' },
              { time: '08:00 – 11:00', label: 'Morning', intensity: 'High', color: 'rose' },
              { time: '17:00 – 21:00', label: 'Evening Peak', intensity: 'Very High', color: 'rose' },
            ].map((w, i) => (
              <div key={i} className={`bg-surface-800/50 rounded-xl p-3 border-l-2 ${
                w.color === 'accent' ? 'border-accent-500' : w.color === 'amber' ? 'border-amber-500' : 'border-rose-500'
              }`}>
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-xs font-semibold text-white">{w.time}</p>
                    <p className="text-[10px] text-surface-400">{w.label}</p>
                  </div>
                  <span className={`badge-${w.color}`}>{w.intensity}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 bg-accent-500/10 rounded-xl p-3 border border-accent-500/20">
            <p className="text-xs text-accent-300 flex items-center gap-2">
              <Moon className="w-3.5 h-3.5" />
              Best window: {bestHour.hour} ({bestHour.gridIntensity.toFixed(0)} gCO₂/kWh)
            </p>
          </div>
        </motion.div>
      </div>

      {/* Row 2: Monthly Trend + Source Breakdown + Target Calculator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Trend */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
          className="glass-card p-6"
        >
          <SectionHeader icon={TrendingDown} title="Monthly CO₂ Trend" subtitle="Actual vs Target (kg)" />
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
              <Line type="monotone" dataKey="actual" stroke="#6366f1" strokeWidth={2} dot={{ r: 3 }} name="Actual" />
              <Line type="monotone" dataKey="target" stroke="#10b981" strokeWidth={2} strokeDasharray="4 4" dot={false} name="Target" />
              <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Source Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <SectionHeader icon={Factory} title="Emission Sources" subtitle="By energy type" />
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={sourceData} cx="50%" cy="50%" innerRadius={50} outerRadius={85} paddingAngle={3} dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {sourceData.map((_, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Adaptive Target Calculator */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
          className="glass-card p-6 space-y-5"
        >
          <SectionHeader icon={Target} title="Adaptive Target" subtitle="Dynamic carbon goal" />

          <div className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-surface-400">Sustainability Weight</span>
                <span className="text-white font-mono">{sustainabilityWeight.toFixed(1)}x</span>
              </div>
              <input
                type="range" min={10} max={200} step={10}
                value={sustainabilityWeight * 100}
                onChange={e => setSustainabilityWeight(parseInt(e.target.value) / 100)}
                className="w-full h-1.5 bg-surface-700 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                  [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent-500
                  [&::-webkit-slider-thumb]:cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-surface-500">
                <span>Conservative</span>
                <span>Aggressive</span>
              </div>
            </div>

            <button onClick={handleComputeTarget} disabled={carbonTarget.loading} className="btn-success w-full flex items-center justify-center gap-2">
              {carbonTarget.loading ? <ArrowDown className="w-4 h-4 animate-bounce" /> : <Target className="w-4 h-4" />}
              Compute Target
            </button>

            {carbonTarget.data && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className="space-y-2">
                <div className="bg-surface-800/50 rounded-xl p-4 space-y-2">
                  {[
                    { label: 'Target CO₂', value: `${carbonTarget.data.target_co2_kg?.toFixed(2)} kg` },
                    { label: 'Actual CO₂', value: `${carbonTarget.data.actual_co2_kg?.toFixed(2)} kg` },
                    { label: 'Grid Intensity', value: `${carbonTarget.data.grid_intensity?.toFixed(0)} gCO₂/kWh` },
                  ].map(item => (
                    <div key={item.label} className="flex justify-between text-xs">
                      <span className="text-surface-400">{item.label}</span>
                      <span className="text-white font-mono">{item.value}</span>
                    </div>
                  ))}
                </div>
                {carbonTarget.data.actual_co2_kg <= carbonTarget.data.target_co2_kg ? (
                  <div className="p-2 rounded-lg bg-accent-500/10 border border-accent-500/20 text-xs text-accent-300 text-center">
                    ✓ Within target — {((1 - carbonTarget.data.actual_co2_kg / carbonTarget.data.target_co2_kg) * 100).toFixed(1)}% margin
                  </div>
                ) : (
                  <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-300 text-center flex items-center justify-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Exceeds target by {((carbonTarget.data.actual_co2_kg / carbonTarget.data.target_co2_kg - 1) * 100).toFixed(1)}%
                  </div>
                )}
              </motion.div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
