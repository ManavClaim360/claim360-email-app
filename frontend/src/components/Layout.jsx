import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useEffect, useState } from 'react'
import {
  Settings, Database, FileText, Eye, Send, BarChart2,
  ShieldCheck, LogOut, Mail, Sun, Moon, Monitor, PenLine, Menu
} from 'lucide-react'

const NAV = [
  { to: '/config',    icon: Settings,  label: 'Configuration',   tip: 'Gmail OAuth settings' },
  { to: '/data',      icon: Database,  label: 'Data & Variables', tip: 'Upload contacts & define variables' },
  { to: '/templates', icon: FileText,  label: 'Templates',        tip: 'Create & manage email templates' },
  { to: '/signature', icon: PenLine,   label: 'Signature',        tip: 'Email signature manager' },
  { to: '/preview',   icon: Eye,       label: 'Preview',          tip: 'Preview emails before sending' },
  { to: '/send',      icon: Send,      label: 'Send Email',       tip: 'Launch email campaigns' },
  { to: '/tracking',  icon: BarChart2, label: 'Tracking & Logs',  tip: 'Monitor open rates & delivery' },
]
const ADMIN_NAV = { to: '/admin', icon: ShieldCheck, label: 'Admin Panel', tip: 'Manage users & platform stats' }

const THEMES = [
  { key: 'dark',    icon: Moon,    label: 'Dark' },
  { key: 'light',   icon: Sun,     label: 'Light' },
  { key: 'default', icon: Monitor, label: 'System' },
]

function useTheme() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('c360-theme')
    if (saved) return saved
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
  })
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('c360-theme', theme)
  }, [theme])
  return [theme, setTheme]
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [theme, setTheme] = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', flexDirection: 'column' }}>
      
      {/* Mobile Topbar */}
      <div className="mobile-topbar" style={{ display: 'none' }}>
        <button onClick={() => setMenuOpen(true)} className="btn-icon" style={{ border: 'none', background: 'transparent', color: 'var(--text)' }}>
          <Menu size={20} />
        </button>
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.5 }}>Claim360</div>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <div className={`sidebar-overlay ${menuOpen ? 'open' : ''}`} onClick={() => setMenuOpen(false)} />
        <aside className={`app-sidebar ${menuOpen ? 'open' : ''}`} style={{
          width: 230, flexShrink: 0, display: 'flex', flexDirection: 'column',
          background: 'rgba(7,19,58,0.95)', backdropFilter: 'blur(16px)',
          borderRight: '1px solid rgba(255,255,255,0.12)',
        }}>
          {/* Logo */}
        <div style={{ padding: '0 18px', height: 64, display: 'flex', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: 'rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Mail size={16} color="white" />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', letterSpacing: 0.5 }}>Claim360</div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)', letterSpacing: 0.3 }}>Email WebApp</div>
          </div>
        </div>

        {/* Nav links */}
        <nav style={{ flex: 1, padding: '10px 8px', overflowY: 'auto' }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.35)', letterSpacing: 1, padding: '8px 10px 4px', textTransform: 'uppercase' }}>Menu</div>
          {NAV.map(({ to, icon: Icon, label, tip }) => (
            <NavLink key={to} to={to} title={tip}
              className={({ isActive }) => isActive ? 'nav-link-active' : ''}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '9px 12px', borderRadius: 6, marginBottom: 1,
                fontSize: 13, fontWeight: isActive ? 600 : 500, textDecoration: 'none',
                color: isActive ? '#fff' : 'rgba(255,255,255,0.65)',
                background: isActive ? 'rgba(255,255,255,0.14)' : 'transparent',
                borderLeft: `3px solid ${isActive ? '#a8c8f0' : 'transparent'}`,
                transition: 'all 0.15s',
              })} onClick={() => setMenuOpen(false)}>
              <Icon size={15} />
              {label}
            </NavLink>
          ))}

          {user?.is_admin && (
            <>
              <div style={{ height: 1, background: 'rgba(255,255,255,0.1)', margin: '8px 4px' }} />
              <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.35)', letterSpacing: 1, padding: '4px 10px 4px', textTransform: 'uppercase' }}>Admin</div>
              <NavLink to={ADMIN_NAV.to} title={ADMIN_NAV.tip} style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '9px 12px', borderRadius: 6, marginBottom: 1,
                fontSize: 13, fontWeight: 500, textDecoration: 'none',
                color: isActive ? '#fff' : 'rgba(255,255,255,0.65)',
                background: isActive ? 'rgba(121,40,202,0.3)' : 'transparent',
                borderLeft: `3px solid ${isActive ? '#B44DFF' : 'transparent'}`,
                transition: 'all 0.15s',
              })} onClick={() => setMenuOpen(false)}>
                <ADMIN_NAV.icon size={15} />
                {ADMIN_NAV.label}
              </NavLink>
            </>
          )}
        </nav>

        {/* Theme switcher */}
        <div style={{ padding: '10px 12px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.35)', letterSpacing: 1, marginBottom: 8, textTransform: 'uppercase' }}>Theme</div>
          <div style={{ display: 'flex', gap: 4 }}>
            {THEMES.map(({ key, icon: Icon, label }) => (
              <button key={key} onClick={() => setTheme(key)} title={label} style={{
                flex: 1, padding: '6px 0', border: 'none', borderRadius: 6, cursor: 'pointer',
                background: theme === key ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.05)',
                color: theme === key ? '#fff' : 'rgba(255,255,255,0.4)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 0.15s',
              }}>
                <Icon size={13} />
              </button>
            ))}
          </div>
        </div>

        {/* User section */}
        <div style={{ padding: '10px 12px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)', marginBottom: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500 }}>
            {user?.full_name || user?.email}
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 8, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {user?.email}
          </div>
          <button onClick={handleLogout} title="Sign out of Claim360"
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, padding: '7px 12px', fontSize: 12, borderRadius: 6, border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.7)', cursor: 'pointer', transition: 'all 0.15s' }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.15)'; e.currentTarget.style.color = '#fff' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = 'rgba(255,255,255,0.7)' }}>
            <LogOut size={13} /> Sign Out
          </button>
        </div>
      </aside>

        {/* Main content */}
        <main style={{ flex: 1, overflow: 'auto', overflowX: 'hidden', background: 'transparent', minWidth: 0 }}>
          <div className="main-content-pad" style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 32px' }}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
