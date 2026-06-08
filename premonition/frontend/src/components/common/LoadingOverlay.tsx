import { Spinner } from '@/components/ui/Spinner'

interface LoadingOverlayProps {
  label?: string
  fullScreen?: boolean
}

export function LoadingOverlay({
  label = 'Loading...',
  fullScreen,
}: LoadingOverlayProps) {
  const wrapper = fullScreen
    ? 'fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-sm'
    : 'flex items-center justify-center py-20'

  return (
    <div className={wrapper}>
      <Spinner size="lg" label={label} />
    </div>
  )
}
