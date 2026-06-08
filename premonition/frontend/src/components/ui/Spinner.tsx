interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

const sizes = { sm: 'h-5 w-5', md: 'h-8 w-8', lg: 'h-12 w-12' }

export function Spinner({ size = 'md', label }: SpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        className={`${sizes[size]} animate-spin rounded-full border-2 border-sky-500/20 border-t-sky-500`}
        role="status"
        aria-label={label || 'Loading'}
      />
      {label && (
        <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
      )}
    </div>
  )
}
