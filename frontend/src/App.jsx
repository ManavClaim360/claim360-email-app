import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { DataProvider } from './context/DataContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import ConfigPage from './pages/ConfigPage'
import DataPage from './pages/DataPage'
import TemplatePage from './pages/TemplatePage'
import PreviewPage from './pages/PreviewPage'
import SendPage from './pages/SendPage'
import TrackingPage from './pages/TrackingPage'
import AdminPage from './pages/AdminPage'
import SignaturePage from './pages/SignaturePage'
import OAuthCallback from './pages/OAuthCallback'

function RequireAuth({ children }) {
  const { user, loading, error } = useAuth()
  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)', flexDirection: 'column', gap: '20px' }}>
      <div className="spinner" style={{ width: 32, height: 32 }} />
      <p style={{ color: '#b0c4de', fontFamily: 'monospace' }}>Checking authentication...</p>
      {error && <p style={{ color: '#f85149', fontFamily: 'monospace', fontSize: '12px', maxWidth: '400px' }}>Error: {error}</p>}
    </div>
  )
  if (error && !user) return (
    <div style={{ padding: 40, fontFamily: 'monospace', background: 'var(--bg)', color: '#f85149', minHeight: '100vh' }}>
      <h2 style={{ marginBottom: 16, color: '#f0f6fc' }}>⚠ Auth Error</h2>
      <p style={{ marginBottom: 12, color: '#b0c4de' }}>Failed to authenticate. {error}</p>
      <button onClick={() => window.location.href = '/login'} style={{ padding: '10px 20px', background: '#1C305E', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer' }}>
        Go to Login
      </button>
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/config" replace /> : <LoginPage />} />
      <Route path="/oauth/callback" element={<OAuthCallback />} />
      <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Navigate to="/config" replace />} />
        <Route path="config"    element={<ConfigPage />} />
        <Route path="data"      element={<DataPage />} />
        <Route path="templates" element={<TemplatePage />} />
        <Route path="preview"   element={<PreviewPage />} />
        <Route path="send"      element={<SendPage />} />
        <Route path="tracking"  element={<TrackingPage />} />
        <Route path="admin"     element={<AdminPage />} />
        <Route path="signature" element={<SignaturePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/config" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <DataProvider>
        <AppRoutes />
      </DataProvider>
    </AuthProvider>
  )
}
