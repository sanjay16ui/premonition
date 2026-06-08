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

interface MetricPoint {
  label: string
  predictions: number
  alerts: number
  errors: number
}

interface SystemMetricsChartProps {
  data: MetricPoint[]
  height?: number
}

export function SystemMetricsChart({
  data,
  height = 280,
}: SystemMetricsChartProps) {
  if (!data.length) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        System metrics will populate as the API serves predictions
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <Tooltip
          contentStyle={{
            background: 'rgba(15,23,42,0.9)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8,
          }}
        />
        <Area
          type="monotone"
          dataKey="predictions"
          name="Predictions"
          stroke={chartColors[0]}
          fill={`${chartColors[0]}33`}
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="alerts"
          name="Alerts"
          stroke={chartColors[5]}
          fill={`${chartColors[5]}33`}
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
