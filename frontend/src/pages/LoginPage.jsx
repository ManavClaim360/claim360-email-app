import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Mail, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'

import { authApi, api } from '../utils/api'

export default function LoginPage() {
  const [tab, setTab] = useState('login')
  const [form, setForm] = useState({ email: '', password: '', full_name: '', otp: '' })
  const [otpSent, setOtpSent] = useState(false)
  const [otpLoading, setOtpLoading] = useState(false)
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSendOtp = async (purpose) => {
    if (!form.email) { toast.error('Please enter your email first'); return }
    setOtpLoading(true)
    try {
      await authApi.sendOtp(form.email, purpose)
      setOtpSent(true)
      toast.success('OTP sent to your email!')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to send OTP')
    }
    setOtpLoading(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (tab === 'login' || tab === 'admin') {
        const data = await login(form.email, form.password, tab === 'admin')
        navigate('/')
      } else if (tab === 'register') {
        if (form.password.length < 8) { toast.error('Password must be 8+ characters'); return }
        if (!form.otp) { toast.error('OTP is required'); return }
        await register(form.email, form.full_name, form.password, form.otp)
        navigate('/')
      } else if (tab === 'forgot') {
        if (form.password.length < 8) { toast.error('Password must be 8+ characters'); return }
        if (!form.otp) { toast.error('OTP is required'); return }
        await authApi.resetPassword(form.email, form.otp, form.password)
        toast.success('Password reset successfully! Please sign in.')
        setTab('login')
        setForm(f => ({ ...f, password: '', otp: '' }))
        setOtpSent(false)
      }
    } catch (err) {
      // error toast handled by axios interceptor
    } finally {
      setLoading(false)
    }
  }

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

      <div className="fade-in" style={{ width: '100%', maxWidth: 400, position: 'relative' }}>
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
          {/* Tabs */}
          <div style={{ display: 'flex', background: 'var(--surface)', borderRadius: 8, padding: 3, marginBottom: 24, gap: 2 }}>
            {['login', 'admin', 'register', 'forgot'].map(t => (
              <button type="button" key={t} onClick={() => { setTab(t); setOtpSent(false) }} style={{
                flex: 1, padding: '7px 0', borderRadius: 6, border: 'none',
                fontSize: 12, fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s',
                background: tab === t ? 'var(--card)' : 'transparent',
                color: tab === t ? 'var(--accent)' : 'var(--subtext)',
                boxShadow: tab === t ? '0 1px 3px rgba(0,0,0,0.3)' : 'none',
              }}>
                {t === 'login' ? 'User' : t === 'admin' ? 'Admin' : t === 'register' ? 'Register' : 'Reset'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit}>
            {tab === 'register' && (
              <div className="form-row">
                <label>Full Name</label>
                <input value={form.full_name} onChange={set('full_name')} placeholder="Your name" required />
              </div>
            )}

            {tab === 'admin' && (
              <div style={{ background: 'rgba(255,140,0,0.1)', border: '1px solid rgba(255,140,0,0.3)', padding: '10px 12px', borderRadius: 6, marginBottom: 16, fontSize: 12, color: 'orange' }}>
                🔒 Admin Login
              </div>
            )}
            
            <div className="form-row">
              <label>Email Address</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input type="email" value={form.email} onChange={set('email')} placeholder="you@company.com" required style={{ flex: 1 }} />
                {(tab === 'register' || tab === 'forgot') && (
                  <button type="button" className="btn-secondary" onClick={() => handleSendOtp(tab === 'register' ? 'register' : 'reset')} disabled={otpLoading} style={{ padding: '0 12px', fontSize: 12 }}>
                    {otpLoading ? 'Sending...' : otpSent ? 'Resend' : 'Send OTP'}
                  </button>
                )}
              </div>
            </div>
            
            {(tab === 'register' || tab === 'forgot') && otpSent && (
              <div className="form-row fade-in">
                <label>OTP Code</label>
                <input value={form.otp} onChange={set('otp')} placeholder="123456" required maxLength={6} style={{ letterSpacing: 2, fontWeight: 'bold' }} />
              </div>
            )}

            {(tab !== 'forgot' || otpSent) && (
              <div className="form-row" style={{ position: 'relative' }}>
                <label>{tab === 'forgot' ? 'New Password' : 'Password'}</label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showPw ? 'text' : 'password'}
                    value={form.password} onChange={set('password')}
                    placeholder={tab === 'register' || tab === 'forgot' ? 'Min 8 characters' : '••••••••'}
                    required style={{ paddingRight: 40, width: '100%' }}
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

            <button type="submit" className="btn-primary" disabled={loading}
              style={{ width: '100%', padding: '11px', marginTop: 8, fontSize: 14, background: tab === 'admin' ? 'linear-gradient(135deg, #ff8c00, #ff6b35)' : undefined }}>
              {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> :
                (tab === 'login' || tab === 'admin') ? 'Sign In' : tab === 'register' ? 'Create Account' : 'Reset Password'}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', color: 'var(--subtext)', fontSize: 11, marginTop: 20 }}>
          Claim360 Email WebApp v1.0 · Internal Team Tool
        </p>
      </div>
    </div>
  )
}
