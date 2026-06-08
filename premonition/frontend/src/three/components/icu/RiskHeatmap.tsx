import { useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import type { Mesh } from 'three'
import * as THREE from 'three'
import type { PatientMonitorState } from '@/api/types'
import { alertLevelFromPatient, RISK_COLORS } from '@/three/utils/riskColors'

interface RiskHeatmapProps {
  patients: PatientMonitorState[]
  size?: number
}

export function RiskHeatmap({ patients, size = 8 }: RiskHeatmapProps) {
  const meshRef = useRef<Mesh>(null)

  const texture = useMemo(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 64
    canvas.height = 64
    const ctx = canvas.getContext('2d')!
    ctx.fillStyle = '#0f172a'
    ctx.fillRect(0, 0, 64, 64)

    patients.forEach((p, i) => {
      const color = RISK_COLORS[alertLevelFromPatient(p)]
      const x = (i % 8) * 8
      const y = Math.floor(i / 8) * 8
      ctx.fillStyle = color
      ctx.globalAlpha = 0.7
      ctx.fillRect(x, y, 7, 7)
    })

    const tex = new THREE.CanvasTexture(canvas)
    tex.needsUpdate = true
    return tex
  }, [patients])

  useFrame((state) => {
    if (meshRef.current) {
      const mat = meshRef.current.material as THREE.MeshBasicMaterial
      mat.opacity = 0.5 + 0.1 * Math.sin(state.clock.elapsedTime * 2)
    }
  })

  return (
    <group position={[size / 2 + 2, 0.05, 0]}>
      <mesh ref={meshRef} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[size, size]} />
        <meshBasicMaterial map={texture} transparent opacity={0.6} />
      </mesh>
    </group>
  )
}
