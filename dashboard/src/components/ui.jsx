import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

/* ── Metric Card ─────────────────────────────────────────── */
export function MetricCard({ icon: Icon, label, value, sub, trend, color = 'primary', delay = 0 }) {
  const palette = {
    primary:  { bg: 'bg-primary-500/10', border: 'border-primary-500/20', text: 'text-primary-400', icon: 'from-primary-500 to-primary-400' },
    accent:   { bg: 'bg-accent-500/10',  border: 'border-accent-500/20',  text: 'text-accent-400',  icon: 'from-accent-500 to-accent-400' },
    amber:    { bg: 'bg-amber-500/10',   border: 'border-amber-500/20',   text: 'text-amber-400',   icon: 'from-amber-500 to-amber-400' },
    rose:     { bg: 'bg-rose-500/10',     border: 'border-rose-500/20',    text: 'text-rose-400',    icon: 'from-rose-500 to-rose-400' },
    violet:   { bg: 'bg-violet-500/10',   border: 'border-violet-500/20',  text: 'text-violet-400',  icon: 'from-violet-500 to-violet-400' },
    cyan:     { bg: 'bg-cyan-500/10',     border: 'border-cyan-500/20',    text: 'text-cyan-400',    icon: 'from-cyan-500 to-cyan-400' },
  };
  const p = palette[color] || palette.primary;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.1, duration: 0.4 }}
      className={`glass-card-hover p-5 ${p.bg}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1">{label}</p>
          <p className="stat-value">{value}</p>
          {sub && <p className={`text-xs mt-1 ${p.text}`}>{sub}</p>}
        </div>
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${p.icon} flex items-center justify-center shadow-lg`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      {trend !== undefined && (
        <div className={`mt-3 text-xs font-medium ${trend >= 0 ? 'text-accent-400' : 'text-rose-400'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}% vs last period
        </div>
      )}
    </motion.div>
  );
}

/* ── Section Header ──────────────────────────────────────── */
export function SectionHeader({ icon: Icon, title, subtitle, action }) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-600 to-primary-500 flex items-center justify-center shadow-lg shadow-primary-500/20">
            <Icon className="w-5 h-5 text-white" />
          </div>
        )}
        <div>
          <h2 className="text-xl font-bold text-white">{title}</h2>
          {subtitle && <p className="text-sm text-surface-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

/* ── Loading Spinner ─────────────────────────────────────── */
export function LoadingSpinner({ text = 'Processing...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4">
      <div className="relative">
        <div className="w-12 h-12 rounded-full border-2 border-surface-700 animate-spin">
          <div className="absolute top-0 left-1/2 w-2 h-2 -translate-x-1/2 -translate-y-1/2 bg-primary-500 rounded-full" />
        </div>
        <Loader2 className="w-6 h-6 text-primary-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-spin" />
      </div>
      <p className="text-sm text-surface-400 animate-pulse">{text}</p>
    </div>
  );
}

/* ── Error Banner ────────────────────────────────────────── */
export function ErrorBanner({ message, onRetry }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center justify-between"
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
          <span className="text-red-400 text-lg">!</span>
        </div>
        <p className="text-sm text-red-300">{message}</p>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary text-xs">
          Retry
        </button>
      )}
    </motion.div>
  );
}

/* ── Empty State ─────────────────────────────────────────── */
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="w-16 h-16 rounded-2xl bg-surface-800 flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-surface-500" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-surface-300 mb-1">{title}</h3>
      {description && <p className="text-sm text-surface-500 max-w-md">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/* ── Param Slider ────────────────────────────────────────── */
export function ParamSlider({ name, meta, value, onChange }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span className="text-surface-400 font-medium">{meta.label}</span>
        <span className="text-white font-mono font-semibold">{value.toFixed(1)} {meta.unit}</span>
      </div>
      <input
        type="range"
        min={meta.min}
        max={meta.max}
        step={meta.step}
        value={value}
        onChange={(e) => onChange(name, parseFloat(e.target.value))}
        className="w-full h-1.5 bg-surface-700 rounded-full appearance-none cursor-pointer
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
          [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary-500
          [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-primary-500/30
          [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:transition-all
          [&::-webkit-slider-thumb]:hover:bg-primary-400 [&::-webkit-slider-thumb]:hover:scale-110"
      />
      <div className="flex justify-between text-[10px] text-surface-500">
        <span>{meta.min}</span>
        <span>{meta.max}</span>
      </div>
    </div>
  );
}

/* ── Status Dot ──────────────────────────────────────────── */
export function StatusDot({ status }) {
  const colors = {
    healthy: 'bg-accent-400',
    warning: 'bg-amber-400',
    critical: 'bg-red-400',
    online: 'bg-accent-400',
    offline: 'bg-surface-500',
  };
  return (
    <span className="relative flex h-2.5 w-2.5">
      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${colors[status] || colors.online}`} />
      <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${colors[status] || colors.online}`} />
    </span>
  );
}

/* ── Data Table ──────────────────────────────────────────── */
export function DataTable({ columns, rows, emptyText = 'No data available' }) {
  if (!rows || rows.length === 0) {
    return <p className="text-sm text-surface-500 text-center py-8">{emptyText}</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-700/50">
            {columns.map((col) => (
              <th key={col.key} className="text-left py-3 px-3 text-xs font-semibold text-surface-400 uppercase tracking-wider">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-800/50">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-surface-800/30 transition-colors">
              {columns.map((col) => (
                <td key={col.key} className="py-3 px-3 text-surface-300">
                  {col.render ? col.render(row[col.key], row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
