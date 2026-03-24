import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi, campaignsApi } from '../utils/api'
import { Send, CheckCircle, XCircle, Clock, Loader, AlertTriangle, Plus, Trash2, RefreshCw, StopCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { useData } from '../context/DataContext'

const STATUS_CONFIG = {
  pending:  { color: 'var(--subtext)', icon: Clock,        label: 'Pending'  },
  sending:  { color: 'var(--warning)', icon: Loader,       label: 'Sending'  },
  sent:     { color: 'var(--success)', icon: CheckCircle,  label: 'Sent'     },
  failed:   { color: 'var(--error)',   icon: XCircle,      label: 'Failed'   },
  opened:   { color: 'var(--accent-lit)', icon: CheckCircle, label: 'Opened' },
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending
  const Icon = cfg.icon
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4,
      fontSize: 11, fontWeight: 600, color: cfg.color, textTransform: 'uppercase' }}>
      <Icon size={11} className={status === 'sending' ? 'pulse' : ''} />
      {cfg.label}
    </span>
  )
}

export default function SendPage() {
  const qc = useQueryClient()
  const [campaignName, setCampaignName]   = useState('')
  const [templateIdx, setTemplateIdx]     = useState(0)
  const [extraAttIds, setExtraAttIds]     = useState([])
  const [campaign, setCampaign]           = useState(null)
  const [logs, setLogs]                   = useState([])
  const [polling, setPolling]             = useState(false)
  const [ccInputs, setCcInputs]           = useState([''])
  const [campaignStatus, setCampaignStatus] = useState('')
  const pollRef = useRef(null)
  const toastIdRef = useRef(null)

  const { data: templates = [] }    = useQuery({ queryKey: ['templates'],    queryFn: templatesApi.list })
  const { data: attachments = [] }  = useQuery({ queryKey: ['attachments'],  queryFn: templatesApi.listAttachments })

  const { contacts, varNames } = useData()
  const ccs       = ccInputs.filter(Boolean)
  const contactsWithCc = contacts.map(c => ({ ...c, cc_emails: ccs }))

  // ── Create + start campaign ──────────────────────────────────────
  const createAndSend = useMutation({
    mutationFn: async () => {
      if (!campaignName.trim()) throw new Error('Campaign name is required')
      if (!contacts.length)    throw new Error('No contacts loaded — go to Data & Variables first')
      const t = templates[templateIdx]
      if (!t) throw new Error('No template selected')

      const camp = await campaignsApi.create({
        name:                 campaignName.trim(),
        template_id:          t.id,
        contacts:             contactsWithCc,
        variable_names:       varNames,
        extra_attachment_ids: extraAttIds,
      })
      await campaignsApi.start(camp.id)
      return camp
    },
    onSuccess: (camp) => {
      setCampaign(camp)
      setCampaignStatus('running')
      setLogs([])
      setPolling(true)
      toast.dismiss()
      toast.success('Campaign started! Emails are being sent...', { duration: 4000 })
    },
    onError: (err) => {
      const msg = err?.response?.data?.detail || err.message || 'Failed to start campaign'
      toast.error(msg)
    },
  })

  // ── Poll for live updates ────────────────────────────────────────
  useEffect(() => {
    if (!polling || !campaign) return

    const poll = async () => {
      try {
        // Fetch logs
        const updatedLogs = await campaignsApi.logs(campaign.id)
        setLogs(updatedLogs)

        // Fetch campaign status separately
        const camps = await campaignsApi.list()
        const updated = camps.find(c => c.id === campaign.id)
        if (updated) {
          setCampaignStatus(updated.status)
          setCampaign(prev => ({ ...prev, ...updated }))

          // Stop polling when done
          if (['completed', 'failed'].includes(updated.status)) {
            setPolling(false)
            clearInterval(pollRef.current)
            toast.dismiss()
            if (updated.status === 'completed') {
              toast.success(`✅ Done! Sent: ${updated.sent_count}, Failed: ${updated.failed_count}`)
            } else {
              toast.error('Campaign failed — check the log for details')
            }
            qc.invalidateQueries(['campaigns'])
            return
          }
        }

        // Also stop if all logs are in a terminal state
        if (updatedLogs.length > 0) {
          const allTerminal = updatedLogs.every(l =>
            ['sent', 'failed', 'opened'].includes(l.status)
          )
          if (allTerminal) {
            setPolling(false)
            clearInterval(pollRef.current)
            toast.dismiss()
            toast.success('Campaign complete!')
            qc.invalidateQueries(['campaigns'])
          }
        }
      } catch (e) {
        console.error('Polling error:', e)
      }
    }

    poll() // immediate first call
    pollRef.current = setInterval(poll, 3000)
    return () => clearInterval(pollRef.current)
  }, [polling, campaign])

  const stopPolling = () => {
    setPolling(false)
    clearInterval(pollRef.current)
  }

  const resetForm = () => {
    setCampaign(null)
    setLogs([])
    setPolling(false)
    setCampaignStatus('')
    setCampaignName('')
  }

  // ── Computed stats ───────────────────────────────────────────────
  const sent    = logs.filter(l => ['sent', 'opened'].includes(l.status)).length
  const failed  = logs.filter(l => l.status === 'failed').length
  const sending = logs.filter(l => l.status === 'sending').length
  const pending = logs.filter(l => l.status === 'pending').length
  const total   = campaign?.total_emails || contacts.length
  const progress = total > 0 ? Math.round(((sent + failed) / total) * 100) : 0

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Send Email Campaign</h1>
        <p>Configure and launch your email campaign with live status tracking</p>
      </div>

      <div className="res-grid" style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 20, alignItems: 'start' }}>

        {/* ── Left: Config ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 14 }}>Campaign Setup</h3>

            <div className="form-row">
              <label>Campaign Name *</label>
              <input value={campaignName} onChange={e => setCampaignName(e.target.value)}
                placeholder="Q1 Outreach 2025" disabled={polling} />
            </div>

            <div className="form-row">
              <label>Template *</label>
              <select value={templateIdx} onChange={e => setTemplateIdx(+e.target.value)} disabled={polling}>
                {templates.map((t, i) => <option key={t.id} value={i}>{t.name}</option>)}
                {!templates.length && <option value={-1}>— No templates yet —</option>}
              </select>
            </div>

            {/* Recipients */}
            <div style={{ padding: '10px 12px', background: 'var(--surface)', borderRadius: 6, border: `1px solid ${contacts.length ? 'rgba(0,230,118,0.3)' : 'var(--border)'}`, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: 'var(--subtext)', marginBottom: 3 }}>Recipients loaded</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: contacts.length ? 'var(--success)' : 'var(--warning)' }}>
                {contacts.length}
                {!contacts.length && <span style={{ fontSize: 11, fontWeight: 400, marginLeft: 8 }}>go to Data & Variables</span>}
              </div>
            </div>

            {/* CC — global CC applied to all emails */}
            <div className="form-row">
              <label>CC Recipients <span style={{ fontWeight: 400, color: 'var(--subtext)', fontSize: 11 }}>(applies to every email in this campaign)</span></label>
              {ccInputs.map((cc, i) => (
                <div key={i} style={{ display: 'flex', gap: 6, marginBottom: 5 }}>
                  <input value={cc}
                    onChange={e => setCcInputs(p => { const n=[...p]; n[i]=e.target.value; return n })}
                    placeholder="cc@company.com" disabled={polling} />
                  <button onClick={() => setCcInputs(p => p.filter((_, j) => j !== i))}
                    title="Remove this CC"
                    style={{ background: 'none', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 6, padding: '0 8px', color: 'var(--error)', cursor: 'pointer', flexShrink: 0 }}>
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                <button onClick={() => setCcInputs(p => [...p, ''])}
                  style={{ background: 'none', border: 'none', color: 'var(--accent-lit)', cursor: 'pointer', fontSize: 12, padding: '2px 0', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Plus size={12} /> Add CC Email
                </button>
                {ccInputs.some(Boolean) && (
                  <button onClick={() => setCcInputs([''])}
                    style={{ background: 'none', border: 'none', color: 'var(--error)', cursor: 'pointer', fontSize: 12, padding: '2px 0' }}>
                    Clear all CC
                  </button>
                )}
              </div>
              {ccInputs.some(Boolean) && (
                <div style={{ marginTop: 6, fontSize: 11, color: 'var(--subtext)', padding: '4px 8px', background: 'rgba(255,255,255,0.04)', borderRadius: 4 }}>
                  💡 These CC addresses will receive a copy of every email in this campaign.
                </div>
              )}
            </div>

            {/* Extra attachments */}
            {attachments.length > 0 && (
              <div className="form-row">
                <label>Extra Attachments</label>
                {attachments.map(a => {
                  const sel = extraAttIds.includes(a.id)
                  return (
                    <label key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, marginBottom: 4 }}>
                      <input type="checkbox" checked={sel}
                        onChange={() => setExtraAttIds(p => sel ? p.filter(id => id !== a.id) : [...p, a.id])}
                        disabled={polling} style={{ width: 14, height: 14 }} />
                      {a.original_filename}
                    </label>
                  )
                })}
              </div>
            )}

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <button className="btn-primary"
                onClick={() => createAndSend.mutate()}
                disabled={polling || createAndSend.isPending || !contacts.length || !templates.length}
                title="Start sending emails to all loaded contacts"
                style={{ flex: 1, padding: '11px', fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                {polling
                  ? <><span className="spinner" style={{ width: 15, height: 15 }} /> Sending...</>
                  : <><Send size={14} /> Start Campaign</>}
              </button>

              {campaign && !polling && (
                <button className="btn-secondary" onClick={resetForm} title="Reset and start a new campaign"
                  style={{ padding: '11px 14px', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                  <RefreshCw size={13} /> New
                </button>
              )}
            </div>

            {!contacts.length && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--warning)', marginTop: 10 }}>
                <AlertTriangle size={13} /> Load contacts in Data & Variables first
              </div>
            )}
          </div>

          {/* Send info card */}
          <div className="card" style={{ padding: '14px 16px' }}>
            <div className="label" style={{ marginBottom: 8 }}>Send Configuration</div>
            {[
              ['Delay between emails', `${settings?.SEND_DELAY_SECONDS || 3}s`],
              ['Sending via', 'Gmail API (OAuth)'],
              ['Tracking', 'Open pixel'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '5px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--subtext)' }}>{k}</span>
                <span style={{ fontWeight: 500 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Right: Live status ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Stats */}
          <div className="res-grid-half" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10 }}>
            {[
              { label: 'Total',   value: total,   color: 'var(--text)' },
              { label: 'Sent',    value: sent,     color: 'var(--success)' },
              { label: 'Failed',  value: failed,   color: 'var(--error)' },
              { label: 'Sending', value: sending,  color: 'var(--warning)' },
              { label: 'Pending', value: pending,  color: 'var(--subtext)' },
            ].map(s => (
              <div key={s.label} className="stat-card" style={{ padding: '12px 14px' }}>
                <div className="stat-value" style={{ color: s.color, fontSize: 20 }}>{s.value}</div>
                <div className="stat-label">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Progress */}
          {campaign && (
            <div className="card" style={{ padding: '14px 16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {polling && <span className="spinner" style={{ width: 14, height: 14 }} />}
                  <span style={{ fontSize: 13, fontWeight: 500 }}>
                    {polling ? 'Sending in progress...' : `Campaign ${campaignStatus}`}
                  </span>
                  <span className={`badge badge-${campaignStatus === 'completed' ? 'success' : campaignStatus === 'failed' ? 'error' : campaignStatus === 'running' ? 'warning' : 'info'}`}>
                    {campaignStatus}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 13, fontWeight: 700 }}>{progress}%</span>
                  {polling && (
                    <button className="btn-secondary" onClick={stopPolling}
                      title="Stop watching (does not cancel sending)"
                      style={{ fontSize: 11, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <StopCircle size={12} /> Stop watching
                    </button>
                  )}
                </div>
              </div>
              <div style={{ height: 10, background: 'var(--surface)', borderRadius: 5, overflow: 'hidden', border: '1px solid var(--border)' }}>
                <div style={{
                  height: '100%', borderRadius: 5, transition: 'width 0.4s ease',
                  width: `${progress}%`,
                  background: failed > 0 && sent === 0
                    ? 'var(--error)'
                    : 'linear-gradient(90deg, var(--accent), #4a6fa5)',
                }} />
              </div>
              <div style={{ fontSize: 11, color: 'var(--subtext)', marginTop: 6 }}>
                {sent} sent · {failed} failed · {sending} sending · {pending} pending
              </div>
            </div>
          )}

          {/* Log table */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Send Log</span>
                {polling && <span className="spinner" style={{ width: 13, height: 13 }} />}
                {logs.length > 0 && <span style={{ fontSize: 11, color: 'var(--subtext)' }}>{logs.length} entries</span>}
              </div>
              {campaign && (
                <button className="btn-secondary" onClick={async () => {
                  const l = await campaignsApi.logs(campaign.id)
                  setLogs(l)
                  toast.success('Refreshed')
                }} title="Manually refresh log" style={{ fontSize: 11, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <RefreshCw size={11} /> Refresh
                </button>
              )}
            </div>

            {logs.length > 0 ? (
              <div style={{ overflowY: 'auto', maxHeight: 500 }}>
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Recipient</th>
                      <th>CC</th>
                      <th>Status</th>
                      <th>Sent At</th>
                      <th>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log, idx) => (
                      <tr key={log.id}>
                        <td style={{ color: 'var(--subtext)', fontSize: 11, width: 32 }}>{idx + 1}</td>
                        <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>{log.recipient_email}</td>
                        <td style={{ fontSize: 11, color: 'var(--subtext)' }}>{log.cc_emails?.join(', ') || '—'}</td>
                        <td><StatusBadge status={log.status} /></td>
                        <td style={{ fontSize: 11, color: 'var(--subtext)', whiteSpace: 'nowrap' }}>
                          {log.sent_at ? new Date(log.sent_at).toLocaleTimeString() : '—'}
                        </td>
                        <td style={{ fontSize: 11, color: 'var(--error)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {log.error_message || ''}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ padding: 48, textAlign: 'center', color: 'var(--subtext)' }}>
                <Send size={32} style={{ marginBottom: 12, opacity: 0.2 }} />
                <div style={{ fontSize: 13, marginBottom: 4 }}>No emails sent yet</div>
                <div style={{ fontSize: 11 }}>Start a campaign to see live results here</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// expose settings for delay display
const settings = { SEND_DELAY_SECONDS: 3 }
