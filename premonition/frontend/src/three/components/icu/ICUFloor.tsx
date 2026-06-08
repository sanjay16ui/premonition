import { Text } from '@react-three/drei'
import type { PatientMonitorState } from '@/api/types'
import { PatientBeds } from './PatientBeds'

import type { AgentAction } from '@/api/hooks/realtime'

interface ICUFloorProps {
  patients: PatientMonitorState[]
  agentActions?: AgentAction[]
}

export function ICUFloor({ patients, agentActions = [] }: ICUFloorProps) {
  const floorW = 18
  const floorD = 14

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[floorW, floorD]} />
        <meshStandardMaterial color="#0f172a" roughness={0.9} metalness={0.1} />
      </mesh>

      <gridHelper args={[floorW, floorW, '#1e3a5f', '#0c1929']} position={[0, 0.01, 0]} />

      <mesh position={[0, 2.5, -floorD / 2 + 0.2]}>
        <boxGeometry args={[floorW, 0.15, 0.2]} />
        <meshStandardMaterial color="#1e293b" emissive="#0ea5e9" emissiveIntensity={0.1} />
      </mesh>

      <Text
        position={[0, 3.2, -floorD / 2 + 0.5]}
        fontSize={0.5}
        color="#38bdf8"
        anchorX="center"
      >
        ICU MONITORING FLOOR
      </Text>

      <PatientBeds patients={patients} cols={4} agentActions={agentActions} />

      {patients.length === 0 && (
        <Text position={[0, 1.5, 0]} fontSize={0.35} color="#64748b" anchorX="center">
          Awaiting live patient data...
        </Text>
      )}
    </group>
  )
}
