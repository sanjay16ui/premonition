import { HospitalDigitalTwin } from '@/three/components/hospital/HospitalDigitalTwin'
import { AlertVisuals } from '@/three/components/alerts/AlertVisuals'
import { DataFlowPipeline } from '@/three/components/dataflow/DataFlowPipeline'
import type { PatientMonitorState } from '@/api/types'

import type { AgentAction } from '@/api/hooks/realtime'

interface DigitalTwinSceneProps {
  patients: PatientMonitorState[]
  agentActions: AgentAction[]
}

export function DigitalTwinScene({ patients, agentActions }: DigitalTwinSceneProps) {
  return (
    <>
      <HospitalDigitalTwin patients={patients} agentActions={agentActions} />
      <AlertVisuals patients={patients} />
      <DataFlowPipeline />
    </>
  )
}
