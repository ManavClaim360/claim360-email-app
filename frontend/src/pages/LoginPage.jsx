import { useState } from 'react'
import axios from 'axios'

// Get API URL from Vite env
const API_URL = import.meta.env.VITE_API_URL

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await axios.post(`${API_URL}/api/auth/login`, { email, password })
      const { access_token, ...user } = res.data
      localStorage.setItem('mb_token', access_token)
      localStorage.setItem('mb_user', JSON.stringify(user))
      window.location.href = '/'
    } catch (err) {
      setError(err?.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', background: '#f7f7fa',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }}>
      <div style={{ width: '100%', maxWidth: 400, background: '#fff', borderRadius: 8, boxShadow: '0 2px 16px #0001', padding: 32 }}>
        <h2 style={{ textAlign: 'center', marginBottom: 24 }}>Sign In</h2>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              style={{ width: '100%', padding: 8, marginTop: 4 }}
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              style={{ width: '100%', padding: 8, marginTop: 4 }}
            />
          </div>
          {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}
          <button type="submit" style={{ width: '100%', padding: 10 }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div style={{ marginTop: 16, fontSize: 12, color: '#888' }}>
          API URL: <span style={{ color: '#333' }}>{API_URL || 'Not set'}</span>
        </div>
      </div>
    </div>
  )
}
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
