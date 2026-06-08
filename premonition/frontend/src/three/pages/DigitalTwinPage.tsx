import { SceneCanvas } from '@/three/components/canvas/SceneCanvas'
import { SceneHUD } from '@/three/components/ui/SceneHUD'
import { DigitalTwinScene } from '@/three/scenes/DigitalTwinScene'
import { useScenePatients } from '@/three/hooks/useScenePatients'

export function DigitalTwinPage() {
  const { patients, executive, connected, isLoading, agentActions } = useScenePatients()

  return (
    <div className="relative h-screen w-full bg-slate-950 overflow-hidden">
      <SceneCanvas cameraPosition={[14, 12, 14]} showStars>
        <DigitalTwinScene patients={patients} agentActions={agentActions || []} />
      </SceneCanvas>

      <SceneHUD
        title="Hospital Digital Twin"
        subtitle="Live ICU sepsis monitoring — enterprise command view"
        connected={connected}
        executive={executive}
        patientCount={patients.length}
      />

      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 z-30">
          <p className="text-slate-400">Connecting to live ICU stream...</p>
        </div>
      )}
    </div>
  )
}
