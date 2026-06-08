import { Text } from '@react-three/drei'
import type { PatientMonitorState } from '@/api/types'
import { PatientBeds } from '../icu/PatientBeds'
import { AlertVisuals } from '../alerts/AlertVisuals'

interface MonitoringRoomProps {
  patients: PatientMonitorState[]
}

export function MonitoringRoom({ patients }: MonitoringRoomProps) {
  return (
    <group>
      <mesh position={[0, 2, -6]}>
        <boxGeometry args={[16, 4, 0.2]} />
        <meshStandardMaterial color="#0f172a" emissive="#1e3a5f" emissiveIntensity={0.15} />
      </mesh>

      {[-5, 0, 5].map((x) => (
        <mesh key={x} position={[x, 1.5, -5.8]}>
          <boxGeometry args={[3, 2, 0.1]} />
          <meshStandardMaterial color="#020617" emissive="#0ea5e9" emissiveIntensity={0.3} />
        </mesh>
      ))}

      <Text position={[0, 3.5, -5.5]} fontSize={0.35} color="#38bdf8" anchorX="center">
        PATIENT MONITORING ROOM
      </Text>

      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[14, 10]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>

      <PatientBeds patients={patients} cols={4} />
      <AlertVisuals patients={patients} />
    </group>
  )
}
