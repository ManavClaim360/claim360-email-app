import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

export default function OAuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    // The backend handles the OAuth exchange and redirects here
    // We just show a success message and go to config
    toast.success('Gmail connected successfully!')
    setTimeout(() => navigate('/config'), 1500)
  }, [navigate])

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', background: 'var(--bg)',
    }}>
      <div className="spinner" style={{ width: 36, height: 36, marginBottom: 16 }} />
      <p style={{ color: 'var(--subtext)' }}>Gmail connected! Redirecting...</p>
    </div>
  )
}
