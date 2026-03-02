import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Brain, Settings2, Fingerprint, Leaf,
  Activity, Box, ShieldCheck, ChevronLeft, ChevronRight,
  Sparkles, Zap
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/',              icon: LayoutDashboard, label: 'Dashboard',        color: 'from-primary-500 to-indigo-400' },
  { path: '/predictions',   icon: Brain,           label: 'Predictions',      color: 'from-violet-500 to-purple-400' },
  { path: '/optimization',  icon: Settings2,       label: 'Optimization',     color: 'from-blue-500 to-cyan-400' },
  { path: '/golden-signature', icon: Fingerprint,  label: 'Golden Signature', color: 'from-amber-500 to-yellow-400' },
  { path: '/carbon',        icon: Leaf,            label: 'Carbon Mgmt',      color: 'from-emerald-500 to-green-400' },
  { path: '/digital-twin',  icon: Box,             label: 'Digital Twin',     color: 'from-pink-500 to-rose-400' },
  { path: '/decisions',     icon: Activity,        label: 'Decision Engine',  color: 'from-orange-500 to-amber-400' },
  { path: '/validation',    icon: ShieldCheck,     label: 'Validation & ROI', color: 'from-teal-500 to-cyan-400' },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="h-screen sticky top-0 flex flex-col bg-surface-900/80 backdrop-blur-xl border-r border-surface-700/50 z-50"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-surface-700/50">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-primary-500/20">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="overflow-hidden whitespace-nowrap"
            >
              <div className="text-sm font-bold text-white tracking-wide">AVEVA</div>
              <div className="text-[10px] text-surface-400 font-medium tracking-widest uppercase">Manufacturing AI</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ path, icon: Icon, label, color }) => {
          const isActive = location.pathname === path;
          return (
            <NavLink key={path} to={path}>
              <motion.div
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
                className={`
                  relative flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group
                  ${isActive
                    ? 'bg-surface-800 text-white shadow-lg'
                    : 'text-surface-400 hover:text-white hover:bg-surface-800/50'
                  }
                `}
              >
                {isActive && (
                  <motion.div
                    layoutId="nav-indicator"
                    className={`absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full bg-gradient-to-b ${color}`}
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
                <div className={`
                  w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-200
                  ${isActive
                    ? `bg-gradient-to-br ${color} shadow-md`
                    : 'bg-surface-800 group-hover:bg-surface-700'
                  }
                `}>
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-surface-400 group-hover:text-white'}`} />
                </div>
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="text-sm font-medium whitespace-nowrap"
                    >
                      {label}
                    </motion.span>
                  )}
                </AnimatePresence>
                {isActive && !collapsed && (
                  <Sparkles className="w-3 h-3 text-primary-400 ml-auto animate-pulse" />
                )}
              </motion.div>
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-surface-700/50">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-xl text-surface-400 hover:text-white hover:bg-surface-800/50 transition-all duration-200"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          {!collapsed && <span className="text-xs font-medium">Collapse</span>}
        </button>
      </div>
    </motion.aside>
  );
}
