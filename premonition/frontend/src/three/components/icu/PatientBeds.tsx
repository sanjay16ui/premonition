import { useRef, useMemo, useCallback } from 'react'
import { useFrame } from '@react-three/fiber'
import type { InstancedMesh } from 'three'
import * as THREE from 'three'
import type { PatientMonitorState } from '@/api/types'
import { alertLevelFromPatient, RISK_COLORS } from '@/three/utils/riskColors'
import { useSceneStore } from '@/three/store/sceneStore'

import type { AgentAction } from '@/api/hooks/realtime'
import { PatientIntelligenceHUD } from '../PatientIntelligenceHUD'

interface PatientBedsProps {
  patients: PatientMonitorState[]
  agentActions?: AgentAction[]
  cols?: number
  onBedClick?: (patient: PatientMonitorState) => void
}

const _color = new THREE.Color()
const _matrix = new THREE.Matrix4()
const _position = new THREE.Vector3()
const _quaternion = new THREE.Quaternion()
const _scale = new THREE.Vector3(1, 1, 1)

function bedPositions(count: number, cols: number): [number, number, number][] {
  const positions: [number, number, number][] = []
  const spacing = 3.2
  const rows = Math.ceil(count / cols)
  const offsetX = ((cols - 1) * spacing) / 2
  const offsetZ = ((rows - 1) * spacing) / 2
  for (let i = 0; i < count; i++) {
    const row = Math.floor(i / cols)
    const col = i % cols
    positions.push([col * spacing - offsetX, 0, row * spacing - offsetZ])
  }
  return positions
}

export function PatientBeds({ patients, agentActions = [], cols = 4, onBedClick }: PatientBedsProps) {
  const meshRef = useRef<InstancedMesh>(null)
  const glowRef = useRef<InstancedMesh>(null)
  const waveRef = useRef<InstancedMesh>(null)
  const alertPulse = useSceneStore((s) => s.alertPulse)
  const lastAlertId = useSceneStore((s) => s.lastAlertPatientId)
  const openPanel = useSceneStore((s) => s.openPanel)
  const closePanel = useSceneStore((s) => s.closePanel)
  const selectedPatient = useSceneStore((s) => s.selectedPatient)

  const positions = useMemo(() => bedPositions(patients.length || 1, cols), [patients.length, cols])

  const patientMap = useMemo(() => {
    const map = new Map<number, PatientMonitorState>()
    patients.forEach((p, i) => map.set(i, p))
    return map
  }, [patients])

  useFrame((state) => {
    if (!meshRef.current || !glowRef.current) return
    const t = state.clock.elapsedTime

    patients.forEach((patient, i) => {
      const level = alertLevelFromPatient(patient)
      const baseColor = RISK_COLORS[level]
      _color.set(baseColor)

      if (alertPulse && patient.patient_id === lastAlertId) {
        const pulse = 0.5 + 0.5 * Math.sin(t * 6)
        _color.multiplyScalar(0.7 + pulse * 0.6)
      }

      meshRef.current!.setColorAt(i, _color)

      const [x, , z] = positions[i] ?? [0, 0, 0]
      const yPulse =
        level === 'RED' || level === 'BLACK'
          ? 0.05 * Math.sin(t * 4 + i)
          : 0
      _position.set(x, 0.35 + yPulse, z)
      _matrix.compose(_position, _quaternion, _scale)
      meshRef.current!.setMatrixAt(i, _matrix)

      const glowScale = level === 'BLACK' || level === 'RED' ? 1.3 : 1.1
      _scale.set(glowScale, 0.05, glowScale)
      _position.set(x, 0.02, z)
      _matrix.compose(_position, _quaternion, _scale)
      glowRef.current!.setMatrixAt(i, _matrix)
      glowRef.current!.setColorAt(i, _color)

      // Wave propagation effect for RED/BLACK alerts
      if (waveRef.current) {
        if (level === 'RED' || level === 'BLACK') {
          const waveScale = (t * 2 + i) % 3
          const waveOpacity = Math.max(0, 1 - waveScale / 3)
          _scale.set(waveScale * 2, 0.01, waveScale * 2)
          _position.set(x, 0.05, z)
          _matrix.compose(_position, _quaternion, _scale)
          waveRef.current.setMatrixAt(i, _matrix)
          _color.set(baseColor)
          _color.multiplyScalar(waveOpacity)
          waveRef.current.setColorAt(i, _color)
        } else {
          _scale.set(0, 0, 0)
          _matrix.compose(_position, _quaternion, _scale)
          waveRef.current.setMatrixAt(i, _matrix)
        }
      }
    })

    meshRef.current.instanceMatrix.needsUpdate = true
    if (meshRef.current.instanceColor) meshRef.current.instanceColor.needsUpdate = true
    glowRef.current.instanceMatrix.needsUpdate = true
    if (glowRef.current.instanceColor) glowRef.current.instanceColor.needsUpdate = true
    if (waveRef.current) {
      waveRef.current.instanceMatrix.needsUpdate = true
      if (waveRef.current.instanceColor) waveRef.current.instanceColor.needsUpdate = true
    }
  })

  const handleClick = useCallback(
    (e: { instanceId?: number; stopPropagation: () => void }) => {
      e.stopPropagation()
      const idx = e.instanceId
      if (idx === undefined) return
      const patient = patientMap.get(idx)
      if (!patient) return
      openPanel(patient)
      onBedClick?.(patient)
    },
    [patientMap, openPanel, onBedClick],
  )

  if (patients.length === 0) return null

  return (
    <group>
      <instancedMesh
        ref={meshRef}
        args={[undefined, undefined, patients.length]}
        onClick={handleClick}
        castShadow
        receiveShadow
      >
        <boxGeometry args={[2.2, 0.5, 1.2]} />
        <meshStandardMaterial vertexColors roughness={0.4} metalness={0.3} />
      </instancedMesh>

      <instancedMesh ref={glowRef} args={[undefined, undefined, patients.length]}>
        <boxGeometry args={[2.4, 0.08, 1.4]} />
        <meshStandardMaterial
          vertexColors
          emissive="#0ea5e9"
          emissiveIntensity={0.15}
          transparent
          opacity={0.6}
        />
      </instancedMesh>

      <instancedMesh ref={waveRef} args={[undefined, undefined, patients.length]}>
        <ringGeometry args={[1, 1.1, 32]} />
        <meshBasicMaterial
          vertexColors
          transparent
          opacity={0.8}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
        />
      </instancedMesh>

      {patients.map((p, i) => {
        const [x, , z] = positions[i] ?? [0, 0, 0]
        const isSelected = selectedPatient?.patient_id === p.patient_id
        return (
          <group key={p.patient_id} position={[x, 0.7, z]}>
            <mesh>
              <boxGeometry args={[0.3, 0.15, 0.6]} />
              <meshStandardMaterial color="#e2e8f0" roughness={0.8} />
            </mesh>
            {isSelected && (
              <PatientIntelligenceHUD 
                patient={p} 
                recentActions={agentActions} 
                onClose={closePanel} 
              />
            )}
          </group>
        )
      })}
    </group>
  )
}
