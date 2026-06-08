import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { RISK_COLORS } from '@/utils/risk'

interface DataPoint {
  patient: string
  probability: number
  category: string
}

interface SepsisProbabilityChartProps {
  data: DataPoint[]
  height?: number
}

export function SepsisProbabilityChart({
  data,
  height = 280,
}: SepsisProbabilityChartProps) {
  if (!data.length) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        Run predictions to see sepsis probability by patient
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
        <XAxis
          type="number"
          domain={[0, 1]}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          stroke="#94a3b8"
          tick={{ fontSize: 11 }}
        />
        <YAxis
          type="category"
          dataKey="patient"
          width={80}
          stroke="#94a3b8"
          tick={{ fontSize: 11 }}
        />
        <Tooltip
          formatter={(v) => [`${(Number(v) * 100).toFixed(1)}%`, 'Sepsis Probability']}
          contentStyle={{
            background: 'rgba(15,23,42,0.9)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8,
          }}
        />
        <Bar dataKey="probability" radius={[0, 6, 6, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={
                RISK_COLORS[entry.category as keyof typeof RISK_COLORS] ||
                '#0ea5e9'
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
