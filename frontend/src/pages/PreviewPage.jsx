import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { templatesApi, signatureApi } from '../utils/api'
import { useData } from '../context/DataContext'
import { Eye, Mail, Paperclip, Tag } from 'lucide-react'
import { buildPreviewHtml } from './SignaturePage'


function getPreviewDoc(bodyHtml) {
  const body = bodyHtml || '<p style="color:#8b949e;font-style:italic">No content yet</p>'
  return [
    '<!DOCTYPE html><html><head><meta charset="utf-8"><style>',
    'body{font-family:Arial,sans-serif;padding:24px;color:#1f2328;line-height:1.7;margin:0;font-size:14px;background:#fff}',
    'table{border-collapse:collapse!important;width:100%;margin:8px 0}',
    'td,th{border:1px solid #aaa!important;padding:7px 12px!important;background:#fff!important;color:#222!important;font-size:13px}',
    'th{background:#eee!important;font-weight:600!important;color:#111!important}',
    'a{color:#0969da} hr{border:none;border-top:1px solid #d0d7de;margin:14px 0}',
    'h1,h2,h3{margin:0 0 8px 0;color:#1f2328} p{margin:0 0 8px 0}',
    '</style></head><body>',
    body,
    '</body></html>',
  ].join('')
}

function substituteVars(text, variables) {
  if (!text) return ''
  return text.replace(/\{\{(\w+)\}\}/g, (_, key) => variables[key] ?? `{{${key}}}`)
}

