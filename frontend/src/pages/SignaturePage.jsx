import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../utils/api'
import { Save, Trash2, Eye, EyeOff, User, Phone, MapPin, Shield, Share2, Upload, X } from 'lucide-react'
import toast from 'react-hot-toast'

const sigApi = {
  get: (u) => u ? api.get(`/api/signatures/admin/${u}`).then(r => r.data).catch(() => ({ exists: false })) : api.get('/api/signatures/me').then(r => r.data).catch(() => ({ exists: false })),
  save: (u, data) => u ? api.put(`/api/signatures/admin/${u}`, data).then(r => r.data) : api.post('/api/signatures/me', data).then(r => r.data),
  delete: (u) => u ? api.delete(`/api/signatures/admin/${u}`).then(r => r.data) : api.delete('/api/signatures/me').then(r => r.data),
}

const EMPTY = {
  name: 'My Signature', is_default: true,
  full_name: '', title: '', company: 'CLAIM 360',
  phone: '', email_addr: '', website: 'www.claim360.in',
  address_mumbai: '311 Sun Industrial Estate, Sun Mill Compound, Lower Parel, Mumbai – 400013',
  address_delhi: 'D-4/4035, Vasant Kunj, New Delhi – 110070',
  address_london: '2 Wymondham, St. Johns Wood Park, London NW8 6RD',
  cin: 'U74999DL2016PTC303092',
  copyright_text: 'Copyright © 2026 360 Degrees Management. All rights reserved.',
  logo_url: '', brand_color: '#1C305E',
  social_links: { whatsapp_number: '', linkedin: '', location: '', twitter: '', instagram: '', facebook: '' },
}

// Brand Icons (Icons8 Grayscale)
const SOCIAL_CFG = [
  { key: 'linkedin', label: 'LinkedIn', src: 'https://img.icons8.com/ios-filled/50/666666/linkedin.png', ph: 'https://linkedin.com/in/yourprofile' },
  { key: 'location', label: 'Google Maps', src: 'https://img.icons8.com/ios-filled/50/666666/marker.png', ph: 'https://maps.google.com/?q=your+address' },
  { key: 'twitter', label: 'X / Twitter', src: 'https://img.icons8.com/ios-filled/50/666666/twitterx--v1.png', ph: 'https://twitter.com/yourhandle' },
  { key: 'instagram', label: 'Instagram', src: 'https://img.icons8.com/ios-filled/50/666666/instagram-new.png', ph: 'https://instagram.com/yourhandle' },
  { key: 'facebook', label: 'Facebook', src: 'https://img.icons8.com/ios-filled/50/666666/facebook-new.png', ph: 'https://facebook.com/yourpage' },
]

// Build signature HTML — mirrors backend exactly
export function buildPreviewHtml(f) {
  const color = f.brand_color || '#1C305E'
  const sl = f.social_links || {}
  const waNum = (sl.whatsapp_number || '').replace(/\D/g, '')

  let html = `<div style="padding-top:14px;border-top:2px solid ${color};font-family:Arial,sans-serif;max-width:560px">`

  if (f.logo_url) {
    // Logo left, all details right — single row table, no gaps
    html += `<table style="border:none!important;border-collapse:collapse;margin:0 0 6px 0;width:auto"><tr>`
    html += `<td style="border:none!important;vertical-align:top;padding:0 14px 0 0;background:transparent!important">`
    html += `<img src="${f.logo_url}" alt="${f.company || ''}" style="height:60px;width:auto;border-radius:6px;display:block" /></td>`
    html += `<td style="border:none!important;vertical-align:top;padding:0;background:transparent!important">`
    html += detailsHtml(f, color)
    html += `</td></tr></table>`
  } else {
    html += detailsHtml(f, color)
  }

  // Social buttons
  const btns = []
  if (waNum) btns.push({ url: `https://wa.me/${waNum}`, label: 'WhatsApp', src: 'https://img.icons8.com/ios-filled/50/666666/whatsapp--v1.png' })
  SOCIAL_CFG.forEach(s => {
    if (sl[s.key]) btns.push({ url: sl[s.key], label: s.label, src: s.src })
  })
  if (btns.length) {
    html += `<div style="margin-top:10px">`
    btns.forEach(b => {
      html += `<a href="${b.url}" title="${b.label}" style="display:inline-block;margin-right:8px;text-decoration:none"><img src="${b.src}" width="16" height="16" alt="${b.label}" style="display:block;border:none;border-radius:50%;background-color:#f5f5f5;padding:8px;" /></a>`
    })
    html += `</div>`
  }
  html += '</div>'
  return html
}

