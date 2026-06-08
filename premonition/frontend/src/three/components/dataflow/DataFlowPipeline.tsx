import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import type { Mesh } from 'three'

const NODES = [
  { label: 'Patient', x: -6, color: '#38bdf8' },
  { label: 'Prediction', x: -2, color: '#8b5cf6' },
  { label: 'Explainability', x: 2, color: '#a78bfa' },
  { label: 'Alert Engine', x: 6, color: '#f97316' },
  { label: 'Dashboard', x: 10, color: '#10b981' },
]

function DataPacket({ startX, endX, y, speed, offset }: {
  startX: number; endX: number; y: number; speed: number; offset: number
}) {
  const ref = useRef<Mesh>(null)

  useFrame((state) => {
    if (!ref.current) return
    const t = ((state.clock.elapsedTime * speed + offset) % 4) / 4
    ref.current.position.x = startX + (endX - startX) * t
  })

  return (
    <mesh ref={ref} position={[startX, y, 0]}>
      <sphereGeometry args={[0.12, 8, 8]} />
      <meshStandardMaterial color="#06b6d4" emissive="#06b6d4" emissiveIntensity={0.8} />
    </mesh>
  )
}

export function DataFlowPipeline() {
  return (
    <group position={[0, 1, -4]}>
      <Text position={[2, 2, 0]} fontSize={0.35} color="#7dd3fc" anchorX="center">
        AI DATA PIPELINE
      </Text>

      {NODES.map((node, i) => (
        <group key={node.label} position={[node.x, 0, 0]}>
          <mesh>
            <boxGeometry args={[1.8, 1, 0.6]} />
            <meshStandardMaterial
              color="#1e293b"
              emissive={node.color}
              emissiveIntensity={0.2}
            />
          </mesh>
          <Text position={[0, 0, 0.35]} fontSize={0.14} color={node.color} anchorX="center">
            {node.label}
          </Text>
          {i < NODES.length - 1 && (
            <>
              <mesh position={[1.4, 0, 0]} rotation={[0, 0, 0]}>
                <boxGeometry args={[1.2, 0.04, 0.04]} />
                <meshBasicMaterial color="#334155" />
              </mesh>
              <DataPacket
                startX={node.x + 0.9}
                endX={NODES[i + 1].x - 0.9}
                y={0.2}
                speed={0.5}
                offset={i * 0.8}
              />
            </>
          )}
        </group>
      ))}
    </group>
  )
}
