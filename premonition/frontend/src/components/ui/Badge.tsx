import type { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  color?: string
  className?: string
}

export function Badge({ children, color, className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}
      style={
        color
          ? { backgroundColor: `${color}20`, color, border: `1px solid ${color}40` }
          : undefined
      }
    >
      {children}
    </span>
  )
}
