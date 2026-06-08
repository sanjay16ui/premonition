import { Pie, PieChart, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { chartColors } from '@/theme/colors'

interface Props { data: Array<{ name: string; value: number }>; height?: number; innerRadius?: number }

export function AnalyticsPieChart({ data, height = 280, innerRadius = 0 }: Props) {
  if (!data.length) return <p className="py-12 text-center text-sm text-slate-400">No data</p>
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={innerRadius} label>
          {data.map((_, i) => <Cell key={i} fill={chartColors[i % chartColors.length]} />)}
        </Pie>
        <Tooltip contentStyle={{ background: 'rgba(15,23,42,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}
