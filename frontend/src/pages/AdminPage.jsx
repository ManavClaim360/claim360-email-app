import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi, adminUserApi } from '../utils/api'
import { ShieldCheck, Users, BarChart2, Mail, RefreshCw, UserCheck, UserX, Plus, Edit2, Trash2, X, Eye, EyeOff, PenTool, Settings } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import SignaturePage from './SignaturePage'

// ── User form modal ────────────────────────────────────────────────
function UserModal({ user, onClose, onSave }) {
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    email:     user?.email     || '',
    password:  '',
    is_admin:  user?.is_admin  || false,
    is_active: user?.is_active ?? true,
  })
  const [showPw, setShowPw] = useState(false)
  const [saving, setSaving] = useState(false)

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const isNew = !user

  const submit = async () => {
    if (!form.full_name.trim()) { toast.error('Full name required'); return }
    if (!form.email.trim())     { toast.error('Email required'); return }
    if (isNew && !form.password){ toast.error('Password required for new user'); return }
    setSaving(true)
    try {
      await onSave(form)
      onClose()
    } catch { } finally { setSaving(false) }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 12, width: '100%', maxWidth: 440, padding: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>{isNew ? 'Add New User' : `Edit: ${user.full_name}`}</h3>
          <button className="btn-icon" onClick={onClose}><X size={14} /></button>
        </div>

        <div className="form-row">
          <label>Full Name *</label>
          <input value={form.full_name} onChange={set('full_name')} placeholder="John Smith" />
        </div>
        <div className="form-row">
          <label>Email Address *</label>
          <input type="email" value={form.email} onChange={set('email')} placeholder="john@company.com" />
        </div>
        <div className="form-row" style={{ position: 'relative' }}>
          <label>{isNew ? 'Password *' : 'New Password (leave blank to keep current)'}</label>
          <div style={{ display: 'flex', gap: 0 }}>
            <input type={showPw ? 'text' : 'password'} value={form.password} onChange={set('password')}
              placeholder={isNew ? 'Min 8 characters' : 'Leave blank to keep unchanged'}
              style={{ borderRadius: '8px 0 0 8px', borderRight: 'none' }} />
            <button type="button" onClick={() => setShowPw(s => !s)}
              style={{ flexShrink: 0, padding: '0 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '0 8px 8px 0', cursor: 'pointer', color: 'var(--subtext)' }}>
              {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 20, marginBottom: 20 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
            <input type="checkbox" checked={form.is_admin} onChange={e => setForm(f => ({ ...f, is_admin: e.target.checked }))} style={{ width: 15, height: 15 }} />
            Admin access
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
            <input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} style={{ width: 15, height: 15 }} />
            Active account
          </label>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-primary" onClick={submit} disabled={saving} style={{ flex: 1 }}>
            {saving ? <span className="spinner" style={{ width: 14, height: 14 }} /> : isNew ? 'Create User' : 'Save Changes'}
          </button>
          <button className="btn-secondary" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
        </div>
      </div>
    </div>
  )
}

// ── Main AdminPage ─────────────────────────────────────────────────
export default function AdminPage() {
  const qc = useQueryClient()
  const { user: me } = useAuth()
  const [tab, setTab] = useState('overview')
  const [modal, setModal] = useState(null)  // null | 'new' | {user object}

  const { data: stats  } = useQuery({ queryKey: ['admin-stats'],     queryFn: adminApi.stats,       enabled: tab === 'overview' })
  const { data: users = [], refetch: refetchUsers } = useQuery({ queryKey: ['admin-users'],  queryFn: adminApi.users, enabled: tab === 'users' })
  const { data: camps  = [], refetch: refetchCamps } = useQuery({ queryKey: ['admin-camps'],  queryFn: adminApi.allCampaigns, enabled: tab === 'campaigns' })
  const { data: sigs   = [], refetch: refetchSigs  } = useQuery({ queryKey: ['admin-sigs'],   queryFn: () => adminApi.allSignatures(), enabled: tab === 'signatures' })

  const createMut = useMutation({
    mutationFn: adminUserApi.create,
    onSuccess: () => { toast.success('User created'); qc.invalidateQueries(['admin-users']) },
    onError: e => toast.error(e?.response?.data?.detail || 'Failed to create user'),
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => adminUserApi.update(id, data),
    onSuccess: () => { toast.success('User updated'); qc.invalidateQueries(['admin-users']) },
    onError: e => toast.error(e?.response?.data?.detail || 'Failed to update user'),
  })
  const deleteMut = useMutation({
    mutationFn: adminUserApi.delete,
    onSuccess: () => { toast.success('User deleted'); qc.invalidateQueries(['admin-users']) },
    onError: e => toast.error(e?.response?.data?.detail || 'Cannot delete user'),
  })
  const toggleAdminMut  = useMutation({ mutationFn: adminApi.toggleAdmin,  onSuccess: () => qc.invalidateQueries(['admin-users']) })
  const toggleActiveMut = useMutation({ mutationFn: adminApi.toggleActive, onSuccess: () => qc.invalidateQueries(['admin-users']) })

  const { data: appSettings, refetch: refetchSettings } = useQuery({
    queryKey: ['admin-settings'],
    queryFn: adminApi.getSettings,
    enabled: tab === 'settings',
  })
  const settingsMut = useMutation({
    mutationFn: adminApi.updateSettings,
    onSuccess: (d) => {
      toast.success(d.registrations_open ? 'Registrations opened ✓' : 'Registrations closed ✓')
      qc.invalidateQueries(['admin-settings'])
    },
    onError: e => toast.error(e?.response?.data?.detail || 'Failed to update settings'),
  })

  const STATUS_COLORS = { completed: 'var(--success)', running: 'var(--warning)', failed: 'var(--error)', draft: 'var(--subtext)' }

  const TABS = [
    { id: 'overview',   label: '📊 Overview' },
    { id: 'users',      label: '👥 Users' },
    { id: 'campaigns',  label: '✉ All Campaigns' },
    { id: 'signatures', label: '🖋 Signatures' },
    { id: 'settings',   label: '⚙ Settings' },
  ]

  if (modal?.type === 'signature') {
    return <SignaturePage adminUserId={modal.user.id} adminUserEmail={modal.user.email} onBack={() => setModal(null)} />
  }

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 38, height: 38, borderRadius: 8, background: 'rgba(121,40,202,0.15)', border: '1px solid rgba(121,40,202,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldCheck size={18} color="#b97cf9" />
          </div>
          <div>
            <h1>Admin Panel</h1>
            <p>Manage users, monitor campaigns, platform health</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border)' }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            padding: '8px 16px', borderRadius: '6px 6px 0 0', border: '1px solid transparent',
            cursor: 'pointer', fontSize: 13, fontWeight: 500, marginBottom: -1,
            background: tab === t.id ? 'var(--card)' : 'transparent',
            color: tab === t.id ? '#b97cf9' : 'var(--subtext)',
            borderColor: tab === t.id ? 'var(--border)' : 'transparent',
            borderBottom: tab === t.id ? '2px solid #7928CA' : '2px solid transparent',
            transition: 'all 0.15s',
          }}>{t.label}</button>
        ))}
      </div>

      {/* ── Overview ── */}
      {tab === 'overview' && (
        <div>
          {stats && (
            <div className="res-grid-half" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 24 }}>
              {[
                { k: 'total_users',     l: 'Total Users',   c: '#b97cf9', i: '👥' },
                { k: 'total_campaigns', l: 'Campaigns',     c: 'var(--accent-lit)', i: '📋' },
                { k: 'total_sent',      l: 'Emails Sent',   c: 'var(--success)',    i: '✉' },
                { k: 'total_opened',    l: 'Opened',        c: 'var(--warning)',    i: '👁' },
                { k: 'total_failed',    l: 'Failed',        c: 'var(--error)',      i: '✗' },
              ].map(s => (
                <div key={s.k} className="stat-card">
                  <div style={{ fontSize: 20, marginBottom: 6 }}>{s.i}</div>
                  <div className="stat-value" style={{ color: s.c }}>{stats[s.k] ?? '—'}</div>
                  <div className="stat-label">{s.l}</div>
                </div>
              ))}
            </div>
          )}
          {stats && stats.total_sent > 0 && (
            <div className="card" style={{ maxWidth: 500 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 14 }}>Platform Health</h3>
              {[
                { label: 'Open Rate',     val: Math.round((stats.total_opened / stats.total_sent) * 100), color: 'var(--accent-lit)' },
                { label: 'Failure Rate',  val: Math.round((stats.total_failed / (stats.total_sent + stats.total_failed || 1)) * 100), color: 'var(--error)' },
              ].map(m => (
                <div key={m.label} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 5 }}>
                    <span style={{ color: 'var(--subtext)' }}>{m.label}</span>
                    <span style={{ fontWeight: 700, color: m.color }}>{m.val}%</span>
                  </div>
                  <div style={{ height: 6, background: 'var(--surface)', borderRadius: 3, overflow: 'hidden', border: '1px solid var(--border)' }}>
                    <div style={{ height: '100%', width: `${m.val}%`, background: m.color, borderRadius: 3, transition: 'width 0.5s' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
          {!stats && <div style={{ textAlign: 'center', padding: 40, color: 'var(--subtext)' }}><span className="spinner" /></div>}
        </div>
      )}

      {/* ── Users ── */}
      {tab === 'users' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <span style={{ fontSize: 13, color: 'var(--subtext)' }}>{users.length} users total</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-secondary" onClick={refetchUsers}
                style={{ fontSize: 12, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 5 }}>
                <RefreshCw size={13} /> Refresh
              </button>
              <button className="btn-primary" onClick={() => setModal('new')}
                style={{ fontSize: 12, padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 5 }}>
                <Plus size={13} /> Add User
              </button>
            </div>
          </div>

          <div style={{ borderRadius: 10, border: '1px solid var(--border)', overflow: 'hidden' }}>
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Name</th><th>Email</th><th>Role</th>
                  <th>Status</th><th>Campaigns</th><th>Sent</th><th>Created</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td style={{ color: 'var(--subtext)', fontSize: 11 }}>{u.id}</td>
                    <td style={{ fontWeight: 500 }}>{u.full_name}</td>
                    <td style={{ fontSize: 12, fontFamily: 'var(--mono)' }}>{u.email}</td>
                    <td><span className={`badge ${u.is_admin ? 'badge-purple' : 'badge-info'}`}>{u.is_admin ? '🛡 Admin' : 'User'}</span></td>
                    <td><span className={`badge ${u.is_active ? 'badge-success' : 'badge-error'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td style={{ textAlign: 'center' }}>{u.campaigns}</td>
                    <td style={{ textAlign: 'center' }}>{u.emails_sent}</td>
                    <td style={{ fontSize: 11, color: 'var(--subtext)', whiteSpace: 'nowrap' }}>
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button className="btn-icon" onClick={() => setModal({ type: 'signature', user: u })} title="Edit signature" style={{ width: 26, height: 26, color: 'var(--accent-lit)' }}>
                          <PenTool size={12} />
                        </button>
                        <button className="btn-icon" onClick={() => setModal(u)} title="Edit user details" style={{ width: 26, height: 26 }}>
                          <Edit2 size={12} />
                        </button>
                        <button className="btn-icon" onClick={() => toggleAdminMut.mutate(u.id)}
                          title={u.is_admin ? 'Remove admin' : 'Make admin'}
                          style={{ width: 26, height: 26, color: u.is_admin ? '#b97cf9' : 'var(--subtext)' }}>
                          <ShieldCheck size={12} />
                        </button>
                        <button className="btn-icon" onClick={() => toggleActiveMut.mutate(u.id)}
                          title={u.is_active ? 'Deactivate' : 'Activate'}
                          style={{ width: 26, height: 26, color: u.is_active ? 'var(--success)' : 'var(--error)' }}>
                          {u.is_active ? <UserCheck size={12} /> : <UserX size={12} />}
                        </button>
                        {u.id !== me?.id && (
                          <button className="btn-icon" onClick={() => {
                            if (confirm(`Delete user ${u.email}? This cannot be undone.`)) deleteMut.mutate(u.id)
                          }} title="Delete user permanently"
                            style={{ width: 26, height: 26, color: 'var(--error)' }}>
                            <Trash2 size={12} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Campaigns ── */}
      {tab === 'campaigns' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
            <button className="btn-secondary" onClick={refetchCamps}
              style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
              <RefreshCw size={13} /> Refresh
            </button>
          </div>
          <div style={{ borderRadius: 10, border: '1px solid var(--border)', overflow: 'hidden' }}>
            <table>
              <thead>
                <tr><th>ID</th><th>Campaign</th><th>Owner</th><th>Status</th><th>Total</th><th>Sent</th><th>Opened</th><th>Failed</th><th>Open%</th><th>Created</th></tr>
              </thead>
              <tbody>
                {camps.map(c => {
                  const openR = c.sent_count > 0 ? Math.round((c.opened_count / c.sent_count) * 100) : 0
                  return (
                    <tr key={c.id}>
                      <td style={{ color: 'var(--subtext)', fontSize: 11 }}>{c.id}</td>
                      <td style={{ fontWeight: 500, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name}</td>
                      <td style={{ fontSize: 12, color: 'var(--subtext)' }}>{c.user_email}</td>
                      <td><span style={{ fontSize: 11, fontWeight: 600, color: STATUS_COLORS[c.status] || 'var(--text)', textTransform: 'uppercase' }}>{c.status}</span></td>
                      <td style={{ textAlign: 'center' }}>{c.total_emails}</td>
                      <td style={{ textAlign: 'center', color: 'var(--success)', fontWeight: 600 }}>{c.sent_count}</td>
                      <td style={{ textAlign: 'center', color: 'var(--accent-lit)', fontWeight: 600 }}>{c.opened_count}</td>
                      <td style={{ textAlign: 'center', color: c.failed_count > 0 ? 'var(--error)' : 'var(--subtext)' }}>{c.failed_count}</td>
                      <td style={{ textAlign: 'center' }}>
                        <span style={{ fontSize: 12, color: openR > 20 ? 'var(--success)' : 'var(--subtext)', fontWeight: openR > 0 ? 600 : 400 }}>{openR}%</span>
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--subtext)', whiteSpace: 'nowrap' }}>{new Date(c.created_at).toLocaleDateString()}</td>
                    </tr>
                  )
                })}
                {!camps.length && (
                  <tr><td colSpan={10} style={{ textAlign: 'center', padding: 24, color: 'var(--subtext)' }}>No campaigns yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Signatures ── */}
      {tab === 'signatures' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
            <button className="btn-secondary" onClick={refetchSigs}
              style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
              <RefreshCw size={13} /> Refresh
            </button>
          </div>
          <div style={{ borderRadius: 10, border: '1px solid var(--border)', overflow: 'hidden' }}>
            <table>
              <thead>
                <tr><th>User ID</th><th>Email</th><th>Owner Name</th><th>Signature Label</th><th>Default</th><th>Company</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {sigs.map(s => (
                  <tr key={s.id}>
                    <td style={{ color: 'var(--subtext)', fontSize: 11 }}>{s.user_id}</td>
                    <td style={{ fontSize: 12, fontFamily: 'var(--mono)' }}>{s.user_email}</td>
                    <td style={{ fontWeight: 500 }}>{s.user_name}</td>
                    <td>{s.name}</td>
                    <td><span className={`badge ${s.is_default ? 'badge-success' : 'badge-warning'}`}>{s.is_default ? 'Yes' : 'No'}</span></td>
                    <td>{s.company || '—'}</td>
                    <td>
                      <button className="btn-secondary" onClick={() => setModal({ type: 'signature', user: { id: s.user_id, email: s.user_email } })} style={{ fontSize: 11, padding: '4px 10px' }}>
                        Edit Signature
                      </button>
                    </td>
                  </tr>
                ))}
                {!sigs.length && (
                  <tr><td colSpan={7} style={{ textAlign: 'center', padding: 24, color: 'var(--subtext)' }}>No signatures created yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Settings ── */}
      {tab === 'settings' && (
        <div style={{ maxWidth: 480 }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
              <Settings size={16} color="#b97cf9" />
              <h3 style={{ fontSize: 15, fontWeight: 700 }}>Platform Settings</h3>
            </div>

            {/* Registration toggle */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '16px 18px', borderRadius: 8,
              background: 'var(--surface)', border: '1px solid var(--border)',
            }}>
              <div>
                <p style={{ fontWeight: 600, fontSize: 14, marginBottom: 3 }}>Allow User Registrations</p>
                <p style={{ fontSize: 12, color: 'var(--subtext)', lineHeight: 1.5 }}>
                  When enabled, new users can sign up via the login page.<br />
                  Disable to lock down the platform.
                </p>
              </div>
              <div style={{ marginLeft: 20, flexShrink: 0 }}>
                {appSettings === undefined ? (
                  <span className="spinner" style={{ width: 18, height: 18 }} />
                ) : (
                  <button
                    id="btn-toggle-registrations"
                    type="button"
                    onClick={() => settingsMut.mutate({ registrations_open: !appSettings.registrations_open })}
                    disabled={settingsMut.isPending}
                    style={{
                      position: 'relative',
                      width: 48, height: 26, borderRadius: 13, border: 'none', cursor: 'pointer',
                      background: appSettings.registrations_open ? 'var(--success)' : 'rgba(255,255,255,0.15)',
                      transition: 'background 0.2s',
                      padding: 0,
                    }}
                    title={appSettings.registrations_open ? 'Click to disable registrations' : 'Click to enable registrations'}
                  >
                    <span style={{
                      position: 'absolute', top: 3,
                      left: appSettings.registrations_open ? 25 : 3,
                      width: 20, height: 20, borderRadius: '50%',
                      background: '#fff',
                      transition: 'left 0.2s',
                      boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
                    }} />
                  </button>
                )}
              </div>
            </div>

            <p style={{ fontSize: 11, color: 'var(--subtext)', marginTop: 10 }}>
              Current status:{' '}
              <strong style={{ color: appSettings?.registrations_open ? 'var(--success)' : 'var(--error)' }}>
                {appSettings?.registrations_open ? 'Open — users can register' : 'Closed — registration disabled'}
              </strong>
            </p>
          </div>
        </div>
      )}

      {/* Modal */}
      {modal && modal.type !== 'signature' && (
        <UserModal
          user={modal === 'new' ? null : modal}
          onClose={() => setModal(null)}
          onSave={async (formData) => {
            if (modal === 'new') {
              await createMut.mutateAsync(formData)
            } else {
              const payload = { ...formData }
              if (!payload.password) delete payload.password
              await updateMut.mutateAsync({ id: modal.id, data: payload })
            }
          }}
        />
      )}
    </div>
  )
}
