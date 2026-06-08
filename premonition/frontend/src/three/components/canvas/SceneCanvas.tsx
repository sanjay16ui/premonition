import { Suspense, type ReactNode } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Stars } from '@react-three/drei'
import { Spinner } from '@/components/ui/Spinner'

interface SceneCanvasProps {
  children: ReactNode
  cameraPosition?: [number, number, number]
  showStars?: boolean
  className?: string
}

function SceneLoader() {
  return (
    <mesh>
      <boxGeometry args={[0.5, 0.5, 0.5]} />
      <meshStandardMaterial color="#0ea5e9" wireframe />
    </mesh>
  )
}

export function SceneCanvas({
  children,
  cameraPosition = [12, 10, 12],
  showStars = false,
  className = 'h-full w-full',
}: SceneCanvasProps) {
  return (
    <div className={`relative ${className}`}>
      <Suspense
        fallback={
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950">
            <Spinner size="lg" label="Loading 3D environment..." />
          </div>
        }
      >
        <Canvas
          shadows
          dpr={[1, 2]}
          gl={{ antialias: true, alpha: false }}
          className="bg-slate-950"
        >
          <color attach="background" args={['#020617']} />
          <fog attach="fog" args={['#020617', 20, 50]} />
          <PerspectiveCamera makeDefault position={cameraPosition} fov={50} />
          <ambientLight intensity={0.35} />
          <directionalLight position={[10, 15, 8]} intensity={1.2} castShadow />
          <pointLight position={[-8, 6, -4]} intensity={0.4} color="#0ea5e9" />
          <pointLight position={[8, 4, 8]} intensity={0.3} color="#8b5cf6" />
          {showStars && <Stars radius={80} depth={40} count={1200} factor={3} fade />}
          <Suspense fallback={<SceneLoader />}>{children}</Suspense>
          <OrbitControls
            enablePan
            enableZoom
            maxPolarAngle={Math.PI / 2.1}
            minDistance={5}
            maxDistance={35}
          />
        </Canvas>
      </Suspense>
    </div>
  )
}
