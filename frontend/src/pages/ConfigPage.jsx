import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { CheckCircle, XCircle, ExternalLink, Wifi, WifiOff, Unlink } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ConfigPage() {
  const qc = useQueryClient()
  const { refreshUser, user } = useAuth()

  const { data: me, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: authApi.me,
  })

  // Listen for popup postMessage after OAuth completes
  useEffect(() => {
    const handleMsg = (e) => {
      if (e.origin !== window.location.origin) return
      if (e.data?.type === 'gmail_connected') {
        qc.invalidateQueries(['me'])
        refreshUser()
        if (e.data.success) toast.success('Gmail connected successfully!')
      }
    }
    window.addEventListener('message', handleMsg)
    return () => window.removeEventListener('message', handleMsg)
  }, [qc, refreshUser])

  const connectGmail = async () => {
    try {
      const { url } = await authApi.oauthUrl()
      window.open(url, 'gmail_oauth', 'width=600,height=700,left=200,top=100')
    } catch { }
  }

  const disconnectMut = useMutation({
    mutationFn: authApi.disconnect,
    onSuccess: () => {
      toast.success('Gmail disconnected')
      qc.invalidateQueries(['me'])
      refreshUser()
    },
  })

  const gmailConnected = me?.gmail_connected

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Configuration</h1>
        <p>Manage your Gmail OAuth connection</p>
      </div>

      {/* Gmail Connection Card */}
      <div className="card" style={{ maxWidth: 600, marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <div style={{
            width: 42, height: 42, borderRadius: 10,
            background: gmailConnected ? 'rgba(0,230,118,0.1)' : 'rgba(255,61,113,0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: `1px solid ${gmailConnected ? 'rgba(0,230,118,0.3)' : 'rgba(255,61,113,0.3)'}`,
          }}>
            {gmailConnected ? <Wifi size={18} color="var(--success)" /> : <WifiOff size={18} color="var(--error)" />}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>Gmail OAuth 2.0</div>
            <div style={{ fontSize: 12, color: 'var(--subtext)' }}>
              {isLoading ? 'Checking...' : gmailConnected ? `Connected as ${me?.gmail_email}` : 'Not connected'}
            </div>
          </div>
          <div style={{ marginLeft: 'auto' }}>
            {gmailConnected
              ? <span className="badge badge-success">● Active</span>
              : <span className="badge badge-error">● Disconnected</span>}
          </div>
        </div>

        <div className="divider" />

        {gmailConnected ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, padding: '10px 14px', background: 'rgba(0,230,118,0.05)', borderRadius: 8, border: '1px solid rgba(0,230,118,0.15)' }}>
              <CheckCircle size={14} color="var(--success)" />
              <span style={{ fontSize: 13 }}>Gmail is connected. You can send emails via the Send page.</span>
            </div>
            <button className="btn-secondary" onClick={() => disconnectMut.mutate()}
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Unlink size={14} /> Disconnect Gmail
            </button>
          </div>
        ) : (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, padding: '10px 14px', background: 'rgba(255,61,113,0.05)', borderRadius: 8, border: '1px solid rgba(255,61,113,0.15)' }}>
              <XCircle size={14} color="var(--error)" />
              <span style={{ fontSize: 13 }}>Connect your Gmail to start sending campaigns.</span>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn-primary" onClick={connectGmail}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ExternalLink size={14} /> Connect Gmail
              </button>
            </div>
          </div>
        )}
      </div>

      {/* OAuth Setup Instructions — admin only */}
      {user?.is_admin && (
        <details className="card" style={{ maxWidth: 600, marginTop: 24, cursor: 'pointer' }}>
          <summary style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', outline: 'none', userSelect: 'none' }}>
            Google Cloud Console setup instructions (Admin only)
          </summary>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
            {[
              { n: 1, title: 'Go to Google Cloud Console', desc: 'Visit console.cloud.google.com and select your project (or create one).' },
              { n: 2, title: 'Enable Gmail API', desc: 'Navigate to: APIs & Services → Library → search "Gmail API" → Enable.' },
              { n: 3, title: 'Create OAuth Credentials', desc: 'APIs & Services → Credentials → Create → OAuth 2.0 Client ID → Web Application.' },
              { n: 4, title: 'Set Authorized JavaScript Origins', body: ['http://localhost:3000', 'https://your-frontend.vercel.app'] },
              { n: 5, title: 'Set Authorized Redirect URIs', body: ['http://localhost:8000/api/auth/oauth/callback', 'https://your-backend.vercel.app/api/auth/oauth/callback'] },
              { n: 6, title: 'Copy credentials to backend .env', desc: 'Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your backend/.env file.' },
            ].map(step => (
              <div key={step.n} style={{ display: 'flex', gap: 14 }}>
                <div style={{
                  width: 26, height: 26, borderRadius: '50%', flexShrink: 0, marginTop: 1,
                  background: 'rgba(70,85,88,0.12)', border: '1px solid rgba(0,212,255,0.3)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700, color: 'var(--accent-lit)',
                }}>{step.n}</div>
                <div style={{ color: 'var(--text)' }}>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{step.title}</div>
                  {step.desc && <div style={{ fontSize: 12, color: 'var(--subtext)', marginTop: 2 }}>{step.desc}</div>}
                  {step.body && (
                    <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {step.body.map(b => (
                        <code key={b} style={{
                          fontSize: 12, padding: '3px 8px', borderRadius: 4,
                          background: 'var(--bg)', border: '1px solid var(--border)',
                          color: 'var(--accent-lit)', fontFamily: 'var(--mono)',
                        }}>{b}</code>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
