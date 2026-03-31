import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Mail, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'
import { authApi } from '../utils/api'

// ── Tab constants ──────────────────────────────────────────────────────────────
const TABS = [
  { id: 'login',    label: 'Sign In' },
  { id: 'register', label: 'Register' },
  { id: 'reset',    label: 'Reset Password' },
]

export default function LoginPage() {
  const [tab, setTab]               = useState('login')
  const [form, setForm]             = useState({ email: '', password: '', full_name: '', otp: '', new_password: '' })
  const [showPw, setShowPw]         = useState(false)
  const [loading, setLoading]       = useState(false)
  const [otpSent, setOtpSent]       = useState(false)
  const [otpLoading, setOtpLoading] = useState(false)
  const [regsOpen, setRegsOpen]     = useState(null) // null = loading, true/false = status

  const { login, register } = useAuth()
  const navigate = useNavigate()

  // Fetch registration status on mount
  useEffect(() => {
    authApi.registrationsStatus()
      .then(d => setRegsOpen(d.open))
      .catch(() => setRegsOpen(false))
  }, [])

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const switchTab = (t) => {
    setTab(t)
    setOtpSent(false)
    setForm(f => ({ ...f, otp: '' }))
  }

  // ── OTP sender ──────────────────────────────────────────────────────────────
  const handleSendOtp = async () => {
    if (!form.email) { toast.error('Enter your email first'); return }
    const purpose = tab === 'register' ? 'register' : 'reset'
    setOtpLoading(true)
    try {
      const res = await authApi.sendOtp(form.email, purpose)
      setOtpSent(true)
      toast.success(res.message || 'OTP sent to your email!')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to send OTP')
    } finally {
      setOtpLoading(false)
    }
  }

  // ── Form submit ─────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (tab === 'login') {
        const data = await login(form.email, form.password)
        toast.success(data.is_admin ? '🛡 Welcome back, Admin!' : `Welcome back, ${data.full_name}!`)
        navigate('/config')

      } else if (tab === 'register') {
        if (!regsOpen) { toast.error('Registrations are currently closed'); return }
        if (form.password.length < 8) { toast.error('Password must be 8+ characters'); return }
        if (!form.otp)                { toast.error('Enter the OTP from your email'); return }
        if (!form.full_name.trim())   { toast.error('Full name is required'); return }
        const data = await register(form.email, form.full_name, form.password, form.otp)
        toast.success(`Account created! Welcome, ${data.full_name}!`)
        navigate('/config')

      } else if (tab === 'reset') {
        if (!form.otp)                          { toast.error('Enter the OTP from your email'); return }
        if (form.new_password.length < 8)       { toast.error('New password must be 8+ characters'); return }
        await authApi.resetPassword(form.email, form.otp, form.new_password)
        toast.success('Password updated! Please sign in.')
        switchTab('login')
        setForm(f => ({ ...f, new_password: '', otp: '' }))
      }
    } catch (err) {
      // axios interceptor already shows the toast — nothing extra needed
    } finally {
      setLoading(false)
    }
  }

  // ── UI helpers ──────────────────────────────────────────────────────────────
  const isOtpTab = tab === 'register' || tab === 'reset'

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }}>
      {/* Background grid */}
      <div style={{
        position: 'fixed', inset: 0, opacity: 0.04,
        backgroundImage: 'linear-gradient(var(--border) 1px, transparent 1px), linear-gradient(90deg, var(--border) 1px, transparent 1px)',
        backgroundSize: '40px 40px',
        pointerEvents: 'none',
      }} />

      <div className="fade-in" style={{ width: '100%', maxWidth: 420, position: 'relative' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: 52, height: 52, borderRadius: 14,
            background: 'linear-gradient(135deg, var(--accent2), var(--accent))',
            marginBottom: 14,
          }}>
            <Mail size={24} color="white" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text)', letterSpacing: -0.5 }}>Claim360</h1>
          <p style={{ color: 'var(--subtext)', fontSize: 13, marginTop: 4 }}>Bulk Email Intelligence Platform</p>
        </div>

        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 12, padding: 32 }}>

          {/* Tab bar */}
          <div style={{ display: 'flex', background: 'var(--surface)', borderRadius: 8, padding: 3, marginBottom: 24 }}>
            {TABS.map(t => (
              <button
                key={t.id}
                type="button"
                id={`tab-${t.id}`}
                onClick={() => switchTab(t.id)}
                style={{
                  flex: 1, padding: '7px 0', borderRadius: 6, border: 'none',
                  fontSize: 12, fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s',
                  background: tab === t.id ? 'var(--card)' : 'transparent',
                  color: tab === t.id ? 'var(--accent2)' : 'var(--subtext)',
                  boxShadow: tab === t.id ? '0 1px 3px rgba(0,0,0,0.3)' : 'none',
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* ── Sign In tab ─────────────────────────────────────────────────── */}
          {tab === 'login' && (
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <label>Email Address</label>
                <input
                  id="login-email"
                  type="email"
                  value={form.email}
                  onChange={set('email')}
                  placeholder="you@company.com"
                  required
                  autoComplete="username"
                />
              </div>

              <div className="form-row">
                <label>Password</label>
                <div style={{ position: 'relative' }}>
                  <input
                    id="login-password"
                    type={showPw ? 'text' : 'password'}
                    value={form.password}
                    onChange={set('password')}
                    placeholder="••••••••"
                    required
                    style={{ paddingRight: 40, width: '100%' }}
                    autoComplete="current-password"
                  />
                  <button type="button" onClick={() => setShowPw(s => !s)} style={{
                    position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', color: 'var(--subtext)', cursor: 'pointer', padding: 0,
                  }}>
                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              {/* Admin hint */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 6,
                fontSize: 11, color: 'var(--subtext)', marginBottom: 16,
              }}>
                <ShieldCheck size={12} />
                <span>Admins use the same form — role is detected automatically.</span>
              </div>

              <button id="btn-signin" type="submit" className="btn-primary" disabled={loading}
                style={{ width: '100%', padding: '11px', fontSize: 14 }}>
                {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Sign In'}
              </button>
            </form>
          )}

          {/* ── Register tab ────────────────────────────────────────────────── */}
          {tab === 'register' && (
            <>
              {regsOpen === null && (
                <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--subtext)' }}>
                  <span className="spinner" />
                </div>
              )}
              {regsOpen === false && (
                <div style={{
                  background: 'rgba(248,81,73,0.08)', border: '1px solid rgba(248,81,73,0.25)',
                  borderRadius: 8, padding: '18px 16px', textAlign: 'center',
                }}>
                  <div style={{ fontSize: 28, marginBottom: 10 }}>🔒</div>
                  <p style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>Registrations Closed</p>
                  <p style={{ fontSize: 12, color: 'var(--subtext)', lineHeight: 1.6 }}>
                    New account registration is currently disabled.<br />
                    Please contact your admin to get access.
                  </p>
                </div>
              )}
              {regsOpen === true && (
                <form onSubmit={handleSubmit}>
                  <div className="form-row">
                    <label>Full Name</label>
                    <input
                      id="reg-name"
                      value={form.full_name}
                      onChange={set('full_name')}
                      placeholder="Your full name"
                      required
                    />
                  </div>

                  <div className="form-row">
                    <label>Email Address</label>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <input
                        id="reg-email"
                        type="email"
                        value={form.email}
                        onChange={set('email')}
                        placeholder="you@company.com"
                        required
                        style={{ flex: 1 }}
                        autoComplete="username"
                      />
                      <button
                        type="button"
                        id="btn-send-otp-reg"
                        className="btn-secondary"
                        onClick={handleSendOtp}
                        disabled={otpLoading}
                        style={{ padding: '0 12px', fontSize: 12, flexShrink: 0 }}
                      >
                        {otpLoading ? 'Sending…' : otpSent ? 'Resend' : 'Send OTP'}
                      </button>
                    </div>
                  </div>

                  {otpSent && (
                    <div className="form-row fade-in">
                      <label>OTP Code</label>
                      <input
                        id="reg-otp"
                        value={form.otp}
                        onChange={set('otp')}
                        placeholder="6-digit code"
                        required
                        maxLength={6}
                        style={{ letterSpacing: 3, fontWeight: 700 }}
                      />
                    </div>
                  )}

                  <div className="form-row">
                    <label>Password</label>
                    <div style={{ position: 'relative' }}>
                      <input
                        id="reg-password"
                        type={showPw ? 'text' : 'password'}
                        value={form.password}
                        onChange={set('password')}
                        placeholder="Min 8 characters"
                        required
                        style={{ paddingRight: 40, width: '100%' }}
                        autoComplete="new-password"
                      />
                      <button type="button" onClick={() => setShowPw(s => !s)} style={{
                        position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                        background: 'none', border: 'none', color: 'var(--subtext)', cursor: 'pointer', padding: 0,
                      }}>
                        {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                      </button>
                    </div>
                  </div>

                  <button id="btn-register" type="submit" className="btn-primary" disabled={loading || !otpSent}
                    style={{ width: '100%', padding: '11px', marginTop: 4, fontSize: 14 }}>
                    {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Create Account'}
                  </button>

                  {!otpSent && (
                    <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--subtext)', marginTop: 12 }}>
                      Send OTP to your email first, then fill it in above.
                    </p>
                  )}
                </form>
              )}
            </>
          )}

          {/* ── Reset Password tab ──────────────────────────────────────────── */}
          {tab === 'reset' && (
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <label>Email Address</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    id="reset-email"
                    type="email"
                    value={form.email}
                    onChange={set('email')}
                    placeholder="you@company.com"
                    required
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    id="btn-send-otp-reset"
                    className="btn-secondary"
                    onClick={handleSendOtp}
                    disabled={otpLoading}
                    style={{ padding: '0 12px', fontSize: 12, flexShrink: 0 }}
                  >
                    {otpLoading ? 'Sending…' : otpSent ? 'Resend' : 'Send OTP'}
                  </button>
                </div>
              </div>

              {otpSent && (
                <div className="form-row fade-in">
                  <label>OTP Code</label>
                  <input
                    id="reset-otp"
                    value={form.otp}
                    onChange={set('otp')}
                    placeholder="6-digit code"
                    required
                    maxLength={6}
                    style={{ letterSpacing: 3, fontWeight: 700 }}
                  />
                </div>
              )}

              {otpSent && (
                <div className="form-row fade-in">
                  <label>New Password</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      id="reset-new-password"
                      type={showPw ? 'text' : 'password'}
                      value={form.new_password}
                      onChange={set('new_password')}
                      placeholder="Min 8 characters"
                      required
                      style={{ paddingRight: 40, width: '100%' }}
                      autoComplete="new-password"
                    />
                    <button type="button" onClick={() => setShowPw(s => !s)} style={{
                      position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                      background: 'none', border: 'none', color: 'var(--subtext)', cursor: 'pointer', padding: 0,
                    }}>
                      {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>
              )}

              <button id="btn-reset" type="submit" className="btn-primary"
                disabled={loading || !otpSent}
                style={{ width: '100%', padding: '11px', marginTop: 4, fontSize: 14 }}>
                {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Update Password'}
              </button>

              {!otpSent && (
                <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--subtext)', marginTop: 12 }}>
                  Enter your email and click "Send OTP" to receive a reset code.
                </p>
              )}
            </form>
          )}
        </div>

        <p style={{ textAlign: 'center', color: 'var(--subtext)', fontSize: 11, marginTop: 20 }}>
          Claim360 Email WebApp v1.0 · Internal Team Tool
        </p>
      </div>
    </div>
  )
}
