import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid, Cell, Legend
} from 'recharts';
import {
  Activity, AlertTriangle, CheckCircle, Bell, Shield,
  Zap, Eye, Clock, ArrowRight, X, MessageSquare
} from 'lucide-react';
import { SectionHeader, MetricCard, LoadingSpinner, ErrorBanner, StatusDot, DataTable } from '../components/ui';
import { useApi } from '../hooks/useApi';
import { monitorBatch, getAlerts, acknowledgeAlert } from '../services/api';

function generateSensorData() {
  return Object.fromEntries(
    ['temperature', 'pressure', 'vibration', 'power', 'flow_rate'].map(sensor => [
      sensor,
      Array.from({ length: 60 }, () =>
        sensor === 'temperature' ? 50 + Math.random() * 15
        : sensor === 'pressure' ? 2 + Math.random() * 1.5
        : sensor === 'vibration' ? 0.5 + Math.random() * 0.8
        : sensor === 'power' ? 30 + Math.random() * 25
        : 10 + Math.random() * 8
      ),
    ])
  );
}

function generateTimeline() {
  return Array.from({ length: 30 }, (_, i) => ({
    time: `${i * 2}m`,
    temperature: 48 + Math.sin(i / 5) * 8 + Math.random() * 3,
    power: 35 + Math.cos(i / 4) * 12 + Math.random() * 5,
    vibration: 0.4 + Math.sin(i / 3) * 0.3 + Math.random() * 0.15,
    quality: Math.min(100, 70 + i * 0.8 + Math.random() * 5),
  }));
}

