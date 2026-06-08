import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { chartColors } from '@/theme/colors'

interface MetricRow {
  model: string
  pr_auc: number
  recall: number
  f1: number
  roc_auc: number
}

interface ModelPerformanceChartProps {
  data: MetricRow[]
  height?: number
}

export function ModelPerformanceChart({
  data,
  height = 300,
}: ModelPerformanceChartProps) {
  if (!data.length) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        Model performance metrics not available
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
        <XAxis dataKey="model" tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <YAxis domain={[0, 1]} tickFormatter={(v) => v.toFixed(2)} stroke="#94a3b8" tick={{ fontSize: 11 }} />
        <Tooltip
          formatter={(v) => Number(v).toFixed(4)}
          contentStyle={{
            background: 'rgba(15,23,42,0.9)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8,
          }}
        />
        <Legend />
        <Bar dataKey="pr_auc" name="PR-AUC" fill={chartColors[0]} radius={[4, 4, 0, 0]} />
        <Bar dataKey="recall" name="Recall" fill={chartColors[1]} radius={[4, 4, 0, 0]} />
        <Bar dataKey="f1" name="F1" fill={chartColors[3]} radius={[4, 4, 0, 0]} />
        <Bar dataKey="roc_auc" name="ROC-AUC" fill={chartColors[2]} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
