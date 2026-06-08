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
import { chartColors } from '@/theme/colors'

interface FeaturePoint {
  feature: string
  contribution: number
  direction: string
}

interface FeatureImportanceChartProps {
  data: FeaturePoint[]
  height?: number
}

export function FeatureImportanceChart({
  data,
  height = 300,
}: FeatureImportanceChartProps) {
  if (!data.length) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        Run an explanation to see feature importance
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
        <XAxis
          type="number"
          tickFormatter={(v) => `${v.toFixed(0)}%`}
          stroke="#94a3b8"
          tick={{ fontSize: 11 }}
        />
        <YAxis
          type="category"
          dataKey="feature"
          width={140}
          stroke="#94a3b8"
          tick={{ fontSize: 11 }}
        />
        <Tooltip
          formatter={(v) => [`${Number(v).toFixed(1)}%`, 'Contribution']}
          contentStyle={{
            background: 'rgba(15,23,42,0.9)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8,
          }}
        />
        <Bar dataKey="contribution" radius={[0, 6, 6, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={
                entry.direction === 'increasing'
                  ? chartColors[5]
                  : chartColors[3]
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
