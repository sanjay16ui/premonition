import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Mail, ArrowRight, RotateCcw, CheckCircle, AlertTriangle, Lock } from 'lucide-react'
import { apiClient } from '../api/client'

type Step = 'email' | 'otp' | 'success'

interface OTPRequestResponse {
  message: string
  expires_in_seconds: number
  masked_email: string
}

interface OTPVerifyResponse {
  message: string
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  role: string
}

function maskEmail(email: string): string {
  const [local, domain] = email.split('@')
  if (!domain) return email
  const masked = local.length <= 2
    ? local[0] + '***'
    : local[0] + '***' + local[local.length - 1]
  return `${masked}@${domain}`
}

export function LoginPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('email')
  const [email, setEmail] = useState('')
  const [maskedEmail, setMaskedEmail] = useState('')
  const [otp, setOtp] = useState(['', '', '', ''])
  const [countdown, setCountdown] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [isDemoLoading, setIsDemoLoading] = useState(false)
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [error, setError] = useState('')
  const [locked, setLocked] = useState(false)
  const [attemptsLeft, setAttemptsLeft] = useState(3)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Countdown timer
  useEffect(() => {
    if (countdown <= 0) {
      if (timerRef.current) clearInterval(timerRef.current)
      return
    }
    timerRef.current = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timerRef.current!)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [countdown])

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const requestOTP = useCallback(async (emailAddr: string, isResend = false) => {
    setIsLoading(true)
    setError('')
    try {
      const endpoint = isResend ? '/auth/resend-otp' : '/auth/request-otp'
      const res = await apiClient.post(endpoint, { email: emailAddr })
      const resp = res.data as OTPRequestResponse

      setMaskedEmail(resp.masked_email || maskEmail(emailAddr))
      setCountdown(Math.min(resp.expires_in_seconds || 30, 30))  // cap at 30s for resend UX
      setOtp(['', '', '', ''])
      setAttemptsLeft(3)
      setError('')
      setStep('otp')
      setTimeout(() => inputRefs.current[0]?.focus(), 100)
    } catch (e: any) {
      const status = e.response?.status
      const detail = e.response?.data?.detail
      if (status === 423) { setLocked(true); setError(detail || 'Account locked.'); return }
      if (status === 429) { setError(detail || 'Too many requests. Try again later.'); return }
      console.error('OTP request error:', e)
      setError('Network error: ' + (detail || e.message || String(e)))
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return
    await requestOTP(email.trim())
  }

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return
    const newOtp = [...otp]
    newOtp[index] = value.slice(-1)
    setOtp(newOtp)
    if (value && index < 3) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
    if (e.key === 'ArrowLeft' && index > 0) inputRefs.current[index - 1]?.focus()
    if (e.key === 'ArrowRight' && index < 3) inputRefs.current[index + 1]?.focus()
  }

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 4)
    if (pasted.length === 4) {
      setOtp(pasted.split(''))
      inputRefs.current[3]?.focus()
    }
  }

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    const code = otp.join('')
    if (code.length !== 4) return
    setIsLoading(true)
    setError('')
    try {
      const res = await apiClient.post('/auth/verify-otp', { email, code })
      const resp = res.data as OTPVerifyResponse

      localStorage.setItem('premonition_access_token', resp.access_token)
      localStorage.setItem('premonition_refresh_token', resp.refresh_token)
      localStorage.setItem('premonition_role', resp.role)
      localStorage.setItem('premonition_email', email)

      setStep('success')
      setTimeout(() => navigate('/'), 1500)
    } catch (e: any) {
      const status = e.response?.status
      const detail = e.response?.data?.detail
      if (status === 423) { setLocked(true); setError(detail || 'Account locked.'); return }
      if (status === 410) { setError('Code expired. Please request a new one.'); setCountdown(0); return }
      if (status === 401) {
        setAttemptsLeft(prev => Math.max(0, prev - 1))
        setError(detail || 'Incorrect code.')
        setOtp(['', '', '', ''])
        inputRefs.current[0]?.focus()
        return
      }
      console.error('OTP verify error:', e)
      setError('Network error: ' + (detail || e.message || String(e)))
    } finally {
      setIsLoading(false)
    }
  }

  const handleResend = () => {
    if (countdown > 0) return
    requestOTP(email, true)
  }

  const handleDemoLogin = async () => {
    setIsDemoLoading(true)
    setError('')
    try {
      const res = await apiClient.post('/auth/demo-login')
      const data = res.data
      
      localStorage.setItem('premonition_access_token', data.access_token)
      localStorage.setItem('premonition_refresh_token', data.refresh_token)
      localStorage.setItem('premonition_role', data.role || 'physician')
      localStorage.setItem('premonition_email', 'demo@premonition.health')
      localStorage.setItem('premonition_demo_mode', 'true')
      
      setIsDemoMode(true)
      setStep('success')
      setTimeout(() => navigate('/'), 1200)
    } catch (e: any) {
      console.error('Demo login error:', e)
      setError('Network error: ' + (e.response?.data?.detail || e.message || String(e)))
    } finally {
      setIsDemoLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0f1e] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 left-1/3 w-[400px] h-[400px] bg-sky-600/8 rounded-full blur-[100px]" />
      </div>

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'linear-gradient(rgba(99,102,241,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.5) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative z-10 w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-sky-500 shadow-lg shadow-indigo-500/30 mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">PREMONITION</h1>
          <p className="text-sm text-slate-400 mt-1">Agentic AI Healthcare Command Center</p>
        </div>

        {/* Card */}
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden">

          {/* Step: Email */}
          {step === 'email' && (
            <div className="p-8">
              <h2 className="text-xl font-semibold text-white mb-1">Doctor Sign In</h2>
              <p className="text-sm text-slate-400 mb-6">Enter your email to receive a verification code</p>

              <form onSubmit={handleEmailSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      id="otp-email-input"
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="doctor@hospital.org"
                      required
                      autoFocus
                      className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                    />
                  </div>
                </div>

                {error && (
                  <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-red-400">{error}</p>
                  </div>
                )}

                <button
                  id="otp-send-btn"
                  type="submit"
                  disabled={isLoading || !email.trim()}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-500 hover:to-sky-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl text-sm transition-all shadow-lg shadow-indigo-500/20"
                >
                  {isLoading ? (
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Sending...
                    </span>
                  ) : (
                    <>Send Verification Code <ArrowRight className="w-4 h-4" /></>
                  )}
                </button>

                {/* Divider */}
                <div className="flex items-center gap-3 my-1">
                  <div className="flex-1 h-px bg-white/10" />
                  <span className="text-xs text-slate-500">or</span>
                  <div className="flex-1 h-px bg-white/10" />
                </div>

                {/* Direct Demo Login */}
                <button
                  id="demo-login-btn"
                  type="button"
                  onClick={handleDemoLogin}
                  disabled={isDemoLoading || isLoading}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-emerald-500/40 disabled:opacity-50 disabled:cursor-not-allowed text-slate-300 hover:text-emerald-400 font-medium rounded-xl text-sm transition-all"
                >
                  {isDemoLoading ? (
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" />
                      Logging in...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <span className="text-base">⚡</span>
                      Direct Demo Login
                    </span>
                  )}
                </button>
                <p className="text-center text-xs text-slate-600">Demo login bypasses OTP — instant access</p>
              </form>
            </div>
          )}

          {/* Step: OTP */}
          {step === 'otp' && (
            <div className="p-8">
              <h2 className="text-xl font-semibold text-white mb-1">Enter Verification Code</h2>
              <p className="text-sm text-slate-400 mb-1">
                Code sent to <span className="text-indigo-400 font-medium">{maskedEmail}</span>
              </p>
              <p className="text-xs text-slate-500 mb-6">Check your inbox (and spam folder)</p>

              {/* Lockout banner */}
              {locked && (
                <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl mb-6">
                  <Lock className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-400">Account Locked</p>
                    <p className="text-xs text-red-400/70 mt-0.5">
                      Too many incorrect attempts. Locked for 2 hours.
                    </p>
                  </div>
                </div>
              )}

              <form onSubmit={handleVerify} className="space-y-6">
                {/* 4-digit input boxes */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-3 text-center">4-Digit Code</label>
                  <div className="flex justify-center gap-3" onPaste={handleOtpPaste}>
                    {otp.map((digit, i) => (
                      <input
                        key={i}
                        id={`otp-digit-${i}`}
                        ref={el => { inputRefs.current[i] = el }}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={e => handleOtpChange(i, e.target.value)}
                        onKeyDown={e => handleOtpKeyDown(i, e)}
                        disabled={locked}
                        className="w-14 h-16 text-center text-2xl font-bold bg-white/5 border-2 border-white/10 rounded-xl text-white focus:outline-none focus:border-indigo-500 focus:bg-indigo-500/10 transition-all disabled:opacity-40 caret-transparent"
                      />
                    ))}
                  </div>
                </div>

                {/* Timer + Resend */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    {countdown > 0 ? (
                      <>
                        <span className="text-xs text-slate-400">Expires in</span>
                        <span className={`text-xs font-mono font-bold tabular-nums ${countdown <= 30 ? 'text-orange-400' : 'text-indigo-400'}`}>
                          {formatTimer(countdown)}
                        </span>
                      </>
                    ) : (
                      <span className="text-xs text-slate-500">Code expired</span>
                    )}
                  </div>
                  <button
                    id="otp-resend-btn"
                    type="button"
                    onClick={handleResend}
                    disabled={countdown > 0 || isLoading || locked}
                    className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-30 disabled:cursor-not-allowed transition"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    Resend Code
                  </button>
                </div>

                {/* Attempts warning */}
                {attemptsLeft < 3 && !locked && (
                  <div className="flex items-center gap-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0" />
                    <p className="text-xs text-yellow-400">
                      {attemptsLeft === 0
                        ? 'No attempts remaining.'
                        : `${attemptsLeft} attempt${attemptsLeft !== 1 ? 's' : ''} remaining before lockout.`}
                    </p>
                  </div>
                )}

                {error && (
                  <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-red-400">{error}</p>
                  </div>
                )}

                <button
                  id="otp-verify-btn"
                  type="submit"
                  disabled={isLoading || otp.join('').length !== 4 || locked}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-500 hover:to-sky-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl text-sm transition-all shadow-lg shadow-indigo-500/20"
                >
                  {isLoading ? (
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Verifying...
                    </span>
                  ) : (
                    <>Verify &amp; Sign In <ArrowRight className="w-4 h-4" /></>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => { setStep('email'); setError(''); setOtp(['', '', '', '']) }}
                  className="w-full text-xs text-slate-500 hover:text-slate-300 transition py-1"
                >
                  ← Use a different email
                </button>
              </form>
            </div>
          )}

          {/* Step: Success */}
          {step === 'success' && (
            <div className="p-8 text-center">
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <CheckCircle className="w-8 h-8 text-emerald-400" />
                </div>
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Login Successful</h2>
              {isDemoMode && (
                <div className="mx-auto mt-3 mb-2 px-4 py-2 bg-amber-500/15 border border-amber-500/30 rounded-lg inline-flex items-center gap-2">
                  <span className="text-amber-400 text-xs font-semibold tracking-wide">⚡ DEMO MODE ACTIVE</span>
                </div>
              )}
              <p className="text-sm text-slate-400">{isDemoMode ? 'Redirecting to Command Center in Demo Mode...' : 'Redirecting to Command Center...'}</p>
              <div className="mt-4 flex justify-center">
                <span className="w-5 h-5 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
              </div>
            </div>
          )}
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          PREMONITION · Secure Clinical AI · Protected by OTP Verification
        </p>
      </div>
    </div>
  )
}
