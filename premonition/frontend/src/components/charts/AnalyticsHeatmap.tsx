interface Props {
  data: number[][]
  rowLabels: string[]
  colLabels: string[]
  height?: number
}

export function AnalyticsHeatmap({ data, rowLabels, colLabels, height = 300 }: Props) {
  const max = Math.max(...data.flat(), 1)
  const cellW = Math.floor(100 / colLabels.length)

  return (
    <div style={{ height }} className="overflow-auto">
      <div className="flex gap-1">
        <div className="w-20" />
        {colLabels.map((c) => (
          <div key={c} className="text-center text-[10px] text-slate-400" style={{ width: `${cellW}%` }}>{c}</div>
        ))}
      </div>
      {data.map((row, ri) => (
        <div key={ri} className="flex items-center gap-1 mt-1">
          <div className="w-20 text-[10px] text-slate-400 truncate">{rowLabels[ri]}</div>
          {row.map((val, ci) => {
            const intensity = val / max
            return (
              <div
                key={ci}
                className="rounded-sm transition-all hover:scale-105"
                style={{
                  width: `${cellW}%`,
                  height: 28,
                  backgroundColor: `rgba(56, 189, 248, ${intensity})`,
                }}
                title={`${rowLabels[ri]} / ${colLabels[ci]}: ${val}`}
              />
            )
          })}
        </div>
      ))}
    </div>
  )
}
