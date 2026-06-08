import { Text } from '@react-three/drei'
import type { ExecutiveSummary, PatientMonitorState } from '@/api/types'
import { ExecutiveWall } from '../executive/ExecutiveWall'
import { DataFlowPipeline } from '../dataflow/DataFlowPipeline'
import { ICUFloor } from '../icu/ICUFloor'
import { AlertVisuals } from '../alerts/AlertVisuals'

interface CommandCenterRoomProps {
  patients: PatientMonitorState[]
  executive: ExecutiveSummary | null
  connected: boolean
}

export function CommandCenterRoom({
  patients,
  executive,
  connected,
}: CommandCenterRoomProps) {
  return (
    <group>
      <mesh position={[0, 5, 0]}>
        <boxGeometry args={[24, 0.3, 20]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>

      <Text position={[0, 5.5, 0]} fontSize={0.5} color="#7dd3fc" anchorX="center">
        EXECUTIVE COMMAND CENTER
      </Text>

      <group position={[0, 0, 3]}>
        <ICUFloor patients={patients} />
        <AlertVisuals patients={patients} />
      </group>

      <ExecutiveWall executive={executive} connected={connected} />
      <DataFlowPipeline />
    </group>
  )
}
