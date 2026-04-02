import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

export default function OAuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    const success = new URLSearchParams(window.location.search).get('success') === '1'

    // If opened as a popup, notify the opener and close
    if (window.opener && !window.opener.closed) {
      try {
        window.opener.postMessage({ type: 'gmail_connected', success }, window.location.origin)
      } catch (_) { /* cross-origin safety */ }
      window.close()
      return
    }

    // Fallback: loaded in the main window (rare)
    if (success) toast.success('Gmail connected successfully!')
    setTimeout(() => navigate('/config'), 1500)
  }, [navigate])

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', background: 'var(--bg)',
    }}>
      <div className="spinner" style={{ width: 36, height: 36, marginBottom: 16 }} />
      <p style={{ color: 'var(--subtext)' }}>Gmail connected! Closing window...</p>
    </div>
  )
}
