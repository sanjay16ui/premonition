import { Text } from '@react-three/drei'
import type { PatientMonitorState } from '@/api/types'
import { ICUFloor } from '../icu/ICUFloor'
import { RiskHeatmap } from '../icu/RiskHeatmap'

import type { AgentAction } from '@/api/hooks/realtime'

interface HospitalDigitalTwinProps {
  patients: PatientMonitorState[]
  agentActions: AgentAction[]
}

export function HospitalDigitalTwin({ patients, agentActions }: HospitalDigitalTwinProps) {
  return (
    <group>
      <mesh position={[0, 4, -10]}>
        <boxGeometry args={[22, 8, 0.3]} />
        <meshStandardMaterial color="#1e293b" emissive="#0c4a6e" emissiveIntensity={0.15} />
      </mesh>
      <Text position={[0, 5.5, -9.7]} fontSize={0.6} color="#7dd3fc" anchorX="center">
        PREMONITION DIGITAL TWIN
      </Text>
      <Text position={[0, 4.8, -9.7]} fontSize={0.25} color="#94a3b8" anchorX="center">
        Enterprise ICU Command Center
      </Text>

      <mesh position={[-8, 2, -5]}>
        <boxGeometry args={[4, 4, 6]} />
        <meshStandardMaterial color="#1e293b" transparent opacity={0.5} />
      </mesh>
      <Text position={[-8, 4.5, -5]} fontSize={0.2} color="#64748b" anchorX="center">
        Admin
      </Text>

      <mesh position={[8, 2, -5]}>
        <boxGeometry args={[4, 4, 6]} />
        <meshStandardMaterial color="#1e293b" transparent opacity={0.5} />
      </mesh>
      <Text position={[8, 4.5, -5]} fontSize={0.2} color="#64748b" anchorX="center">
        Labs
      </Text>

      <group position={[0, 0, 2]}>
        <ICUFloor patients={patients} agentActions={agentActions} />
        <RiskHeatmap patients={patients} />
      </group>
    </group>
  )
}
