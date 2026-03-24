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
  const { user, loading } = useAuth()
  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)' }}>
      <div className="spinner" style={{ width: 32, height: 32 }} />
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
