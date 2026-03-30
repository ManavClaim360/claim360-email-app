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
