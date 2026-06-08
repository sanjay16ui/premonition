import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import type { Mesh } from 'three'
import * as THREE from 'three'
import type { PatientMonitorState } from '@/api/types'
import { isCritical } from '@/three/utils/riskColors'

interface AlertVisualsProps {
  patients: PatientMonitorState[]
}

function EmergencyBeacon({ position }: { position: [number, number, number] }) {
  const ref = useRef<Mesh>(null)

  useFrame((state) => {
    if (!ref.current) return
    const pulse = 0.5 + 0.5 * Math.sin(state.clock.elapsedTime * 5)
    ref.current.scale.setScalar(0.8 + pulse * 0.4)
    const mat = ref.current.material as THREE.MeshStandardMaterial
    mat.emissiveIntensity = 0.5 + pulse * 1.5
  })

  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[0.3, 16, 16]} />
      <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={1} />
    </mesh>
  )
}

function RiskWave({ position }: { position: [number, number, number] }) {
  const ref = useRef<Mesh>(null)

  useFrame((state) => {
    if (!ref.current) return
    const t = (state.clock.elapsedTime % 2) / 2
    const scale = 1 + t * 3
    ref.current.scale.setScalar(scale)
    const mat = ref.current.material as { opacity: number }
    mat.opacity = 0.6 * (1 - t)
  })

  return (
    <mesh ref={ref} position={position} rotation={[-Math.PI / 2, 0, 0]}>
      <ringGeometry args={[0.5, 0.7, 32]} />
      <meshBasicMaterial color="#ef4444" transparent opacity={0.5} side={2} />
    </mesh>
  )
}

export function AlertVisuals({ patients }: AlertVisualsProps) {
  const critical = patients.filter(isCritical)
  const cols = 4
  const spacing = 3.2

  return (
    <group>
      {critical.map((p, i) => {
        const row = Math.floor(i / cols)
        const col = i % cols
        const rows = Math.ceil(patients.length / cols)
        const offsetX = ((cols - 1) * spacing) / 2
        const offsetZ = ((rows - 1) * spacing) / 2
        const x = col * spacing - offsetX
        const z = row * spacing - offsetZ
        const pos: [number, number, number] = [x, 1.5, z]
        return (
          <group key={p.patient_id}>
            <EmergencyBeacon position={pos} />
            <RiskWave position={[x, 0.1, z]} />
          </group>
        )
      })}
    </group>
  )
}
