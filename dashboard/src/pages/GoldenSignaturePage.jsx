import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell, Legend, LineChart, Line
} from 'recharts';
import {
  Fingerprint, Award, ThumbsUp, ThumbsDown, MessageSquare,
  RefreshCw, Shield, Sparkles, History, SlidersHorizontal,
  CheckCircle, XCircle, ArrowRight
} from 'lucide-react';
import { SectionHeader, LoadingSpinner, ErrorBanner, MetricCard, StatusDot, DataTable } from '../components/ui';
import { useApi, PARAM_META } from '../hooks/useApi';
import { getCurrentSignature, getAllSignatures, approveSignature, reprioritizeTargets } from '../services/api';

const TARGET_OPTIONS = [
  { key: 'quality', label: 'Quality', color: '#6366f1' },
  { key: 'yield', label: 'Yield', color: '#10b981' },
  { key: 'performance', label: 'Performance', color: '#f59e0b' },
  { key: 'energy', label: 'Energy Efficiency', color: '#06b6d4' },
  { key: 'carbon', label: 'Low Carbon', color: '#8b5cf6' },
];

export default function GoldenSignaturePage() {
  const currentSig = useApi(getCurrentSignature);
  const allSigs = useApi(getAllSignatures);
  const approve = useApi(approveSignature);
  const reprioritize = useApi(reprioritizeTargets);

  const [feedback, setFeedback] = useState('');
  const [weights, setWeights] = useState({ quality: 0.3, yield: 0.25, performance: 0.2, energy: 0.15, carbon: 0.1 });
  const [activeTab, setActiveTab] = useState('current');

  useEffect(() => {
    currentSig.execute();
    allSigs.execute();
  }, []);

  const sig = currentSig.data;

  // Build radar from signature
  const radarData = sig?.process_parameters
    ? Object.entries(sig.process_parameters).filter(([k]) => PARAM_META[k]).map(([key, val]) => ({
        param: PARAM_META[key]?.label || key,
        value: ((val - (PARAM_META[key]?.min || 0)) / ((PARAM_META[key]?.max || 100) - (PARAM_META[key]?.min || 0))) * 100,
        raw: val,
      }))
    : [];

  // History data from all signatures
  const historyData = (allSigs.data || []).map((s, i) => ({
    version: `v${s.version || i + 1}`,
    confidence: (s.confidence_score || 0.85 + Math.random() * 0.1) * 100,
    carbon: s.carbon_intensity || 20 + Math.random() * 10,
    health: (s.asset_health_score || 0.8 + Math.random() * 0.15) * 100,
    approved: s.approved,
  }));

  const handleApprove = async (approved) => {
    if (!sig?.signature_id) return;
    await approve.execute(sig.signature_id, approved, feedback);
    setFeedback('');
    currentSig.execute();
    allSigs.execute();
  };

  const handleReprioritize = async () => {
    await reprioritize.execute(weights);
    currentSig.execute();
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        icon={Fingerprint}
        title="Golden Signature Management"
        subtitle="Human-in-the-loop optimization benchmarks — approve, reprioritize, and track signature evolution"
      />

      {/* Tabs */}
      <div className="flex gap-2">
        {['current', 'history', 'reprioritize'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              activeTab === tab
                ? 'bg-primary-500/20 text-primary-300 border border-primary-500/30'
                : 'bg-surface-800/50 text-surface-400 hover:text-white border border-surface-700/30'
            }`}
          >
            {tab === 'current' && <><Sparkles className="w-3.5 h-3.5 inline mr-1.5" />Current Signature</>}
            {tab === 'history' && <><History className="w-3.5 h-3.5 inline mr-1.5" />History</>}
            {tab === 'reprioritize' && <><SlidersHorizontal className="w-3.5 h-3.5 inline mr-1.5" />Reprioritize</>}
          </button>
        ))}
      </div>

      {currentSig.error && <ErrorBanner message={currentSig.error} onRetry={() => currentSig.execute()} />}

      {/* Current Signature Tab */}
      <AnimatePresence mode="wait">
        {activeTab === 'current' && (
          <motion.div key="current" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
            {currentSig.loading ? <LoadingSpinner text="Loading golden signature..." /> : sig ? (
              <>
                {/* KPI Row */}
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
                  <MetricCard icon={Award} label="Version" value={`v${sig.version || 1}`} color="primary" delay={0} />
                  <MetricCard icon={Shield} label="Confidence" value={`${((sig.confidence_score || 0) * 100).toFixed(1)}%`} color="accent" delay={1} />
                  <MetricCard icon={Fingerprint} label="Status" value={sig.approved ? 'Approved' : 'Pending'} color={sig.approved ? 'accent' : 'amber'} delay={2} />
                  <MetricCard
                    icon={Sparkles} label="Carbon Intensity"
                    value={`${(sig.carbon_intensity || 0).toFixed(1)}`}
                    sub="gCO₂/kWh" color="violet" delay={3}
                  />
                  <MetricCard
                    icon={Shield} label="Asset Health"
                    value={`${((sig.asset_health_score || 0) * 100).toFixed(0)}%`}
                    color="cyan" delay={4}
                  />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Radar */}
                  <div className="glass-card p-6">
                    <h3 className="section-title mb-4"><Sparkles className="w-4 h-4 text-amber-400" /> Parameter Profile</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <RadarChart data={radarData} outerRadius="70%">
                        <PolarGrid stroke="#1e293b" />
                        <PolarAngleAxis dataKey="param" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                        <PolarRadiusAxis tick={{ fill: '#475569', fontSize: 9 }} domain={[0, 100]} />
                        <Radar name="Golden" dataKey="value" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} strokeWidth={2} />
                        <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* HITL Approval */}
                  <div className="glass-card p-6 space-y-5">
                    <h3 className="section-title"><Shield className="w-4 h-4 text-accent-400" /> Human-in-the-Loop Review</h3>

                    {sig.scenario_tags?.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {sig.scenario_tags.map(tag => (
                          <span key={tag} className="badge-primary">{tag}</span>
                        ))}
                      </div>
                    )}

                    <div className="bg-surface-800/50 rounded-xl p-4 space-y-3">
                      <p className="text-xs text-surface-400 uppercase tracking-wider font-medium">Process Parameters</p>
                      <div className="grid grid-cols-2 gap-2">
                        {sig.process_parameters && Object.entries(sig.process_parameters).map(([k, v]) => (
                          <div key={k} className="flex justify-between text-xs">
                            <span className="text-surface-400">{PARAM_META[k]?.label || k}</span>
                            <span className="text-white font-mono">{typeof v === 'number' ? v.toFixed(1) : v} {PARAM_META[k]?.unit || ''}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <textarea
                      value={feedback}
                      onChange={e => setFeedback(e.target.value)}
                      placeholder="Enter feedback or notes for this signature..."
                      className="input-field h-20 resize-none"
                    />

                    <div className="flex gap-3">
                      <button
                        onClick={() => handleApprove(true)}
                        disabled={approve.loading}
                        className="btn-success flex-1 flex items-center justify-center gap-2"
                      >
                        <ThumbsUp className="w-4 h-4" /> Approve
                      </button>
                      <button
                        onClick={() => handleApprove(false)}
                        disabled={approve.loading}
                        className="btn-danger flex-1 flex items-center justify-center gap-2"
                      >
                        <ThumbsDown className="w-4 h-4" /> Reject
                      </button>
                    </div>

                    {approve.data && (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        className="p-3 rounded-xl bg-accent-500/10 border border-accent-500/20 text-xs text-accent-300 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" /> Decision recorded successfully
                      </motion.div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="glass-card p-16 text-center">
                <Fingerprint className="w-16 h-16 text-surface-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-surface-300">No Golden Signature Available</h3>
                <p className="text-sm text-surface-500 mt-1">Run an optimization first to generate golden signatures.</p>
              </div>
            )}
          </motion.div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <motion.div key="history" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
            {allSigs.loading ? <LoadingSpinner text="Loading signature history..." /> : (
              <>
                <div className="glass-card p-6">
                  <h3 className="section-title mb-4"><History className="w-4 h-4 text-violet-400" /> Confidence Score Evolution</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={historyData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="version" tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} />
                      <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} axisLine={false} domain={[80, 100]} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', fontSize: '12px' }} />
                      <Line type="monotone" dataKey="confidence" stroke="#6366f1" strokeWidth={2} dot={{ fill: '#6366f1', r: 4 }} name="Confidence %" />
                      <Line type="monotone" dataKey="health" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', r: 4 }} name="Asset Health %" />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="glass-card p-6">
                  <h3 className="section-title mb-4"><Award className="w-4 h-4 text-amber-400" /> All Signatures</h3>
                  <DataTable
                    columns={[
                      { key: 'version', label: 'Version' },
                      { key: 'confidence', label: 'Confidence', render: v => `${v.toFixed(1)}%` },
                      { key: 'carbon', label: 'Carbon', render: v => `${v.toFixed(1)} gCO₂` },
                      { key: 'health', label: 'Health', render: v => `${v.toFixed(0)}%` },
                      { key: 'approved', label: 'Status', render: v => (
                        <span className={v ? 'badge-success' : 'badge-warning'}>
                          {v ? 'Approved' : 'Pending'}
                        </span>
                      )},
                    ]}
                    rows={historyData}
                  />
                </div>
              </>
            )}
          </motion.div>
        )}

        {/* Reprioritize Tab */}
        {activeTab === 'reprioritize' && (
          <motion.div key="reprioritize" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
            <div className="glass-card p-6 space-y-6">
              <h3 className="section-title"><SlidersHorizontal className="w-4 h-4 text-primary-400" /> Target Weights</h3>
              <p className="text-sm text-surface-400">
                Adjust the optimization target weights to reprioritize what the golden signature should optimize for. Weights should sum to 1.0.
              </p>

              <div className="space-y-4">
                {TARGET_OPTIONS.map(t => (
                  <div key={t.key} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-surface-300 font-medium flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full" style={{ background: t.color }} />
                        {t.label}
                      </span>
                      <span className="font-mono text-white">{(weights[t.key] * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range" min={0} max={100} step={5}
                      value={weights[t.key] * 100}
                      onChange={(e) => setWeights(prev => ({ ...prev, [t.key]: parseInt(e.target.value) / 100 }))}
                      className="w-full h-1.5 bg-surface-700 rounded-full appearance-none cursor-pointer
                        [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                        [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer"
                      style={{ accentColor: t.color }}
                    />
                  </div>
                ))}
              </div>

              {/* Weight visualization */}
              <div className="bg-surface-800/50 rounded-xl p-4">
                <div className="flex h-4 rounded-full overflow-hidden">
                  {TARGET_OPTIONS.map(t => (
                    <div
                      key={t.key}
                      style={{ width: `${weights[t.key] * 100}%`, background: t.color }}
                      className="transition-all duration-300"
                      title={`${t.label}: ${(weights[t.key] * 100).toFixed(0)}%`}
                    />
                  ))}
                </div>
                <p className="text-xs text-surface-400 text-center mt-2">
                  Total: {(Object.values(weights).reduce((a, b) => a + b, 0) * 100).toFixed(0)}%
                </p>
              </div>

              <button
                onClick={handleReprioritize}
                disabled={reprioritize.loading}
                className="btn-primary flex items-center gap-2"
              >
                {reprioritize.loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                Apply New Priorities
              </button>

              {reprioritize.data && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="p-3 rounded-xl bg-primary-500/10 border border-primary-500/20 text-xs text-primary-300">
                  Targets reprioritized — new golden signature will be computed on next optimization run.
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
