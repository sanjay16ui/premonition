import { useState, useEffect } from 'react'
import { audioManager } from '@/utils/audio'
import { Button } from '@/components/ui/Button'
import { GlassCard } from '@/components/ui/GlassCard'
import { Volume2, VolumeX } from 'lucide-react'

export function SoundControls() {
  const [isMuted, setIsMuted] = useState(audioManager.getIsMuted())
  const [volume, setVolume] = useState(audioManager.getVolume())

  useEffect(() => {
    setIsMuted(audioManager.getIsMuted())
    setVolume(audioManager.getVolume())
  }, [])

  const handleToggleMute = () => {
    const muted = audioManager.toggleMute()
    setIsMuted(muted)
    if (muted) setVolume(0)
    else setVolume(audioManager.getVolume() || 0.5)
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value)
    audioManager.setVolume(val)
    setVolume(val)
    setIsMuted(val === 0)
  }

  const testSound = (level: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED' | 'BLACK') => {
    audioManager.play(level)
  }

  return (
    <GlassCard title="Audio Alert Settings" className="max-w-xl">
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="secondary" onClick={handleToggleMute}>
            {isMuted ? <VolumeX className="w-4 h-4 text-red-400" /> : <Volume2 className="w-4 h-4 text-emerald-400" />}
          </Button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={volume}
            onChange={handleVolumeChange}
            className="flex-1 accent-emerald-500"
          />
          <span className="text-sm font-mono">{Math.round(volume * 100)}%</span>
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-300">Test Alert Tones</h4>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" className="border-emerald-500/50 hover:bg-emerald-500/20" onClick={() => testSound('GREEN')}>
              Soft (🟢)
            </Button>
            <Button variant="secondary" className="border-yellow-500/50 hover:bg-yellow-500/20" onClick={() => testSound('YELLOW')}>
              Gentle (🟡)
            </Button>
            <Button variant="secondary" className="border-orange-500/50 hover:bg-orange-500/20" onClick={() => testSound('ORANGE')}>
              Warning (🟠)
            </Button>
            <Button variant="secondary" className="border-red-500/50 hover:bg-red-500/20" onClick={() => testSound('RED')}>
              Urgent (🔴)
            </Button>
            <Button variant="secondary" className="border-purple-500/50 hover:bg-purple-500/20" onClick={() => testSound('BLACK')}>
              Emergency (⚫)
            </Button>
          </div>
        </div>
      </div>
    </GlassCard>
  )
}
