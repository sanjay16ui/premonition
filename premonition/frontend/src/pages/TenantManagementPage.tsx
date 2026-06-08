import { useQuery } from '@tanstack/react-query'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { Badge } from '@/components/ui/Badge'
import { apiClient } from '@/api/client'

interface Tenant {
  id: string
  hospital_name: string
  slug: string
  status: string
  bed_capacity: number
  icu_beds: number
}

export function TenantManagementPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: async () => {
      const { data: d } = await apiClient.get('/tenants')
      return d as { count: number; items: Tenant[] }
    },
  })

  return (
    <PageContainer title="Tenant Management" subtitle="Multi-hospital SaaS administration">
      {isLoading ? (
        <p className="text-slate-400">Loading tenants...</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {(data?.items ?? []).map((tenant) => (
            <GlassCard key={tenant.id} title={tenant.hospital_name}>
              <div className="space-y-2 text-sm">
                <p className="text-slate-400">ID: <span className="text-slate-200">{tenant.id}</span></p>
                <p className="text-slate-400">Slug: <span className="text-slate-200">{tenant.slug}</span></p>
                <p className="text-slate-400">Beds: <span className="text-slate-200">{tenant.bed_capacity} ({tenant.icu_beds} ICU)</span></p>
                <Badge color={tenant.status === 'active' ? '#10b981' : '#f59e0b'}>{tenant.status}</Badge>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </PageContainer>
  )
}
