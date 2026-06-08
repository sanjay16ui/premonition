type AlertLevel = 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED' | 'BLACK'

class AlertSoundManager {
  private ctx: AudioContext | null = null
  private gainNode: GainNode | null = null
  private isMuted: boolean = false
  private volume: number = 0.5
  private activeOscillators: OscillatorNode[] = []

  constructor() {
    this.loadSettings()
  }

  private init() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
      this.gainNode = this.ctx.createGain()
      this.gainNode.connect(this.ctx.destination)
      this.updateGain()
    }
  }

  public isSuspended(): boolean {
    return this.ctx?.state === 'suspended'
  }

  public async resumeContext(): Promise<void> {
    if (this.ctx?.state === 'suspended') {
      await this.ctx.resume()
    }
  }

  private loadSettings() {
    try {
      const stored = localStorage.getItem('premonition_audio_settings')
      if (stored) {
        const parsed = JSON.parse(stored)
        this.isMuted = !!parsed.isMuted
        this.volume = parsed.volume ?? 0.5
      }
    } catch (e) {
      console.error('Failed to load audio settings', e)
    }
  }

  public saveSettings() {
    localStorage.setItem(
      'premonition_audio_settings',
      JSON.stringify({ isMuted: this.isMuted, volume: this.volume })
    )
    this.updateGain()
  }

  public toggleMute() {
    this.isMuted = !this.isMuted
    this.saveSettings()
    if (this.isMuted) this.stopAll()
    return this.isMuted
  }

  public setVolume(val: number) {
    this.volume = Math.max(0, Math.min(1, val))
    if (this.volume === 0) this.isMuted = true
    else if (this.isMuted && this.volume > 0) this.isMuted = false
    this.saveSettings()
  }

  public getVolume() {
    return this.volume
  }

  public getIsMuted() {
    return this.isMuted
  }

  private updateGain() {
    if (this.gainNode && this.ctx) {
      this.gainNode.gain.setValueAtTime(this.isMuted ? 0 : this.volume, this.ctx.currentTime)
    }
  }

  public stopAll() {
    this.activeOscillators.forEach((osc) => {
      try {
        osc.stop()
        osc.disconnect()
      } catch (e) {}
    })
    this.activeOscillators = []
  }

  private playTone(freqs: number[], type: OscillatorType, duration: number, beepPattern?: { on: number, off: number, count: number }) {
    if (this.isMuted) return
    this.init()
    const ctx = this.ctx
    const gainNode = this.gainNode
    if (!ctx || !gainNode) return

    const now = ctx.currentTime

    freqs.forEach((freq) => {
      if (beepPattern) {
        for (let i = 0; i < beepPattern.count; i++) {
          const startTime = now + i * (beepPattern.on + beepPattern.off)
          const osc = ctx.createOscillator()
          const env = ctx.createGain()
          osc.type = type
          osc.frequency.setValueAtTime(freq, startTime)
          
          env.gain.setValueAtTime(0, startTime)
          env.gain.linearRampToValueAtTime(1, startTime + 0.05)
          env.gain.setValueAtTime(1, startTime + beepPattern.on - 0.05)
          env.gain.linearRampToValueAtTime(0, startTime + beepPattern.on)
          
          osc.connect(env)
          env.connect(gainNode)
          osc.start(startTime)
          osc.stop(startTime + beepPattern.on)
          this.activeOscillators.push(osc)
        }
      } else {
        const osc = ctx.createOscillator()
        const env = ctx.createGain()
        osc.type = type
        osc.frequency.setValueAtTime(freq, now)
        
        env.gain.setValueAtTime(0, now)
        env.gain.linearRampToValueAtTime(1, now + 0.1)
        env.gain.setValueAtTime(1, now + duration - 0.1)
        env.gain.linearRampToValueAtTime(0, now + duration)
        
        osc.connect(env)
        env.connect(gainNode)
        osc.start(now)
        osc.stop(now + duration)
        this.activeOscillators.push(osc)
      }
    })
    
    // Cleanup old oscillators
    setTimeout(() => {
      this.activeOscillators = this.activeOscillators.filter(o => o.context.currentTime < now + duration * 2)
    }, duration * 2000)
  }

  public play(level: AlertLevel) {
    this.stopAll() // Interrupt previous alerts
    switch (level) {
      case 'GREEN':
        // Soft notification
        this.playTone([440, 554], 'sine', 0.5)
        break
      case 'YELLOW':
        // Gentle attention tone
        this.playTone([440], 'triangle', 0.3, { on: 0.15, off: 0.1, count: 2 })
        break
      case 'ORANGE':
        // Warning tone
        this.playTone([523.25, 659.25], 'square', 1.0, { on: 0.2, off: 0.1, count: 3 })
        break
      case 'RED':
        // Urgent medical tone (standard IEC 60601-1-8 high priority pattern)
        this.playTone([600, 800], 'sawtooth', 2.0, { on: 0.1, off: 0.05, count: 5 })
        break
      case 'BLACK':
        // Emergency alarm (continuous warble)
        if (this.isMuted) return
        this.init()
        if (!this.ctx || !this.gainNode) return
        const now = this.ctx.currentTime
        const osc = this.ctx.createOscillator()
        const mod = this.ctx.createOscillator()
        const modGain = this.ctx.createGain()
        
        osc.type = 'sawtooth'
        osc.frequency.value = 800
        
        mod.type = 'square'
        mod.frequency.value = 5
        
        modGain.gain.value = 200
        
        mod.connect(modGain)
        modGain.connect(osc.frequency)
        
        osc.connect(this.gainNode)
        
        mod.start(now)
        osc.start(now)
        // Removed mod.stop() and osc.stop() to let it loop until stopAll()
        this.activeOscillators.push(osc, mod)
        break
    }
  }
}

export const audioManager = new AlertSoundManager()