function detailsHtml(f, color) {
  let html = ''
  if (f.full_name) html += `<div style="font-size:16px;font-weight:700;color:${color};margin:0 0 1px">${f.full_name}</div>`
  if (f.title) html += `<div style="font-size:12px;color:#555;margin:0 0 1px">${f.title}</div>`
  if (f.company) html += `<div style="font-size:12px;font-weight:600;color:#333;margin:0 0 6px">${f.company}</div>`
  if (f.phone) html += `<div style="font-size:12px;color:#444;margin:2px 0">&#128222; <a href="tel:${f.phone}" style="color:#444;text-decoration:none">${f.phone}</a></div>`
  if (f.email_addr) html += `<div style="font-size:12px;color:#444;margin:2px 0">&#128231; <a href="mailto:${f.email_addr}" style="color:${color};text-decoration:none">${f.email_addr}</a></div>`
  if (f.website) html += `<div style="font-size:12px;color:#444;margin:2px 0">&#127759; <a href="https://${f.website}" style="color:${color};text-decoration:none">${f.website}</a></div>`
  const addrs = [['Mumbai', f.address_mumbai], ['Delhi', f.address_delhi], ['London', f.address_london]]
  addrs.forEach(([lbl, addr]) => {
    if (addr) html += `<div style="font-size:11px;color:#666;margin:2px 0">&#128205; <strong>${lbl}:</strong> ${addr}</div>`
  })
  const footer = []
  if (f.cin) footer.push(`CIN: ${f.cin}`)
  if (f.copyright_text) footer.push(f.copyright_text)
  if (footer.length) html += `<div style="font-size:10px;color:#999;margin:5px 0 0">${footer.join(' &nbsp;&bull;&nbsp; ')}</div>`
  return html
}

// Logo upload with base64
function LogoUpload({ value, onChange }) {
  const ref = useRef(null)
  const [busy, setBusy] = useState(false)
  const handleFile = f => {
    if (!f) return
    if (f.size > 3 * 1024 * 1024) { toast.error('Max 3MB'); return }
    setBusy(true)
    const r = new FileReader()
    r.onload = e => { onChange(e.target.result); setBusy(false) }
    r.onerror = () => { toast.error('Read failed'); setBusy(false) }
    r.readAsDataURL(f)
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <label style={{ cursor: 'pointer', flexShrink: 0 }}>
          <input ref={ref} type="file" accept="image/*" style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
          <span className="btn-secondary" style={{ fontSize: 12, padding: '6px 12px', display: 'inline-flex', alignItems: 'center', gap: 5, cursor: 'pointer' }}>
            <Upload size={13} /> {busy ? 'Reading…' : 'Upload Logo'}
          </span>
        </label>
        <input value={value?.startsWith('data:') ? '' : (value || '')}
          onChange={e => onChange(e.target.value)}
          placeholder="or paste image URL (https://...)"
          style={{ flex: 1, fontSize: 12 }} />
        {value && (
          <button onClick={() => onChange('')} className="btn-icon" title="Remove logo" style={{ width: 28, height: 28, flexShrink: 0, color: 'var(--error)' }}>
            <X size={12} />
          </button>
        )}
      </div>
      {value && (
        <div style={{ padding: 8, background: 'rgba(255,255,255,0.05)', borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)', display: 'inline-block' }}>
          <img src={value} alt="Logo" style={{ height: 44, display: 'block', borderRadius: 4 }} onError={e => e.target.style.display = 'none'} />
        </div>
      )}
    </div>
  )
}

// Social icon button — grey until hover
function SocialBtn({ cfg, value, onChange }) {
  const [hov, setHov] = useState(false)
  const bgColor = hov ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.08)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ width: 36, height: 36, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: bgColor, transition: 'all 0.2s', cursor: 'pointer' }}
        onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}>
        <img src={cfg.src} alt={cfg.label} style={{ width: 18, height: 18, filter: 'invert(1)', opacity: hov ? 1 : 0.6, transition: 'all 0.2s' }} />
      </div>
      <div style={{ flex: 1 }}>
        <label style={{ fontSize: 11, color: 'var(--subtext)', display: 'block', marginBottom: 3 }}>{cfg.label} URL</label>
        <input value={value || ''} onChange={e => onChange(cfg.key, e.target.value)} placeholder={cfg.ph} style={{ fontSize: 12 }} />
      </div>
    </div>
  )
}

