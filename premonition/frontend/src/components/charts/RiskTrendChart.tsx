import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { chartColors } from '@/theme/colors'

interface DataPoint {
  time: string
  risk: number
}

interface RiskTrendChartProps {
  data: DataPoint[]
  height?: number
}

export function RiskTrendChart({ data, height = 280 }: RiskTrendChartProps) {
  if (!data.length) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        No risk trend data available yet
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={chartColors[0]} stopOpacity={0.3} />
            <stop offset="95%" stopColor={chartColors[0]} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
        <XAxis dataKey="time" tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <YAxis
          tick={{ fontSize: 11 }}
          stroke="#94a3b8"
          domain={[0, 1]}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
        />
        <Tooltip
          formatter={(v) => [`${(Number(v) * 100).toFixed(1)}%`, 'Risk Score']}
          contentStyle={{
            background: 'rgba(15,23,42,0.9)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8,
          }}
        />
        <Area
          type="monotone"
          dataKey="risk"
          stroke={chartColors[0]}
          fill="url(#riskGrad)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
