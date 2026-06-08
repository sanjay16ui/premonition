import { Text } from '@react-three/drei'
import type { PatientMonitorState } from '@/api/types'
import { alertLevelFromPatient, RISK_COLORS } from '@/three/utils/riskColors'
import { MonitoringRoom } from '@/three/components/monitoring/MonitoringRoom'

interface Patient3DSceneProps {
  patient: PatientMonitorState
  allPatients: PatientMonitorState[]
}

export function Patient3DScene({ patient, allPatients }: Patient3DSceneProps) {
  const level = alertLevelFromPatient(patient)
  const color = RISK_COLORS[level]

  return (
    <group>
      <MonitoringRoom patients={allPatients} />

      <group position={[0, 2, 0]}>
        <mesh>
          <cylinderGeometry args={[1.5, 1.5, 0.1, 32]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.4} />
        </mesh>
        <Text position={[0, 1, 0]} fontSize={0.4} color="#ffffff" anchorX="center">
          FOCUS: #{patient.patient_id}
        </Text>
        <Text position={[0, 0.5, 0]} fontSize={0.25} color={color} anchorX="center">
          {(patient.risk_score * 100).toFixed(1)}% RISK
        </Text>
      </group>
    </group>
  )
}
