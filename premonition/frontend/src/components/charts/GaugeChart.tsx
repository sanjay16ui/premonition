import { useRef, useEffect } from 'react'
import { trafficLight, type AlertLevel } from '@/theme/colors'

interface GaugeChartProps {
  value: number    // 0 – 1
  label?: string
  size?: number
  level?: AlertLevel
}

export function GaugeChart({ value, label, size = 180, level }: GaugeChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const resolvedLevel: AlertLevel = level || (
    value >= 0.9 ? 'BLACK' :
    value >= 0.7 ? 'RED' :
    value >= 0.5 ? 'ORANGE' :
    value >= 0.3 ? 'YELLOW' : 'GREEN'
  )
  const tl = trafficLight[resolvedLevel]

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    canvas.width = size * dpr
    canvas.height = size * dpr
    ctx.scale(dpr, dpr)
    ctx.clearRect(0, 0, size, size)

    const cx = size / 2
    const cy = size / 2
    const radius = size / 2 - 16
    const lineWidth = 14
    const startAngle = 0.75 * Math.PI
    const endAngle = 2.25 * Math.PI
    const sweepAngle = endAngle - startAngle

    // Background arc
    ctx.beginPath()
    ctx.arc(cx, cy, radius, startAngle, endAngle)
    ctx.strokeStyle = 'rgba(255,255,255,0.08)'
    ctx.lineWidth = lineWidth
    ctx.lineCap = 'round'
    ctx.stroke()

    // Value arc
    const valAngle = startAngle + sweepAngle * Math.min(1, Math.max(0, value))
    ctx.beginPath()
    ctx.arc(cx, cy, radius, startAngle, valAngle)
    ctx.strokeStyle = tl.bg
    ctx.lineWidth = lineWidth
    ctx.lineCap = 'round'
    ctx.shadowColor = tl.glow
    ctx.shadowBlur = 12
    ctx.stroke()
    ctx.shadowBlur = 0

    // Value text
    ctx.fillStyle = '#fff'
    ctx.font = `bold ${size * 0.2}px Inter, system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(`${Math.round(value * 100)}%`, cx, cy - 4)

    // Label
    if (label) {
      ctx.fillStyle = 'rgba(148,163,184,0.8)'
      ctx.font = `${size * 0.08}px Inter, system-ui, sans-serif`
      ctx.fillText(label, cx, cy + size * 0.16)
    }
  }, [value, size, tl, label])

  return (
    <div className="flex items-center justify-center">
      <canvas
        ref={canvasRef}
        style={{ width: size, height: size }}
      />
    </div>
  )
}
