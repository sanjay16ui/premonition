import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

interface ShapPoint {
  feature: string
  value: number
}

interface ShapContributionChartProps {
  data: ShapPoint[]
  baseValue?: number
  height?: number
}

export function ShapContributionChart({
  data,
  baseValue,
  height = 300,
}: ShapContributionChartProps) {
  if (!data.length) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        SHAP values will appear after running an explanation
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
        <XAxis
          dataKey="feature"
          tick={{ fontSize: 10, angle: -30 }}
          stroke="#94a3b8"
          interval={0}
          height={60}
        />
        <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
        <Tooltip
          formatter={(v) => [Number(v).toFixed(4), 'SHAP Value']}
          contentStyle={{
            background: 'rgba(15,23,42,0.9)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8,
          }}
        />
        {baseValue !== undefined && (
          <ReferenceLine y={baseValue} stroke="#8b5cf6" strokeDasharray="5 5" label="Base" />
        )}
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.value >= 0 ? '#ef4444' : '#10b981'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