// WhatsApp — phone number input
function WhatsAppInput({ value, onChange }) {
  const [hov, setHov] = useState(false)
  const waSvg = 'M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ width: 36, height: 36, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: hov ? '#25D36622' : 'rgba(255,255,255,0.08)', transition: 'all 0.2s' }}
        onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}>
        <svg viewBox="0 0 24 24" width="18" height="18" fill={hov ? '#25D366' : '#888888'} xmlns="http://www.w3.org/2000/svg" style={{ transition: 'fill 0.2s' }}>
          <path d={waSvg} />
        </svg>
      </div>
      <div style={{ flex: 1 }}>
        <label style={{ fontSize: 11, color: 'var(--subtext)', display: 'block', marginBottom: 3 }}>WhatsApp Number</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
          <span style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.18)', borderRight: 'none', borderRadius: '8px 0 0 8px', fontSize: 13, color: 'var(--subtext)', flexShrink: 0 }}>+</span>
          <input value={value || ''} onChange={e => onChange('whatsapp_number', e.target.value.replace(/\D/g, ''))}
            placeholder="919910501395" style={{ fontSize: 12, borderRadius: '0 8px 8px 0' }} />
        </div>
        <div style={{ fontSize: 10, color: 'var(--subtext)', marginTop: 3 }}>Enter digits only with country code (e.g. 919910501395)</div>
      </div>
    </div>
  )
}

function Section({ icon: Icon, label, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10, paddingBottom: 6, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        <Icon size={13} color="var(--accent-lit)" />
        <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.6, color: 'var(--accent-lit)' }}>{label}</span>
      </div>
      {children}
    </div>
  )
}
const F = ({ label, name, value, onChange, placeholder, mono }) => (
  <div className="form-row" style={{ marginBottom: 8 }}>
    <label style={{ fontSize: 11, color: 'var(--subtext)', marginBottom: 4 }}>{label}</label>
    <input value={value || ''} onChange={e => onChange(name, e.target.value)} placeholder={placeholder || ''} style={mono ? { fontFamily: 'var(--mono)', fontSize: 12 } : {}} />
  </div>
)
const TA = ({ label, name, value, onChange, placeholder }) => {
  const active = value !== null && value !== '' && value !== undefined
  return (
    <div className="form-row" style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <input type="checkbox" checked={active} onChange={e => onChange(name, e.target.checked ? placeholder : '')} style={{ width: 13, height: 13 }} />
        <label style={{ fontSize: 11, color: 'var(--subtext)' }}>Include {label} Address</label>
      </div>
      {active && <textarea value={value || ''} onChange={e => onChange(name, e.target.value)} placeholder={placeholder} rows={2} style={{ resize: 'vertical', fontSize: 12 }} />}
    </div>
  )
}

