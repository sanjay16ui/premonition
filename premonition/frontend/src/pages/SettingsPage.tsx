import { Link } from 'react-router-dom'
import { ROUTES } from '@/routes/paths'
import { useSettingsStore } from '@/store/settingsStore'
import { useThemeStore } from '@/store/themeStore'
import { PageContainer } from '@/components/layout/PageContainer'
import { GlassCard } from '@/components/ui/GlassCard'
import { ThemeToggle } from '@/components/common/ThemeToggle'
import { useNotificationStore } from '@/store/notificationStore'
import { SoundControls } from '@/components/ui/SoundControls'

export function SettingsPage() {
  const {
    refreshInterval,
    defaultTopN,
    showTooltips,
    apiBaseUrl,
    setRefreshInterval,
    setDefaultTopN,
    setShowTooltips,
  } = useSettingsStore()
  const { mode } = useThemeStore()
  const notify = useNotificationStore()

  return (
    <PageContainer
      title="Settings"
      subtitle="Configure dashboard preferences and display options"
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <GlassCard title="Appearance">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Theme</p>
              <p className="text-sm text-slate-400">
                Currently: {mode === 'dark' ? 'Dark' : 'Light'} mode
              </p>
            </div>
            <ThemeToggle />
          </div>
        </GlassCard>

        <GlassCard title="Display">
          <div className="space-y-4">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={showTooltips}
                onChange={(e) => setShowTooltips(e.target.checked)}
                className="h-4 w-4 rounded"
              />
              <div>
                <p className="text-sm font-medium">Show tooltips</p>
                <p className="text-xs text-slate-400">
                  Display help icons with explanations on metrics
                </p>
              </div>
            </label>
          </div>
        </GlassCard>

        <GlassCard title="SHAP Settings">
          <div>
            <label className="text-sm text-slate-500">
              Default top features (SHAP)
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={defaultTopN}
              onChange={(e) => setDefaultTopN(Number(e.target.value))}
              className="mt-1 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
            />
            <p className="mt-1 text-xs text-slate-400">
              Number of top contributing features shown in explanations
            </p>
          </div>
        </GlassCard>

        <GlassCard title="Data Refresh">
          <div>
            <label className="text-sm text-slate-500">
              Auto-refresh interval (seconds)
            </label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="mt-1 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
            >
              <option value={5000}>5 seconds</option>
              <option value={15000}>15 seconds</option>
              <option value={30000}>30 seconds</option>
              <option value={60000}>60 seconds</option>
            </select>
          </div>
        </GlassCard>

        <SoundControls />

        <GlassCard className="lg:col-span-2" title="API Connection">
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Base URL</span>
              <code className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs">
                {apiBaseUrl}
              </code>
            </div>
            <p className="text-xs text-slate-400">
              Configure via VITE_API_BASE_URL in .env. Vite dev server proxies /api to localhost:8000.
            </p>
            <button
              onClick={() => notify.info('Settings saved', 'Preferences are stored locally in your browser.')}
              className="rounded-xl bg-sky-500 px-4 py-2 text-sm text-white hover:bg-sky-600"
            >
              Save Preferences
            </button>
          </div>
        </GlassCard>

        {/* Advanced Developer Links */}
        <GlassCard className="lg:col-span-2" title="Advanced (Developer Tools)">
          <p className="text-sm text-slate-400 mb-4">
            These views are for technical debugging, model auditing, and system health checks.
          </p>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
            {[
              { path: ROUTES.shapExplain, name: 'SHAP Explain' },
              { path: ROUTES.auditLogs, name: 'Audit Logs' },
              { path: ROUTES.analyticsDashboard, name: 'Analytics Dashboard' },
              { path: ROUTES.modelPerformance, name: 'Model Performance' },
              { path: ROUTES.systemHealth, name: 'System Health' },
              { path: ROUTES.tenantManagement, name: 'Tenant Management' },
              { path: ROUTES.predictionHistory, name: 'Prediction History' },
              { path: ROUTES.copilotPatient, name: 'Patient Copilot (Dev)' },
              { path: ROUTES.copilotExecutive, name: 'Executive Copilot (Dev)' }
            ].map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className="flex items-center justify-between rounded-xl bg-slate-100/50 dark:bg-slate-800/50 p-4 text-sm font-medium hover:bg-slate-200/50 dark:hover:bg-slate-700/50 transition"
              >
                {link.name}
                <span className="text-slate-400">→</span>
              </Link>
            ))}
          </div>
        </GlassCard>
      </div>
    </PageContainer>
  )
}
