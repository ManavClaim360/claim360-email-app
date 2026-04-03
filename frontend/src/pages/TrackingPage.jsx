import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { campaignsApi } from '../utils/api'
import { BarChart2, RefreshCw, CheckCircle, XCircle, Eye, Clock, Mail, Trash2 } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

const STATUS_COLORS = {
  sent:    'var(--success)',
  opened:  'var(--accent)',
  failed:  'var(--error)',
  pending: 'var(--subtext)',
  sending: 'var(--warning)',
}

export default function TrackingPage() {
  const qc = useQueryClient()
  const [selectedId, setSelectedId] = useState(null)

  const { data: campaigns = [], refetch } = useQuery({
    queryKey: ['campaigns'],
    queryFn: campaignsApi.list,
    // Only poll while there's a running campaign
    refetchInterval: (dataOrQuery) => {
      const arr = Array.isArray(dataOrQuery) ? dataOrQuery : dataOrQuery?.state?.data
      return Array.isArray(arr) && arr.some(c => c.status === 'running') ? 8000 : false
    },
  })

  const selected = campaigns.find(c => c.id === selectedId)

  const { data: logs = [], isLoading: logsLoading } = useQuery({
    queryKey: ['campaign-logs', selectedId],
    queryFn: () => campaignsApi.logs(selectedId),
    enabled: !!selectedId,
    // Only poll logs while the selected campaign is actively running
    refetchInterval: selected?.status === 'running' ? 4000 : false,
  })

  const deleteMut = useMutation({
    mutationFn: campaignsApi.delete,
    onSuccess: () => {
      toast.success('Campaign deleted')
      setSelectedId(null)
      qc.invalidateQueries(['campaigns'])
    },
  })

  const STATUS_BADGE = (status) => {
    const map = {
      draft: { cls: 'badge-info', label: 'Draft' },
      running: { cls: 'badge-warning', label: 'Running' },
      completed: { cls: 'badge-success', label: 'Completed' },
      failed: { cls: 'badge-error', label: 'Failed' },
    }
    const cfg = map[status] || { cls: 'badge-info', label: status }
    return <span className={`badge ${cfg.cls}`}>{cfg.label}</span>
  }

  const openRate = selected
    ? selected.sent_count > 0
      ? Math.round((selected.opened_count / selected.sent_count) * 100)
      : 0
    : null

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1>Tracking & Logs</h1>
          <p>Monitor campaign performance and email open rates</p>
        </div>
        <button className="btn-secondary" onClick={() => refetch()} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      <div className="res-grid" style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20, alignItems: 'start' }}>
        {/* Campaign list */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Campaigns ({campaigns.length})</span>
          </div>
          <div style={{ maxHeight: 600, overflowY: 'auto' }}>
            {campaigns.map(c => (
              <div key={c.id} onClick={() => setSelectedId(c.id)} style={{
                padding: '12px 16px', cursor: 'pointer', borderBottom: '1px solid var(--border)',
                background: selectedId === c.id ? 'rgba(0,212,255,0.06)' : 'transparent',
                borderLeft: `3px solid ${selectedId === c.id ? 'var(--accent)' : 'transparent'}`,
                transition: 'all 0.1s',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 500 }}>{c.name}</span>
                  {STATUS_BADGE(c.status)}
                </div>
                <div style={{ fontSize: 11, color: 'var(--subtext)', display: 'flex', gap: 10 }}>
                  <span>📧 {c.total_emails}</span>
                  <span style={{ color: 'var(--success)' }}>✓ {c.sent_count}</span>
                  <span style={{ color: 'var(--accent)' }}>👁 {c.opened_count}</span>
                  {c.failed_count > 0 && <span style={{ color: 'var(--error)' }}>✗ {c.failed_count}</span>}
                </div>
              </div>
            ))}
            {!campaigns.length && (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--subtext)', fontSize: 13 }}>
                No campaigns yet
              </div>
            )}
          </div>
        </div>

        {/* Detail panel */}
        {selected ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h2 style={{ fontSize: 17, fontWeight: 700 }}>{selected.name}</h2>
                <div style={{ fontSize: 12, color: 'var(--subtext)', marginTop: 2 }}>
                  Created {new Date(selected.created_at).toLocaleDateString()}
                  {' · '}{STATUS_BADGE(selected.status)}
                </div>
              </div>
              <button className="btn-danger" onClick={() => deleteMut.mutate(selected.id)}
                style={{ fontSize: 12, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Trash2 size={13} /> Delete
              </button>
            </div>

            {/* Stats */}
            <div className="tracking-stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }}>
              {[
                { label: 'Total',   value: selected.total_emails,  color: 'var(--text)' },
                { label: 'Sent',    value: selected.sent_count,    color: 'var(--success)' },
                { label: 'Opened',  value: selected.opened_count,  color: 'var(--accent)' },
                { label: 'Failed',  value: selected.failed_count,  color: 'var(--error)' },
                { label: 'Open Rate', value: `${openRate}%`,       color: 'var(--warning)' },
              ].map(s => (
                <div key={s.label} className="stat-card" style={{ padding: '12px 14px' }}>
                  <div className="stat-value" style={{ color: s.color, fontSize: 20 }}>{s.value}</div>
                  <div className="stat-label">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Open rate bar */}
            <div style={{ padding: '12px 16px', background: 'var(--card)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
                <span style={{ color: 'var(--subtext)' }}>Open Rate</span>
                <span style={{ fontWeight: 600, color: 'var(--accent)' }}>{openRate}%</span>
              </div>
              <div style={{ height: 6, background: 'var(--surface)', borderRadius: 3, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${openRate}%`, borderRadius: 3, background: 'linear-gradient(90deg, var(--accent2), var(--accent))', transition: 'width 0.5s' }} />
              </div>
            </div>

            {/* Email log table */}
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Email Log ({logs.length})</span>
                {logsLoading && <span className="spinner" style={{ width: 14, height: 14 }} />}
              </div>
              <div style={{ overflowY: 'auto', maxHeight: 400 }}>
                {logsLoading ? (
                  <div style={{ padding: 30, textAlign: 'center' }}><span className="spinner" /></div>
                ) : logs.length ? (
                  <table>
                    <thead>
                      <tr>
                        <th>Recipient</th>
                        <th>CC</th>
                        <th>Status</th>
                        <th>Sent At</th>
                        <th>Opened At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map(log => (
                        <tr key={log.id}>
                          <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>{log.recipient_email}</td>
                          <td style={{ fontSize: 12, color: 'var(--subtext)' }}>{log.cc_emails?.join(', ') || '—'}</td>
                          <td>
                            <span style={{ fontSize: 11, fontWeight: 600, color: STATUS_COLORS[log.status] || 'var(--text)', textTransform: 'uppercase' }}>
                              {log.status}
                            </span>
                          </td>
                          <td style={{ fontSize: 12, color: 'var(--subtext)' }}>
                            {log.sent_at ? new Date(log.sent_at).toLocaleString() : '—'}
                          </td>
                          <td style={{ fontSize: 12, color: log.opened_at ? 'var(--accent)' : 'var(--subtext)' }}>
                            {log.opened_at ? new Date(log.opened_at).toLocaleString() : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div style={{ padding: 24, textAlign: 'center', color: 'var(--subtext)', fontSize: 13 }}>No logs yet</div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="card" style={{ textAlign: 'center', padding: 60, color: 'var(--subtext)' }}>
            <BarChart2 size={36} style={{ marginBottom: 12, opacity: 0.3 }} />
            <div>Select a campaign to view tracking details</div>
          </div>
        )}
      </div>
    </div>
  )
}