export default function SignaturePage({ adminUserId, adminUserEmail, onBack }) {
  const qc = useQueryClient()
  const [form, setForm] = useState(EMPTY)
  const [preview, setPreview] = useState(true)

  const { data: saved, isLoading } = useQuery({ queryKey: ['sig', adminUserId], queryFn: () => sigApi.get(adminUserId), retry: false })

  useEffect(() => {
    if (saved?.exists) {
      setForm({ ...EMPTY, ...saved, social_links: { ...EMPTY.social_links, ...(saved.social_links || {}) } })
    } else {
      setForm(EMPTY)
    }
  }, [saved, adminUserId])

  const set = (name, val) => setForm(f => ({ ...f, [name]: val }))
  const setSocial = (key, val) => setForm(f => ({ ...f, social_links: { ...f.social_links, [key]: val } }))

  const saveMut = useMutation({
    mutationFn: () => sigApi.save(adminUserId, form),
    onSuccess: () => { toast.success('Signature saved!'); qc.invalidateQueries(['sig', adminUserId]) },
    onError: e => {
      const s = e?.response?.status, msg = e?.response?.data?.detail || e?.message || 'Save failed'
      if (s === 404 || s === 500) toast.error('Run: python scripts/create_signatures_table.py — then restart backend')
      else toast.error(msg)
    },
  })
  const deleteMut = useMutation({
    mutationFn: () => sigApi.delete(adminUserId),
    onSuccess: () => { toast.success('Deleted'); setForm(EMPTY); qc.invalidateQueries(['sig', adminUserId]) },
  })

  if (isLoading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60 }}><span className="spinner" style={{ width: 28, height: 28 }} /></div>

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20 }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          {onBack && (
            <button className="btn-secondary" onClick={onBack} style={{ marginBottom: 12, fontSize: 12, padding: '4px 8px' }}>
              &larr; Back to Admin
            </button>
          )}
          <h1>{adminUserId ? `Editing Signature: ${adminUserEmail}` : 'Email Signature'}</h1>
          <p>{adminUserId ? 'Admin override for user signature' : 'Automatically appended to every email you send'}</p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', padding: '6px 12px', background: 'rgba(255,255,255,0.06)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', fontSize: 13 }}>
            <input type="checkbox" checked={form.is_default} onChange={e => set('is_default', e.target.checked)} style={{ width: 15, height: 15 }} /> Auto-append
          </label>
          <button className="btn-secondary" onClick={() => setPreview(p => !p)} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            {preview ? <><EyeOff size={13} /> Hide Preview</> : <><Eye size={13} /> Preview</>}
          </button>
          {saved?.exists && (
            <button className="btn-danger" onClick={() => { if (confirm('Delete signature?')) deleteMut.mutate() }} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, padding: '6px 12px' }}>
              <Trash2 size={13} /> Delete
            </button>
          )}
          <button className="btn-primary" onClick={() => saveMut.mutate()} disabled={saveMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '7px 18px' }}>
            <Save size={13} /> {saveMut.isPending ? 'Saving…' : 'Save Signature'}
          </button>
        </div>
      </div>

      <div style={{
        padding: '8px 14px', marginBottom: 20, borderRadius: 8, fontSize: 12,
        background: form.is_default ? 'rgba(63,185,80,0.08)' : 'rgba(210,153,34,0.08)',
        border: `1px solid ${form.is_default ? 'rgba(63,185,80,0.25)' : 'rgba(210,153,34,0.25)'}`,
        color: form.is_default ? 'var(--success)' : 'var(--warning)'
      }}>
        {form.is_default ? '✅ Active — appended to every outgoing email.' : '⚠ Disabled — emails sent without signature.'}
      </div>

      <div className="res-grid" style={{ display: 'grid', gridTemplateColumns: preview ? '460px 1fr' : '680px', gap: 24, alignItems: 'start' }}>
        <div>
          {/* Label + colour */}
          <div className="card" style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 11, color: 'var(--subtext)', display: 'block', marginBottom: 5 }}>Signature Label</label>
                <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="My Signature" />
              </div>
              <div>
                <label style={{ fontSize: 11, color: 'var(--subtext)', display: 'block', marginBottom: 5 }}>Brand Colour</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input type="color" value={form.brand_color || '#1C305E'} onChange={e => set('brand_color', e.target.value)} style={{ width: 44, height: 36, padding: 2, cursor: 'pointer', borderRadius: 6 }} />
                  <code style={{ fontSize: 12, color: 'var(--accent-lit)', fontFamily: 'var(--mono)' }}>{form.brand_color}</code>
                </div>
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 14 }}>
            <Section icon={User} label="Identity">
              <div className="res-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <F label="Full Name" name="full_name" value={form.full_name} onChange={set} placeholder="Enter Your Name" />
                <F label="Job Title" name="title" value={form.title} onChange={set} placeholder="Business Development Manager" />
              </div>
              <F label="Company" name="company" value={form.company} onChange={set} placeholder="CLAIM 360" />
              <div style={{ marginBottom: 8 }}>
                <label style={{ fontSize: 11, color: 'var(--subtext)', display: 'block', marginBottom: 5 }}>Company Logo</label>
                <LogoUpload value={form.logo_url} onChange={v => set('logo_url', v)} />
              </div>
            </Section>
            <Section icon={Phone} label="Contact">
              <div className="res-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <F label="Phone" name="phone" value={form.phone} onChange={set} placeholder="+91 9xxxxxxxx0" />
                <F label="Email" name="email_addr" value={form.email_addr} onChange={set} placeholder="youremail@claim360.in" />
              </div>
              <F label="Website" name="website" value={form.website} onChange={set} placeholder="www.claim360.in" />
            </Section>
          </div>

          <div className="card" style={{ marginBottom: 14 }}>
            <Section icon={MapPin} label="Office Addresses">
              <TA label="Mumbai" name="address_mumbai" value={form.address_mumbai} onChange={set} placeholder="311 Sun Industrial Estate..." />
              <TA label="Delhi" name="address_delhi" value={form.address_delhi} onChange={set} placeholder="D-4/4035, Vasant Kunj..." />
              <TA label="London" name="address_london" value={form.address_london} onChange={set} placeholder="2 Wymondham, St. Johns Wood Park..." />
            </Section>
          </div>

          <div className="card" style={{ marginBottom: 14 }}>
            <Section icon={Shield} label="Legal">
              <F label="CIN" name="cin" value={form.cin} onChange={set} placeholder="U74999DL2016PTC303092" mono />
              <F label="Copyright" name="copyright_text" value={form.copyright_text} onChange={set} placeholder="Copyright © 2026 360 Degrees Management..." />
            </Section>
          </div>

          <div className="card">
            <Section icon={Share2} label="Social Media">
              <p style={{ fontSize: 12, color: 'var(--subtext)', marginBottom: 14 }}>
                Icons are grey by default, hover to see brand colour. Leave blank to hide.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <WhatsAppInput value={form.social_links?.whatsapp_number} onChange={setSocial} />
                {SOCIAL_CFG.map(cfg => (
                  <SocialBtn key={cfg.key} cfg={cfg} value={form.social_links?.[cfg.key]} onChange={setSocial} />
                ))}
              </div>
            </Section>
          </div>
        </div>

        {/* Preview */}
        {preview && (
          <div style={{ position: 'sticky', top: 20 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.6, color: 'var(--subtext)', marginBottom: 10 }}>Live Preview</div>
            <div style={{ background: 'white', borderRadius: 10, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.15)', boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}>
              <div style={{ padding: '10px 16px', background: '#f6f8fa', borderBottom: '1px solid #e0e0e0', fontSize: 12, color: '#555' }}>
                <div style={{ marginBottom: 2 }}><strong>From:</strong> {form.email_addr || 'you@gmail.com'}</div>
                <div style={{ marginBottom: 2 }}><strong>To:</strong> recipient@example.com</div>
                <div><strong>Subject:</strong> Following up on our discussion</div>
              </div>
              <div style={{ padding: '16px 20px', fontFamily: 'Arial,sans-serif', fontSize: 14, color: '#222', lineHeight: 1.6 }}>
                <p style={{ margin: '0 0 10px' }}>Dear [Name],</p>
                <p style={{ margin: '0 0 10px' }}>Thank you for your time. Please find the details below.</p>
                <p style={{ margin: '0 0 16px' }}>Best regards,</p>
                {(form.full_name || form.phone || form.email_addr) ? (
                  <div dangerouslySetInnerHTML={{ __html: buildPreviewHtml(form) }} />
                ) : (
                  <div style={{ padding: 20, textAlign: 'center', color: '#aaa', fontSize: 13, border: '2px dashed #e0e0e0', borderRadius: 6 }}>
                    Fill in your name or contact details to see preview
                  </div>
                )}
              </div>
            </div>
            <p style={{ fontSize: 11, color: 'var(--subtext)', marginTop: 8, textAlign: 'center' }}>Exactly how recipients will see your signature</p>
          </div>
        )}
      </div>
    </div>
  )
}