export default function DecisionPage() {
  const alertsApi = useApi(getAlerts);
  const monitorApi = useApi(monitorBatch);
  const acknowledgeApi = useApi(acknowledgeAlert);

  const timeline = useMemo(() => generateTimeline(), []);

  const [batchId, setBatchId] = useState('BATCH-2847');
  const [currentPhase, setCurrentPhase] = useState('drying');

  useEffect(() => {
    alertsApi.execute().catch(() => {});
  }, []);

  const handleMonitor = () => {
    monitorApi.execute({
      batch_id: batchId,
      current_phase: currentPhase,
      sensor_data: generateSensorData(),
    });
  };

  const handleAcknowledge = async (id) => {
    await acknowledgeApi.execute(id);
    alertsApi.execute().catch(() => {});
  };

  const monitorData = monitorApi.data;

  // Demo alerts
  const demoAlerts = [
    { id: 'DEC-001', type: 'deviation', severity: 'warning', message: 'Drying temperature 3.2°C above optimal', time: '2 min ago', phase: 'Drying' },
    { id: 'DEC-002', type: 'efficiency', severity: 'info', message: 'Energy consumption 12% above golden signature', time: '5 min ago', phase: 'Compression' },
    { id: 'DEC-003', type: 'maintenance', severity: 'critical', message: 'Vibration pattern indicates bearing wear', time: '8 min ago', phase: 'Granulation' },
    { id: 'DEC-004', type: 'quality', severity: 'warning', message: 'Content uniformity trending below spec', time: '12 min ago', phase: 'Blending' },
  ];

  const severityColors = {
    critical: { badge: 'badge-danger', dot: 'critical', bg: 'bg-red-500/5 border-red-500/20' },
    warning:  { badge: 'badge-warning', dot: 'warning', bg: 'bg-amber-500/5 border-amber-500/20' },
    info:     { badge: 'badge-primary', dot: 'online', bg: 'bg-primary-500/5 border-primary-500/20' },
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Activity}
        title="Real-Time Decision Engine"
        subtitle="Live batch monitoring, deviation detection, corrective actions, and operator alerts"
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard icon={Bell}           label="Active Alerts"     value="4"       sub="2 warnings, 1 critical" color="amber" delay={0} />
        <MetricCard icon={Shield}         label="Deviations"        value="3"       sub="Last 30 min"           color="rose"   delay={1} />
        <MetricCard icon={CheckCircle}    label="Actions Taken"     value="12"      sub="This shift"            color="accent" delay={2} />
        <MetricCard icon={Eye}            label="Monitoring"        value="Active"  sub="3 batches live"        color="primary" delay={3} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Real-Time Monitor */}
        <div className="xl:col-span-8 space-y-6">
          {/* Sensor Timeline */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="section-title"><Activity className="w-4 h-4 text-cyan-400" /> Live Sensor Feed — {batchId}</h3>
              <div className="flex items-center gap-2">
                <StatusDot status="healthy" />
                <span className="text-xs text-surface-400">Streaming</span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
                <Line type="monotone" dataKey="temperature" stroke="#ef4444" strokeWidth={2} dot={false} name="Temp (°C)" />
                <Line type="monotone" dataKey="power" stroke="#6366f1" strokeWidth={2} dot={false} name="Power (kW)" />
                <Line type="monotone" dataKey="quality" stroke="#10b981" strokeWidth={2} dot={false} name="Quality" />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Monitor Batch Action */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="glass-card p-6 space-y-4">
            <h3 className="section-title"><Eye className="w-4 h-4 text-primary-400" /> Run Decision Analysis</h3>
            <div className="flex gap-3">
              <input type="text" value={batchId} onChange={e => setBatchId(e.target.value)}
                className="input-field flex-1" placeholder="Batch ID" />
              <select value={currentPhase} onChange={e => setCurrentPhase(e.target.value)}
                className="input-field w-40">
                <option value="granulation">Granulation</option>
                <option value="drying">Drying</option>
                <option value="blending">Blending</option>
                <option value="compression">Compression</option>
                <option value="coating">Coating</option>
              </select>
              <button onClick={handleMonitor} disabled={monitorApi.loading}
                className="btn-primary flex items-center gap-2 whitespace-nowrap">
                {monitorApi.loading ? <Activity className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                Analyze
              </button>
            </div>

            {monitorApi.error && <ErrorBanner message={monitorApi.error} />}
            {monitorApi.loading && <LoadingSpinner text="Analyzing batch telemetry..." />}

            {monitorData && !monitorApi.loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
                {/* Decisions */}
                {monitorData.decisions?.length > 0 && (
                  <div className="bg-primary-500/5 border border-primary-500/20 rounded-xl p-4 space-y-2">
                    <p className="text-xs font-semibold text-primary-300 uppercase tracking-wider">Decisions</p>
                    {monitorData.decisions.map((d, i) => (
                      <div key={i} className="text-xs text-surface-300 flex items-start gap-2">
                        <CheckCircle className="w-3 h-3 text-primary-400 mt-0.5 flex-shrink-0" />
                        <span>{typeof d === 'string' ? d : JSON.stringify(d)}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Corrective Actions */}
                {monitorData.corrective_actions?.length > 0 && (
                  <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 space-y-2">
                    <p className="text-xs font-semibold text-amber-300 uppercase tracking-wider">Corrective Actions</p>
                    {monitorData.corrective_actions.map((a, i) => (
                      <div key={i} className="text-xs text-surface-300 flex items-start gap-2">
                        <AlertTriangle className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
                        <span>{typeof a === 'string' ? a : JSON.stringify(a)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
          </motion.div>
        </div>

        {/* Alerts Panel */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
          className="xl:col-span-4 glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="section-title"><Bell className="w-4 h-4 text-amber-400" /> Active Alerts</h3>
            <span className="badge-warning">{demoAlerts.length} active</span>
          </div>

          <div className="space-y-3">
            {demoAlerts.map((alert) => {
              const sev = severityColors[alert.severity] || severityColors.info;
              return (
                <motion.div key={alert.id}
                  initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
                  className={`rounded-xl p-4 border ${sev.bg} space-y-2`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <StatusDot status={sev.dot} />
                      <span className="text-xs font-semibold text-white">{alert.id}</span>
                    </div>
                    <button onClick={() => handleAcknowledge(alert.id)}
                      className="text-surface-500 hover:text-white transition-colors">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <p className="text-xs text-surface-300">{alert.message}</p>
                  <div className="flex items-center justify-between">
                    <span className={sev.badge}>{alert.severity}</span>
                    <span className="text-[10px] text-surface-500 flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" /> {alert.time}
                    </span>
                  </div>
                  <div className="text-[10px] text-surface-400">Phase: {alert.phase}</div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
