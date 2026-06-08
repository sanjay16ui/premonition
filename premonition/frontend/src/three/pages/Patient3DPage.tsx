import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { SceneCanvas } from '@/three/components/canvas/SceneCanvas'
import { PatientIntelligencePanel } from '@/three/components/ui/PatientIntelligencePanel'
import { Patient3DScene } from '@/three/scenes/Patient3DScene'
import { useScenePatients } from '@/three/hooks/useScenePatients'
import { useSceneStore } from '@/three/store/sceneStore'
import { ROUTES } from '@/routes/paths'

export function Patient3DPage() {
  const { id } = useParams<{ id: string }>()
  const { patients, connected } = useScenePatients()
  const openPanel = useSceneStore((s) => s.openPanel)
  const closePanel = useSceneStore((s) => s.closePanel)
  const selectedPatient = useSceneStore((s) => s.selectedPatient)
  const panelOpen = useSceneStore((s) => s.panelOpen)

  const patient = patients.find((p) => p.patient_id === id) ?? null

  useEffect(() => {
    if (patient) openPanel(patient)
    return () => closePanel()
  }, [patient, openPanel, closePanel])

  return (
    <div className="relative h-screen w-full bg-slate-950 overflow-hidden">
      <SceneCanvas cameraPosition={[8, 6, 10]}>
        {patient ? (
          <Patient3DScene patient={patient} allPatients={patients} />
        ) : (
          <mesh position={[0, 1, 0]}>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial color="#334155" wireframe />
          </mesh>
        )}
      </SceneCanvas>

      <div className="absolute top-4 left-4 z-40">
        <Link
          to={ROUTES.digitalTwin}
          className="flex items-center gap-2 rounded-lg bg-slate-800/80 px-4 py-2 text-sm text-slate-300 hover:text-white backdrop-blur"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Digital Twin
        </Link>
      </div>

      {!patient && (
        <div className="absolute inset-0 flex items-center justify-center z-30">
          <p className="text-slate-400">Patient #{id} not found in live monitoring</p>
        </div>
      )}

      <PatientIntelligencePanel
        patient={selectedPatient ?? patient}
        open={panelOpen || !!patient}
        onClose={closePanel}
        connected={connected}
      />
    </div>
  )
}
