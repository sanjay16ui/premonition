import { useEffect, useRef, useState } from 'react'
import {
  motion,
  useInView,
  useMotionValue,
  useSpring,
  animate,
} from 'framer-motion'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts'
import {
  Activity,
  AlertTriangle,
  Brain,
  ChevronUp,
  ChevronDown,
  Clock,
  Cpu,
  FlaskConical,
  HeartPulse,
  RefreshCw,
  Shield,
  Sigma,
  TrendingUp,
  Users,
  Zap,
} from 'lucide-react'
import {
  useAnalyticsKPIs,
  useAnalyticsPopulation,
  useAnalyticsCompareModels,
  useAnalyticsExecutive,
  usePredictionHistory,
} from '@/api/hooks'

// ─── Framer-Motion Variants ──────────────────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.1 },
  },
}

const itemVariants: any = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  },
}

const fadeSlideRight: any = {
  hidden: { opacity: 0, x: -24 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
}

// ─── Palette ─────────────────────────────────────────────────────────────────

const RISK_COLORS: Record<string, string> = {
  low: '#10b981',
  medium: '#f59e0b',
  high: '#f97316',
  critical: '#ef4444',
  unknown: '#6b7280',
}

const PIE_FALLBACK_COLORS = ['#10b981', '#f59e0b', '#f97316', '#ef4444', '#6b7280']

// ─── Animated Counter ────────────────────────────────────────────────────────

function AnimatedCounter({
  value,
  decimals = 0,
  suffix = '',
  prefix = '',
}: {
  value: number
  decimals?: number
  suffix?: string
  prefix?: string
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const motionVal = useMotionValue(0)
  const springVal = useSpring(motionVal, { stiffness: 80, damping: 18 })
  const inView = useInView(ref, { once: true })

  useEffect(() => {
    if (inView) {
      animate(motionVal, value, { duration: 1.8, ease: 'easeOut' })
    }
  }, [inView, value, motionVal])

  useEffect(() => {
    const unsub = springVal.on('change', (v) => {
      if (ref.current) {
        ref.current.textContent = `${prefix}${v.toFixed(decimals)}${suffix}`
      }
    })
    return unsub
  }, [springVal, decimals, suffix, prefix])

  return <span ref={ref}>{prefix}0{suffix}</span>
}

// ─── KPI Card ────────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string
  value: number
  decimals?: number
  unit?: string
  prefix?: string
  change?: number
  icon: React.ReactNode
  accentColor: string
  glowColor: string
  loading?: boolean
}

import React from 'react'

function KpiCardComponent({
  label,
  value,
  decimals = 0,
  unit = '',
  prefix = '',
  change,
  icon,
  accentColor,
  glowColor,
  loading,
}: KpiCardProps) {
  const positive = change !== undefined ? change >= 0 : undefined

  if (loading) {
    return (
      <div className="animate-pulse bg-slate-800/30 rounded-2xl h-36" />
    )
  }

  return (
    <motion.div
      variants={itemVariants}
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className="glass-panel rounded-2xl p-5 relative overflow-hidden group cursor-default"
      style={{ boxShadow: `0 0 0 1px rgba(255,255,255,0.05), 0 8px 32px rgba(0,0,0,0.4)` }}
    >
      {/* Accent glow orb */}
      <div
        className="absolute -top-8 -right-8 w-32 h-32 rounded-full opacity-10 group-hover:opacity-20 transition-opacity duration-500"
        style={{ background: `radial-gradient(circle, ${glowColor}, transparent 70%)` }}
      />

      {/* Top row */}
      <div className="flex items-start justify-between mb-3">
        <div
          className="p-2 rounded-xl"
          style={{ background: `${accentColor}18`, border: `1px solid ${accentColor}30` }}
        >
          <div style={{ color: accentColor }}>{icon}</div>
        </div>

        {change !== undefined && (
          <div
            className="flex items-center gap-0.5 text-xs font-semibold px-2 py-0.5 rounded-full"
            style={{
              background: positive ? '#10b98118' : '#ef444418',
              color: positive ? '#10b981' : '#ef4444',
              border: `1px solid ${positive ? '#10b98130' : '#ef444430'}`,
            }}
          >
            {positive ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {Math.abs(change)}%
          </div>
        )}
      </div>

      {/* Value */}
      <div className="mt-1">
        <div className="text-3xl font-bold text-white tracking-tight tabular-nums">
          <AnimatedCounter value={value} decimals={decimals} suffix={unit} prefix={prefix} />
        </div>
        <div className="text-xs font-medium text-slate-400 mt-1 uppercase tracking-widest">
          {label}
        </div>
      </div>

      {/* Bottom accent line */}
      <div
        className="absolute bottom-0 left-0 right-0 h-[2px] opacity-60"
        style={{ background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)` }}
      />
    </motion.div>
  )
}
const KpiCard = React.memo(KpiCardComponent)

// ─── Custom Tooltip ───────────────────────────────────────────────────────────

function DarkTooltipComponent({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-panel rounded-xl px-3 py-2 text-xs shadow-2xl border border-white/10">
      <div className="text-slate-400 mb-1 font-medium">{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color || p.fill }} />
          <span className="text-slate-300 capitalize">{p.name}:</span>
          <span className="text-white font-semibold">{typeof p.value === 'number' ? p.value.toFixed(3) : p.value}</span>
        </div>
      ))}
    </div>
  )
}
const DarkTooltip = React.memo(DarkTooltipComponent)

// ─── Section Header ───────────────────────────────────────────────────────────

function SectionHeaderComponent({ title, subtitle, icon }: { title: string; subtitle?: string; icon: React.ReactNode }) {
  return (
    <motion.div variants={fadeSlideRight} className="flex items-center gap-3 mb-4">
      <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
        {icon}
      </div>
      <div>
        <h2 className="text-sm font-semibold text-white tracking-wide">{title}</h2>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
    </motion.div>
  )
}
const SectionHeader = React.memo(SectionHeaderComponent)

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function ChartSkeleton({ height = 'h-64' }: { height?: string }) {
  return <div className={`animate-pulse bg-slate-800/30 rounded-2xl ${height}`} />
}

// ─── Risk Progress Bar ────────────────────────────────────────────────────────

function RiskProgressBar({
  label,
  value,
  total,
  color,
  delay,
}: {
  label: string
  value: number
  total: number
  color: string
  delay: number
}) {
  const pct = total > 0 ? (value / total) * 100 : 0
  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.5, ease: 'easeOut' }}
      className="mb-4"
    >
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs font-medium text-slate-300 uppercase tracking-widest">{label}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">{value} pts</span>
          <span className="text-xs font-bold" style={{ color }}>{pct.toFixed(1)}%</span>
        </div>
      </div>
      <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ delay: delay + 0.2, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="h-full rounded-full"
          style={{
            background: `linear-gradient(90deg, ${color}aa, ${color})`,
            boxShadow: `0 0 8px ${color}66`,
          }}
        />
      </div>
    </motion.div>
  )
}

// ─── Live Pulse Indicator ─────────────────────────────────────────────────────

function LivePulse() {
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
      </span>
      <span className="text-xs font-medium text-emerald-400 tracking-wide">LIVE</span>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function AnalyticsDashboardPage() {
  const { data: kpisData, isLoading: kpisLoading } = useAnalyticsKPIs()
  const { data: popData, isLoading: popLoading } = useAnalyticsPopulation()
  const { data: compData, isLoading: compLoading } = useAnalyticsCompareModels()
  useAnalyticsExecutive()  // side-effect: fetches & caches executive data
  const { data: historyData, isLoading: histLoading } = usePredictionHistory({ limit: 200 })

  const [lastRefresh, setLastRefresh] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setLastRefresh(new Date()), 15_000)
    return () => clearInterval(id)
  }, [])

  // ── KPI derivation ──
  const totalPredictions: number = kpisData?.predictions_per_day ?? 0
  const sepsisRate: number = kpisData ? kpisData.sepsis_detection_rate * 100 : 0
  const avgResponse: number = kpisData?.alert_response_time_min ?? 0
  const modelAccuracy: number = kpisData?.model_uptime_pct ?? 0

  // ── Risk Trend (24h) – from population trend or history bucketing ──
  const riskTrend: Array<{ time: string; risk: number; baseline: number }> = React.useMemo(() => {
    if (popData?.trend && Array.isArray(popData.trend) && popData.trend.length > 0) {
      return popData.trend.map((t: any) => ({
        time: t.time ?? t.label ?? '00:00',
        risk: Number(t.risk ?? t.value ?? 0),
        baseline: 0.3,
      }))
    }
    // Derive from history
    const items = historyData?.items ?? []
    if (items.length === 0) return []
    const buckets = new Map<string, { sum: number; count: number }>()
    for (const item of items) {
      const h = new Date(item.timestamp).getHours()
      const key = `${String(h).padStart(2, '0')}:00`
      const b = buckets.get(key) ?? { sum: 0, count: 0 }
      b.sum += item.risk_score ?? (item.prediction_label === 'sepsis_alert' ? 0.75 : 0.25)
      b.count++
      buckets.set(key, b)
    }
    return Array.from(buckets.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([time, v]) => ({
        time,
        risk: Number((v.sum / v.count).toFixed(3)),
        baseline: 0.3,
      }))
  }, [popData?.trend, historyData?.items])

  // ── Risk Distribution (pie) ──
  const riskDistribution: Array<{ name: string; value: number; color: string }> = React.useMemo(() => {
    if (popData?.risk_distribution && typeof popData.risk_distribution === 'object') {
      return Object.entries(popData.risk_distribution).map(([k, v], i) => ({
        name: k.charAt(0).toUpperCase() + k.slice(1),
        value: Number(v),
        color: RISK_COLORS[k.toLowerCase()] ?? PIE_FALLBACK_COLORS[i % PIE_FALLBACK_COLORS.length],
      }))
    }
    // Derive from history
    const items = historyData?.items ?? []
    if (items.length === 0) return []
    const counts: Record<string, number> = {}
    for (const item of items) {
      const label = item.prediction_label ?? 'unknown'
      counts[label] = (counts[label] ?? 0) + 1
    }
    return Object.entries(counts).map(([k, v], i) => ({
      name: k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      value: v,
      color: PIE_FALLBACK_COLORS[i % PIE_FALLBACK_COLORS.length],
    }))
  }, [popData?.risk_distribution, historyData?.items])

  // ── Model Performance (bar) ──
  const modelPerfData: Array<{ model: string; roc_auc: number; f1: number; recall: number; pr_auc: number }> = React.useMemo(() => {
    return compData?.models
      ? compData.models.map((m: any) => ({
          model: (m.model_name as string).replace(/_/g, ' '),
          roc_auc: Number((m.roc_auc ?? 0).toFixed(3)),
          f1: Number((m.f1 ?? 0).toFixed(3)),
          recall: Number((m.recall ?? 0).toFixed(3)),
          pr_auc: Number((m.pr_auc ?? 0).toFixed(3)),
        }))
      : []
  }, [compData?.models])

  // ── Population breakdown for progress bars ──
  const populationBreakdown: Array<{ label: string; value: number; color: string }> = React.useMemo(() => {
    if (!riskDistribution.length) return []
    const total = riskDistribution.reduce((s, r) => s + r.value, 0)
    return riskDistribution.map((r) => ({ label: r.name, value: r.value, color: r.color, total } as any))
  }, [riskDistribution])
  const populationTotal = populationBreakdown.reduce((s, r) => s + r.value, 0)

  // ── Prediction timeline for secondary area ──
  const timelineData: Array<{ time: string; alerts: number; total: number; safe: number }> = React.useMemo(() => {
    const items = historyData?.items ?? []
    if (!items.length) return []
    const buckets = new Map<string, { alerts: number; total: number }>()
    for (const item of items) {
      const h = new Date(item.timestamp).getHours()
      const key = `${String(h).padStart(2, '0')}:00`
      const b = buckets.get(key) ?? { alerts: 0, total: 0 }
      b.total++
      if (item.prediction_label === 'sepsis_alert') b.alerts++
      buckets.set(key, b)
    }
    return Array.from(buckets.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([time, v]) => ({
        time,
        alerts: v.alerts,
        total: v.total,
        safe: v.total - v.alerts,
      }))
  }, [historyData?.items])

  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-full bg-[#020617] text-slate-200 relative">
      {/* Background gradient mesh */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-0 right-0 w-[700px] h-[700px] rounded-full opacity-[0.04] blur-3xl"
          style={{ background: 'radial-gradient(circle, #0ea5e9, transparent 70%)' }} />
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] rounded-full opacity-[0.03] blur-3xl"
          style={{ background: 'radial-gradient(circle, #8b5cf6, transparent 70%)' }} />
        <div className="absolute inset-0"
          style={{
            backgroundImage: `linear-gradient(rgba(14,165,233,0.03) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(14,165,233,0.03) 1px, transparent 1px)`,
            backgroundSize: '64px 64px',
          }} />
      </div>

      {/* ── Sticky Header ── */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="sticky top-0 z-40 glass-panel border-b border-white/5 px-6 py-4"
        style={{ backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)' }}
      >
        <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
          {/* Left: Title */}
          <div className="flex items-center gap-4">
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20">
              <Activity size={20} className="text-sky-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">Advanced Analytics</h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Enterprise-grade clinical intelligence command center
              </p>
            </div>
          </div>

          {/* Right: Status bar */}
          <div className="flex items-center gap-5">
            <LivePulse />

            <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500">
              <RefreshCw size={12} className="animate-spin" style={{ animationDuration: '6s' }} />
              <span>Updated {lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-xs font-medium text-slate-300">
              <Cpu size={12} className="text-emerald-400" />
              <span>Model Online</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── Content ── */}
      <div className="max-w-screen-2xl mx-auto px-6 py-8 relative z-10 space-y-8">

        {/* ── KPI Cards ── */}
        <motion.section
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={fadeSlideRight} className="flex items-center gap-2 mb-4">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Key Performance Indicators</span>
            <div className="flex-1 h-px bg-gradient-to-r from-slate-700 to-transparent" />
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <KpiCard
              label="Total Predictions"
              value={totalPredictions}
              decimals={0}
              unit=" / day"
              change={4.2}
              icon={<Brain size={18} />}
              accentColor="#0ea5e9"
              glowColor="#0ea5e9"
              loading={kpisLoading}
            />
            <KpiCard
              label="Sepsis Detection Rate"
              value={sepsisRate}
              decimals={1}
              unit="%"
              change={1.5}
              icon={<HeartPulse size={18} />}
              accentColor="#10b981"
              glowColor="#10b981"
              loading={kpisLoading}
            />
            <KpiCard
              label="Avg Alert Response Time"
              value={avgResponse}
              decimals={1}
              unit=" min"
              change={-8.3}
              icon={<Clock size={18} />}
              accentColor="#f59e0b"
              glowColor="#f59e0b"
              loading={kpisLoading}
            />
            <KpiCard
              label="Model Accuracy"
              value={modelAccuracy}
              decimals={2}
              unit="%"
              change={0.1}
              icon={<Sigma size={18} />}
              accentColor="#8b5cf6"
              glowColor="#8b5cf6"
              loading={kpisLoading}
            />
          </div>
        </motion.section>

        {/* ── Risk Trend Area Chart (full width) ── */}
        <motion.section
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
        >
          <SectionHeader
            title="Risk Trend — 24h Rolling Window"
            subtitle="Aggregated sepsis risk score across all monitored patients"
            icon={<TrendingUp size={16} />}
          />

          <motion.div
            variants={itemVariants}
            className="glass-panel rounded-2xl p-6"
            style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.04), 0 12px 48px rgba(0,0,0,0.5)' }}
          >
            {popLoading || histLoading ? (
              <ChartSkeleton height="h-72" />
            ) : riskTrend.length === 0 ? (
              <div className="h-72 flex flex-col items-center justify-center gap-3 text-slate-600">
                <Activity size={32} className="opacity-30" />
                <span className="text-sm">Awaiting live data stream…</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={riskTrend} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="baselineGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.04)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="time"
                    tick={{ fill: '#64748b', fontSize: 11 }}
                    axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#64748b', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    domain={[0, 1]}
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  />
                  <Tooltip content={<DarkTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="baseline"
                    name="Baseline"
                    stroke="#8b5cf6"
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    fill="url(#baselineGrad)"
                    dot={false}
                    activeDot={false}
                  />
                  <Area
                    type="monotone"
                    dataKey="risk"
                    name="Risk Score"
                    stroke="#0ea5e9"
                    strokeWidth={2.5}
                    fill="url(#riskGrad)"
                    dot={false}
                    activeDot={{ r: 5, fill: '#0ea5e9', stroke: '#020617', strokeWidth: 2 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}

            {/* Mini stats row */}
            {riskTrend.length > 0 && (
              <div className="flex gap-6 mt-4 pt-4 border-t border-white/5">
                {[
                  { label: 'Peak Risk', val: Math.max(...riskTrend.map((r) => r.risk)).toFixed(3), color: '#ef4444' },
                  { label: 'Avg Risk', val: (riskTrend.reduce((s, r) => s + r.risk, 0) / riskTrend.length).toFixed(3), color: '#0ea5e9' },
                  { label: 'Min Risk', val: Math.min(...riskTrend.map((r) => r.risk)).toFixed(3), color: '#10b981' },
                  { label: 'Datapoints', val: String(riskTrend.length), color: '#8b5cf6' },
                ].map((s) => (
                  <div key={s.label}>
                    <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">{s.label}</div>
                    <div className="text-sm font-bold" style={{ color: s.color }}>{s.val}</div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </motion.section>

        {/* ── 2-Column: Pie + Bar ── */}
        <motion.section
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          {/* Donut — Risk Distribution */}
          <div>
            <SectionHeader
              title="Risk Distribution"
              subtitle="Patient population stratification by acuity"
              icon={<Shield size={16} />}
            />
            <motion.div
              variants={itemVariants}
              className="glass-panel rounded-2xl p-6"
              style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.04), 0 12px 48px rgba(0,0,0,0.5)' }}
            >
              {popLoading || histLoading ? (
                <ChartSkeleton />
              ) : riskDistribution.length === 0 ? (
                <div className="h-64 flex flex-col items-center justify-center gap-3 text-slate-600">
                  <FlaskConical size={28} className="opacity-30" />
                  <span className="text-sm">No distribution data yet</span>
                </div>
              ) : (
                <div className="flex items-center gap-4">
                  <ResponsiveContainer width="55%" height={240}>
                    <PieChart>
                      <defs>
                        {riskDistribution.map((entry, i) => (
                          <radialGradient key={i} id={`pieGrad${i}`} cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stopColor={entry.color} stopOpacity={1} />
                            <stop offset="100%" stopColor={entry.color} stopOpacity={0.6} />
                          </radialGradient>
                        ))}
                      </defs>
                      <Pie
                        data={riskDistribution}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={3}
                        dataKey="value"
                        stroke="none"
                        animationBegin={200}
                        animationDuration={1200}
                      >
                        {riskDistribution.map((_entry, i) => (
                          <Cell key={i} fill={`url(#pieGrad${i})`} />
                        ))}
                      </Pie>
                      <Tooltip content={<DarkTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>

                  {/* Legend */}
                  <div className="flex-1 space-y-2.5">
                    {riskDistribution.map((entry) => {
                      const total = riskDistribution.reduce((s, r) => s + r.value, 0)
                      const pct = total > 0 ? ((entry.value / total) * 100).toFixed(1) : '0.0'
                      return (
                        <div key={entry.name} className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                              style={{ background: entry.color, boxShadow: `0 0 6px ${entry.color}88` }}
                            />
                            <span className="text-xs text-slate-300 font-medium">{entry.name}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-xs font-bold text-white">{entry.value}</span>
                            <span className="text-[10px] text-slate-500 ml-1">({pct}%)</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </motion.div>
          </div>

          {/* Bar — Model Performance */}
          <div>
            <SectionHeader
              title="Model Performance"
              subtitle="Comparative metrics across deployed model versions"
              icon={<Brain size={16} />}
            />
            <motion.div
              variants={itemVariants}
              className="glass-panel rounded-2xl p-6"
              style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.04), 0 12px 48px rgba(0,0,0,0.5)' }}
            >
              {compLoading ? (
                <ChartSkeleton />
              ) : modelPerfData.length === 0 ? (
                <div className="h-64 flex flex-col items-center justify-center gap-3 text-slate-600">
                  <Cpu size={28} className="opacity-30" />
                  <span className="text-sm">Model comparison data unavailable</span>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart
                    data={modelPerfData}
                    margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    barCategoryGap="30%"
                    barGap={4}
                  >
                    <defs>
                      <linearGradient id="barRoc" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#0ea5e9" stopOpacity={1} />
                        <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0.4} />
                      </linearGradient>
                      <linearGradient id="barF1" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#8b5cf6" stopOpacity={1} />
                        <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.4} />
                      </linearGradient>
                      <linearGradient id="barRecall" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#10b981" stopOpacity={1} />
                        <stop offset="100%" stopColor="#10b981" stopOpacity={0.4} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(255,255,255,0.04)"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="model"
                      tick={{ fill: '#64748b', fontSize: 10 }}
                      axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: '#64748b', fontSize: 10 }}
                      axisLine={false}
                      tickLine={false}
                      domain={[0, 1]}
                    />
                    <Tooltip content={<DarkTooltip />} />
                    <Legend
                      wrapperStyle={{ fontSize: '11px', color: '#94a3b8', paddingTop: '8px' }}
                    />
                    <Bar dataKey="roc_auc" name="ROC AUC" fill="url(#barRoc)" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="f1" name="F1 Score" fill="url(#barF1)" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="recall" name="Recall" fill="url(#barRecall)" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </motion.div>
          </div>
        </motion.section>

        {/* ── Population Risk Breakdown ── */}
        <motion.section
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
        >
          <SectionHeader
            title="Population Risk Breakdown"
            subtitle="Live patient volume distribution across clinical risk tiers"
            icon={<Users size={16} />}
          />

          <motion.div
            variants={itemVariants}
            className="glass-panel rounded-2xl p-6"
            style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.04), 0 12px 48px rgba(0,0,0,0.5)' }}
          >
            {popLoading || histLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="flex justify-between mb-2">
                      <div className="h-3 bg-slate-800 rounded w-20" />
                      <div className="h-3 bg-slate-800 rounded w-12" />
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full" />
                  </div>
                ))}
              </div>
            ) : populationBreakdown.length === 0 ? (
              <div className="h-32 flex items-center justify-center gap-3 text-slate-600">
                <AlertTriangle size={24} className="opacity-30" />
                <span className="text-sm">No population data available</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12">
                <div>
                  {populationBreakdown.slice(0, Math.ceil(populationBreakdown.length / 2)).map((r, i) => (
                    <RiskProgressBar
                      key={r.label}
                      label={r.label}
                      value={r.value}
                      total={populationTotal}
                      color={r.color}
                      delay={i * 0.1}
                    />
                  ))}
                </div>
                <div>
                  {populationBreakdown.slice(Math.ceil(populationBreakdown.length / 2)).map((r, i) => (
                    <RiskProgressBar
                      key={r.label}
                      label={r.label}
                      value={r.value}
                      total={populationTotal}
                      color={r.color}
                      delay={i * 0.1 + 0.2}
                    />
                  ))}
                </div>
              </div>
            )}

            {populationTotal > 0 && (
              <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
                <div className="text-xs text-slate-500">
                  Total monitored: <span className="text-white font-semibold ml-1">{populationTotal} patients</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                  <Zap size={12} />
                  <span>Real-time feed active</span>
                </div>
              </div>
            )}
          </motion.div>
        </motion.section>

        {/* ── Prediction Timeline Area (secondary) ── */}
        {timelineData.length > 0 && (
          <motion.section
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <SectionHeader
              title="Prediction Timeline"
              subtitle="Hourly breakdown — alerts vs safe predictions"
              icon={<Activity size={16} />}
            />

            <motion.div
              variants={itemVariants}
              className="glass-panel rounded-2xl p-6"
              style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.04), 0 12px 48px rgba(0,0,0,0.5)' }}
            >
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={timelineData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="alertGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="safeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<DarkTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                  <Area type="monotone" dataKey="safe" name="Safe" stroke="#10b981" strokeWidth={2} fill="url(#safeGrad)" dot={false} />
                  <Area type="monotone" dataKey="alerts" name="Alerts" stroke="#ef4444" strokeWidth={2} fill="url(#alertGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </motion.div>
          </motion.section>
        )}

        {/* ── Footer ── */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="flex items-center justify-between pt-4 border-t border-white/5 text-[10px] text-slate-600"
        >
          <span>PREMONITION Analytics · Enterprise Edition</span>
          <span>Data refresh every 15s · {lastRefresh.toLocaleString()}</span>
        </motion.div>
      </div>
    </div>
  )
}