export default function PreviewPage() {
  const [templateIdx, setTemplateIdx] = useState(0)
  const [contactIdx,  setContactIdx]  = useState(0)

  const { data: templates = [] } = useQuery({ queryKey: ['templates'], queryFn: templatesApi.list })
  const { data: sig } = useQuery({ queryKey: ['my-sig'], queryFn: () => signatureApi.get().catch(() => null) })
  const { contacts: ctxContacts } = useData()

  const contacts = ctxContacts.length ? ctxContacts : [
    { email: 'john.doe@example.com', variables: { name: 'John Doe', company: 'Acme Corp', position: 'Manager' }, cc_emails: [] }
  ]

  const template = templates[templateIdx]
  const contact  = contacts[Math.min(contactIdx, contacts.length - 1)]
  const vars     = contact?.variables || {}

  const subject  = template ? substituteVars(template.subject,   vars) : ''
  let bodyHtml   = template ? substituteVars(template.body_html, vars) : ''

  if (bodyHtml) {
    bodyHtml = bodyHtml.replace(/<table\b([^>]*)>/gi, '<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; border: 1px solid #dddddd;" $1>')
    bodyHtml = bodyHtml.replace(/<td\b([^>]*)>/gi, '<td style="border: 1px solid #dddddd; padding: 6px;" $1>')
    bodyHtml = bodyHtml.replace(/<th\b([^>]*)>/gi, '<th style="border: 1px solid #dddddd; padding: 6px;" $1>')
  }

  if (sig?.exists && sig?.is_default) {
    bodyHtml += '<br>' + buildPreviewHtml(sig)
  }

  if (template?.attachments?.length) {
    bodyHtml += '<div style="margin-top: 30px; padding-top: 15px; border-top: 1px dashed #ccc; font-family: Arial, sans-serif;">'
    bodyHtml += '<strong style="font-size: 13px; color: #555;">Attachments:</strong><div style="display:flex; flex-wrap:wrap; gap: 10px; margin-top: 10px;">'
    template.attachments.forEach(a => {
      bodyHtml += `<div style="padding: 8px 12px; border: 1px solid #ddd; background: #f9f9f9; border-radius: 6px; font-size: 12px; color: #444; display: flex; align-items: center; gap: 6px;"><span style="font-size: 14px;">📎</span> ${a.original_filename}</div>`
    })
    bodyHtml += '</div></div>'
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Email Preview</h1>
        <p>See exactly how your email looks with real variable values substituted</p>
      </div>

      {/* Selectors */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 20, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <label className="label">Template</label>
          <select value={templateIdx} onChange={e => setTemplateIdx(+e.target.value)}>
            {templates.map((t, i) => <option key={t.id} value={i}>{t.name}</option>)}
            {!templates.length && <option value={0}>No templates yet — create one first</option>}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <label className="label">Recipient ({contacts.length} loaded)</label>
          <select value={contactIdx} onChange={e => setContactIdx(+e.target.value)}>
            {contacts.map((c, i) => <option key={i} value={i}>{c.email}</option>)}
          </select>
        </div>
        {!ctxContacts.length && (
          <div style={{ fontSize: 12, color: 'var(--warning)', padding: '8px 12px', background: 'rgba(210,153,34,0.08)', borderRadius: 6, border: '1px solid rgba(210,153,34,0.25)' }}>
            ⚠ Using sample data — go to Data & Variables to load real contacts
          </div>
        )}
      </div>

      {template ? (
        <div className="res-grid" style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 20, alignItems: 'start' }}>
          {/* Meta sidebar */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="card" style={{ padding: '14px 16px' }}>
              <div className="label" style={{ marginBottom: 8 }}>Email Info</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--subtext)', marginBottom: 2 }}>TO</div>
                  <div style={{ fontSize: 13, fontFamily: 'var(--mono)', color: 'var(--accent-lit)' }}>{contact?.email}</div>
                </div>
                {contact?.cc_emails?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--subtext)', marginBottom: 2 }}>CC</div>
                    <div style={{ fontSize: 12, color: 'var(--subtext)' }}>{contact.cc_emails.join(', ')}</div>
                  </div>
                )}
                <div>
                  <div style={{ fontSize: 11, color: 'var(--subtext)', marginBottom: 2 }}>FROM</div>
                  <div style={{ fontSize: 12, color: 'var(--subtext)' }}>Your Gmail (OAuth)</div>
                </div>
              </div>
            </div>

            {/* Variable values */}
            {Object.keys(vars).length > 0 && (
              <div className="card" style={{ padding: '14px 16px' }}>
                <div className="label" style={{ marginBottom: 8 }}>Variable Values</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {Object.entries(vars).map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', gap: 8, fontSize: 12, padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
                      <code style={{ color: 'var(--accent-lit)', fontFamily: 'var(--mono)', flexShrink: 0 }}>{`{{${k}}}`}</code>
                      <span style={{ color: 'var(--text)', textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 130 }} title={v}>{v || '—'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Attachments */}
            {template.attachments?.length > 0 && (
              <div className="card" style={{ padding: '14px 16px' }}>
                <div className="label" style={{ marginBottom: 8 }}>Attachments</div>
                {template.attachments.map(a => (
                  <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--subtext)', padding: '3px 0' }}>
                    <Paperclip size={11} /> {a.original_filename}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Email preview */}
          <div>
            {/* Subject bar */}
            <div style={{ padding: '12px 18px', background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '10px 10px 0 0', borderBottom: 'none' }}>
              <div style={{ fontSize: 11, color: 'var(--subtext)', marginBottom: 3, textTransform: 'uppercase', letterSpacing: 0.5 }}>Subject</div>
              <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text)' }}>{subject || '(empty subject)'}</div>
            </div>
            {/* Body iframe */}
            <div style={{ background: 'white', border: '1px solid var(--border)', borderRadius: '0 0 10px 10px', overflow: 'hidden' }}>
              <iframe
                srcDoc={getPreviewDoc(bodyHtml)}
                style={{ width: '100%', minHeight: 450, border: 'none', display: 'block' }}
                title="Email Preview"
                sandbox="allow-same-origin"
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: 60, color: 'var(--subtext)' }}>
          <Eye size={36} style={{ marginBottom: 14, opacity: 0.2 }} />
          <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>No template selected</div>
          <div style={{ fontSize: 12 }}>Create a template first, then come back to preview it here</div>
        </div>
      )}
    </div>
  )
}
