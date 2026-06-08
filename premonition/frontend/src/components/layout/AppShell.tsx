import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

function AudioUnlocker() {
  const [unlocked, setUnlocked] = useState(false)
  
  useEffect(() => {
    const handleUnlock = async () => {
      const { audioManager } = await import('@/utils/audio')
      if (audioManager.isSuspended()) {
        await audioManager.resumeContext()
      }
      setUnlocked(true)
      window.removeEventListener('click', handleUnlock)
      window.removeEventListener('keydown', handleUnlock)
    }
    
    window.addEventListener('click', handleUnlock)
    window.addEventListener('keydown', handleUnlock)
    
    return () => {
      window.removeEventListener('click', handleUnlock)
      window.removeEventListener('keydown', handleUnlock)
    }
  }, [])

  if (unlocked) return null

  return (
    <div className="fixed top-0 left-0 w-full z-50 bg-indigo-600 text-white text-xs text-center py-1">
      Click anywhere to enable emergency audio alerts.
    </div>
  )
}

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden">
      <AudioUnlocker />
      <Sidebar />

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50 lg:hidden"
            onClick={() => setMobileOpen(false)}
          >
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              className="h-full w-64 bg-white dark:bg-slate-900"
              onClick={(e) => e.stopPropagation()}
            >
              <Sidebar />
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
