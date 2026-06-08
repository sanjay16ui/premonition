import { RISK_COLORS, RISK_LABELS, type RiskCategory } from '@/utils/risk'
import { Badge } from './Badge'

interface RiskBadgeProps {
  category: RiskCategory | string
  score?: number
}

export function RiskBadge({ category, score }: RiskBadgeProps) {
  const cat = (category in RISK_LABELS ? category : 'green') as RiskCategory
  const color = RISK_COLORS[cat]
  return (
    <Badge color={color}>
      {RISK_LABELS[cat]}
      {score !== undefined && ` (${(score * 100).toFixed(0)}%)`}
    </Badge>
  )
}
