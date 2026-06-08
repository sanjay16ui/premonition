import { Text } from '@react-three/drei'
import type { ExecutiveSummary } from '@/api/types'

interface ExecutiveWallProps {
  executive: ExecutiveSummary | null
  connected: boolean
}

interface MetricProps {
  label: string
  value: string
  color?: string
  y: number
}

function Metric({ label, value, color = '#38bdf8', y }: MetricProps) {
  return (
    <group position={[0, y, 0.1]}>
      <Text fontSize={0.18} color="#64748b" anchorX="center" position={[0, 0.3, 0]}>
        {label}
      </Text>
      <Text fontSize={0.55} color={color} anchorX="center" fontWeight="bold">
        {value}
      </Text>
    </group>
  )
}

export function ExecutiveWall({ executive, connected }: ExecutiveWallProps) {
  const e = executive

  return (
    <group position={[0, 3, -8]}>
      <mesh>
        <boxGeometry args={[14, 7, 0.2]} />
        <meshStandardMaterial
          color="#0f172a"
          emissive="#0c4a6e"
          emissiveIntensity={0.2}
          roughness={0.3}
          metalness={0.5}
        />
      </mesh>

      <mesh position={[0, 0, 0.12]}>
        <planeGeometry args={[13.5, 6.5]} />
        <meshBasicMaterial color="#020617" transparent opacity={0.3} />
      </mesh>

      <Text position={[0, 2.8, 0.2]} fontSize={0.45} color="#7dd3fc" anchorX="center">
        EXECUTIVE ANALYTICS WALL
      </Text>

      <Text
        position={[5.5, 2.8, 0.2]}
        fontSize={0.15}
        color={connected ? '#10b981' : '#64748b'}
        anchorX="right"
      >
        {connected ? '● LIVE' : '○ OFFLINE'}
      </Text>

      <Metric label="ICU PATIENTS" value={String(e?.current_icu_patients ?? '—')} y={1.5} />
      <Metric
        label="HIGH RISK"
        value={String(e?.high_risk_count ?? '—')}
        color="#f97316"
        y={0.5}
      />
      <Metric
        label="CRITICAL"
        value={String(e?.critical_alert_count ?? '—')}
        color="#ef4444"
        y={-0.5}
      />
      <Metric
        label="PREDICTIONS TODAY"
        value={String(e?.predictions_today ?? '—')}
        y={-1.5}
      />

      <group position={[-4, 0, 0]}>
        <Metric label="ALERTS TODAY" value={String(e?.alerts_today ?? '—')} color="#f59e0b" y={1} />
        <Metric
          label="AVG RISK"
          value={e ? `${(e.average_risk_score * 100).toFixed(1)}%` : '—'}
          y={0}
        />
        <Metric
          label="MODEL ACCURACY"
          value={e?.model_accuracy ? `${(e.model_accuracy * 100).toFixed(1)}%` : '—'}
          color="#a78bfa"
          y={-1}
        />
      </group>

      <group position={[4, 0, 0]}>
        <Metric
          label="BLACK ALERTS"
          value={String(e?.black_alert_count ?? '—')}
          color="#6366f1"
          y={1}
        />
        <Metric
          label="UPTIME"
          value={e ? `${Math.floor(e.system_uptime_seconds / 60)}m` : '—'}
          y={0}
        />
        <Metric label="SYSTEM" value="ONLINE" color="#10b981" y={-1} />
      </group>
    </group>
  )
}
