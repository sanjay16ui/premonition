import { CommandCenterRoom } from '@/three/components/command/CommandCenterRoom'
import type { ExecutiveSummary, PatientMonitorState } from '@/api/types'

interface Executive3DSceneProps {
  patients: PatientMonitorState[]
  executive: ExecutiveSummary | null
  connected: boolean
}

export function Executive3DScene({ patients, executive, connected }: Executive3DSceneProps) {
  return (
    <CommandCenterRoom
      patients={patients}
      executive={executive}
      connected={connected}
    />
  )
}
