import { SceneCanvas } from '@/three/components/canvas/SceneCanvas'
import { SceneHUD } from '@/three/components/ui/SceneHUD'
import { PatientIntelligencePanel } from '@/three/components/ui/PatientIntelligencePanel'
import { Executive3DScene } from '@/three/scenes/Executive3DScene'
import { useScenePatients } from '@/three/hooks/useScenePatients'
import { useSceneStore } from '@/three/store/sceneStore'

export function Executive3DPage() {
  const { patients, executive, connected } = useScenePatients()
  const panelOpen = useSceneStore((s) => s.panelOpen)
  const selectedPatient = useSceneStore((s) => s.selectedPatient)
  const closePanel = useSceneStore((s) => s.closePanel)

  return (
    <div className="relative h-screen w-full bg-slate-950 overflow-hidden">
      <SceneCanvas cameraPosition={[0, 8, 18]} showStars>
        <Executive3DScene
          patients={patients}
          executive={executive}
          connected={connected}
        />
      </SceneCanvas>

      <SceneHUD
        title="3D Executive Command Center"
        subtitle="CEO analytics wall · ICU floor · AI data pipeline"
        connected={connected}
        executive={executive}
        patientCount={patients.length}
      />

      <PatientIntelligencePanel
        patient={selectedPatient}
        open={panelOpen}
        onClose={closePanel}
        connected={connected}
      />
    </div>
  )
}
