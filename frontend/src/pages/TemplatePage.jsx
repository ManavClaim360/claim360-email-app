import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesApi } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { useData } from '../context/DataContext'
import { Plus, Trash2, Save, Upload, FileText, Globe, Lock, Eye, EyeOff, Send,
  Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight,
  List, Link, Smile, Minus, Code, Palette, Table, ChevronDown, X
} from 'lucide-react'
import toast from 'react-hot-toast'

// ── Constants ─────────────────────────────────────────────────────
const FONTS  = ['Arial','Georgia','Verdana','Tahoma','Courier New','Times New Roman','Trebuchet MS']
const SIZES  = [2,4,6,8,10,11,12,13,14,15,16,17,18,20,22,24,26,28,30,32,34,36]
const EMOJIS = ['😊','👍','🎉','✅','⚠️','🔥','💡','📌','🎯','🚀','💼','📊','🤝','⭐','✨','🙏','📝','🔑','💰','📞','📧','🌏','🔗','❤️']


// ── Email preview document builder ──────────────────────────────
function getPreviewDoc(bodyHtml) {
  const body = bodyHtml || '<p style="color:#8b949e">No content yet.</p>'
  return [
    '<!DOCTYPE html><html><head><meta charset="utf-8"><style>',
    'body{font-family:Arial,sans-serif;padding:24px;color:#1f2328;line-height:1.7;margin:0;background:#fff}',
    'table{border-collapse:collapse!important;width:100%;margin:8px 0}',
    'td,th{border:1px solid #aaa!important;padding:7px 12px!important;background:#fff!important;color:#222!important;font-size:13px}',
    'th{background:#eee!important;font-weight:600!important;color:#111!important}',
    'a{color:#0969da} hr{border:none;border-top:1px solid #d0d7de;margin:14px 0}',
    'h1,h2,h3{color:#1f2328} p{margin:0 0 8px 0}',
    '</style></head><body>',
    body,
    '</body></html>',
  ].join('')
}

// ── Floating dropdown helper (uses fixed position to escape stacking contexts) ──
function useAnchorRect(ref) {
  const [rect, setRect] = React.useState(null)
  React.useEffect(() => {
    if (ref.current) setRect(ref.current.getBoundingClientRect())
  }, [ref])
  return rect
}

function TableDropdown({ anchorEl, tableRows, setTableRows, tableCols, setTableCols, tableWidth, setTableWidth, tableHeader, setTableHeader, onInsert, onClose }) {
  const rect = anchorEl?.getBoundingClientRect()
  const top  = rect ? rect.bottom + window.scrollY + 4 : 100
  const left = rect ? rect.left  + window.scrollX     : 100
  return (
    <div
      style={{
        position: 'fixed',
        top: rect ? rect.bottom + 4 : 100,
        left: rect ? rect.left : 100,
        zIndex: 99999,
        background: '#0d1a3a',
        border: '1px solid rgba(168,200,240,0.3)',
        borderRadius: 10,
        padding: 16,
        width: 220,
        boxShadow: '0 12px 40px rgba(0,0,0,0.8)',
        color: '#f0f6fc',
      }}
      onMouseDown={e => e.stopPropagation()}
    >
      <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 12, color: '#f0f6fc' }}>Insert Table</div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 10 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, color: '#b0c4de', marginBottom: 4 }}>Rows</div>
          <input type="number" value={tableRows} min={1} max={20}
            onChange={e => setTableRows(+e.target.value)}
            style={{ padding: '4px 6px', fontSize: 12 }} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, color: '#b0c4de', marginBottom: 4 }}>Columns</div>
          <input type="number" value={tableCols} min={1} max={10}
            onChange={e => setTableCols(+e.target.value)}
            style={{ padding: '4px 6px', fontSize: 12 }} />
        </div>
      </div>

      <div style={{ marginBottom: 10 }}>
        <div style={{ fontSize: 11, color: '#b0c4de', marginBottom: 4 }}>Width: {tableWidth}%</div>
        <input type="range" min={20} max={100} step={5} value={tableWidth}
          onChange={e => setTableWidth(+e.target.value)}
          style={{ width: '100%', padding: 0, height: 4, border: 'none', cursor: 'pointer', accentColor: '#a8c8f0' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#8b949e', marginTop: 2 }}>
          <span>20%</span><span>60%</span><span>100%</span>
        </div>
      </div>

      <label style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12, marginBottom: 14, cursor: 'pointer', color: '#f0f6fc' }}>
        <input type="checkbox" checked={tableHeader} onChange={e => setTableHeader(e.target.checked)} style={{ width: 14, height: 14 }} />
        Include header row
      </label>

      <button type="button" className="btn-primary" onClick={onInsert}
        style={{ width: '100%', fontSize: 12, padding: '7px 0', marginBottom: 6 }}>
        Insert {tableRows}×{tableCols} Table
      </button>
      <button type="button" className="btn-secondary" onClick={onClose}
        style={{ width: '100%', fontSize: 12, padding: '6px 0' }}>Cancel</button>
    </div>
  )
}

// ── Rich Text Editor ──────────────────────────────────────────────
function RTE({ initialValue, onChange, variables }) {
  const editorRef   = useRef(null)
  const savedRange  = useRef(null)
  const tableBtnRef = useRef(null)
  const [showHtml,   setShowHtml]   = useState(false)
  const [showEmoji,  setShowEmoji]  = useState(false)
  const [showTable,  setShowTable]  = useState(false)
  const [htmlVal,    setHtmlVal]    = useState(initialValue || '')
  const [tableRows,  setTableRows]  = useState(3)
  const [tableCols,  setTableCols]  = useState(3)
  const [tableHeader,setTableHeader]= useState(true)
  const [tableWidth, setTableWidth] = useState(100)

  // Set initial content
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.innerHTML = initialValue || ''
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Save caret position before any toolbar button blurs the editor
  const saveRange = useCallback(() => {
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0 && editorRef.current?.contains(sel.anchorNode)) {
      savedRange.current = sel.getRangeAt(0).cloneRange()
    }
  }, [])

  // Restore caret before inserting
  const restoreRange = useCallback(() => {
    if (!savedRange.current) return
    editorRef.current?.focus()
    const sel = window.getSelection()
    sel.removeAllRanges()
    sel.addRange(savedRange.current)
  }, [])

  const emit = useCallback(() => {
    const html = editorRef.current?.innerHTML || ''
    onChange(html)
    setHtmlVal(html)
  }, [onChange])

  const exec = useCallback((cmd, val = null) => {
    editorRef.current?.focus()
    document.execCommand(cmd, false, val)
    emit()
  }, [emit])

  // ── Font size using span injection (reliable 2–36px) ──────────
  const applyFontSize = useCallback((px) => {
    editorRef.current?.focus()
    restoreRange()
    const sel = window.getSelection()
    if (!sel || sel.rangeCount === 0) return
    if (sel.isCollapsed) {
      // No selection — just set a marker for next typed chars
      document.execCommand('fontSize', false, '7')
      editorRef.current.querySelectorAll('font[size="7"]').forEach(el => {
        el.removeAttribute('size')
        el.style.fontSize = px + 'px'
      })
    } else {
      // Wrap selection in a span
      const range = sel.getRangeAt(0)
      const span  = document.createElement('span')
      span.style.fontSize = px + 'px'
      try { range.surroundContents(span) } catch {
        document.execCommand('fontSize', false, '7')
        editorRef.current.querySelectorAll('font[size="7"]').forEach(el => {
          el.removeAttribute('size'); el.style.fontSize = px + 'px'
        })
      }
    }
    emit()
  }, [restoreRange, emit])

  // ── Insert variable as plain text {{var}} ────────────────────
  // We use plain text so the email recipient sees the substituted value,
  // not a styled box. The editor just shows it inline normally.
  const insertVariable = useCallback((v) => {
    restoreRange()
    editorRef.current?.focus()
    // Insert as plain {{var}} text — completely plain, no wrapping span
    // This ensures email recipients see only the substituted value
    document.execCommand('insertText', false, `{{${v}}}`)
    emit()
    setShowEmoji(false)
  }, [restoreRange, emit])

  // ── Insert hyperlink ──────────────────────────────────────────
  const insertLink = useCallback(() => {
    saveRange()
    const url = prompt('Enter URL:', 'https://')
    if (!url) return
    restoreRange()
    const text = window.getSelection()?.toString() || url
    document.execCommand('insertHTML', false,
      `<a href="${url}" style="color:#88b4e0" target="_blank">${text}</a>`)
    emit()
  }, [saveRange, restoreRange, emit])

  // ── Insert table ──────────────────────────────────────────────
  const insertTable = useCallback(() => {
    restoreRange()
    // Use email-safe inline styles — work in both dark editor and light email clients
    const borderColor = '#cccccc'
    const headerBg = '#f5f5f5'
    const headerColor = '#222222'
    const cellColor = '#222222'
    // All table colors are email-safe (dark text on light/transparent bg)
    let html = `<table style="border-collapse:collapse;width:${tableWidth}%;margin:10px 0;table-layout:fixed;font-family:Arial,sans-serif">`
    if (tableHeader) {
      html += '<thead><tr>'
      for (let c = 0; c < tableCols; c++) {
        const w = Math.floor(100 / tableCols)
        html += `<th style="border:1px solid ${borderColor};padding:8px 12px;background:${headerBg};color:${headerColor};font-weight:600;text-align:left;width:${w}%;min-width:60px;font-size:13px;font-family:Arial,sans-serif">Header ${c+1}</th>`
      }
      html += '</tr></thead>'
    }
    html += '<tbody>'
    const dataRows = tableRows - (tableHeader ? 1 : 0)
    for (let r = 0; r < dataRows; r++) {
      html += '<tr>'
      for (let c = 0; c < tableCols; c++)
        html += `<td style="border:1px solid ${borderColor};padding:8px 12px;background:#ffffff;color:${cellColor};min-width:80px;font-size:13px;font-family:Arial,sans-serif"> </td>`
      html += '</tr>'
    }
    html += '</tbody></table><p><br></p>'
    document.execCommand('insertHTML', false, html)
    setShowTable(false); emit()
  }, [restoreRange, tableRows, tableCols, tableHeader, emit])

  // ── Drag & Drop variable from pill bar into editor ────────────
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const v = e.dataTransfer.getData('application/x-var-name')
    if (!v) return
    editorRef.current?.focus()
    // Position caret at drop point
    if (document.caretRangeFromPoint) {
      const range = document.caretRangeFromPoint(e.clientX, e.clientY)
      if (range) {
        const sel = window.getSelection()
        sel.removeAllRanges()
        sel.addRange(range)
        savedRange.current = range.cloneRange()
      }
    }
    insertVariable(v)
  }, [insertVariable])

  const handleDragOver = (e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy' }

  // ── HTML edit apply ───────────────────────────────────────────
  const applyHtml = () => {
    if (editorRef.current) editorRef.current.innerHTML = htmlVal
    onChange(htmlVal); setShowHtml(false)
  }

  // ── Toolbar button component ──────────────────────────────────
  const Btn = ({ cmd, val, icon: Icon, label, title: t, wide }) => (
    <button type="button" className="rte-btn" title={t || label}
      style={wide ? { width: 'auto', padding: '0 6px' } : {}}
      onMouseDown={e => { e.preventDefault(); saveRange(); exec(cmd, val) }}>
      {Icon ? <Icon size={12} /> : label}
    </button>
  )

  return (
    <div className="rte-wrap">
      <style>{`
        .rte-body table { border-collapse: collapse !important; min-width: 100%; margin: 8px 0; }
        .rte-body th, .rte-body td { border: 1px dotted #ccc !important; padding: 6px !important; }
      `}</style>
      {/* ── Variable pill bar ── */}
      {variables.length > 0 && (
        <div className="rte-var-bar">
          <span style={{ fontSize: 10, color: 'var(--subtext)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginRight: 6, flexShrink: 0 }}>
            Variables (drag or click):
          </span>
          {variables.map(v => (
            <span key={v}
              className="rte-var-pill"
              draggable
              onDragStart={e => {
                e.dataTransfer.setData('application/x-var-name', v)
                e.dataTransfer.effectAllowed = 'copy'
              }}
              onMouseDown={e => { e.preventDefault(); saveRange() }}
              onClick={() => insertVariable(v)}
              title={`Click or drag to insert {{${v}}}`}>
              {`{{${v}}}`}
            </span>
          ))}
          <span style={{ fontSize: 10, color: 'var(--subtext)', marginLeft: 4 }}>
            ← from your Excel upload
          </span>
        </div>
      )}

      {/* ── Toolbar ── */}
      <div className="rte-toolbar">
        {/* Font family */}
        <select className="rte-select" style={{ width: 90 }} title="Font family"
          defaultValue=""
          onChange={e => { saveRange(); exec('fontName', e.target.value) }}>
          <option value="" disabled>Font</option>
          {FONTS.map(f => <option key={f} value={f}>{f}</option>)}
        </select>

        {/* Font size */}
        <select className="rte-select" style={{ width: 62 }} title="Font size (px)"
          defaultValue=""
          onChange={e => { saveRange(); applyFontSize(+e.target.value) }}>
          <option value="" disabled>Size</option>
          {SIZES.map(s => <option key={s} value={s}>{s}px</option>)}
        </select>

        <div className="rte-toolbar-sep" />

        <Btn cmd="bold"         icon={Bold}      title="Bold (Ctrl+B)" />
        <Btn cmd="italic"       icon={Italic}    title="Italic (Ctrl+I)" />
        <Btn cmd="underline"    icon={Underline} title="Underline (Ctrl+U)" />
        <Btn cmd="strikeThrough" label="S̶"       title="Strikethrough" />

        <div className="rte-toolbar-sep" />

        {/* Text colour */}
        <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
          <button type="button" className="rte-btn" title="Text colour"
            style={{ width: 36, gap: 2 }} onMouseDown={e => e.preventDefault()}>
            <Palette size={12} />
            <input type="color" defaultValue="#e6edf3"
              onMouseDown={e => { e.stopPropagation(); saveRange() }}
              onChange={e => { restoreRange(); exec('foreColor', e.target.value) }}
              style={{ width: 13, height: 13, border: 'none', padding: 0, cursor: 'pointer', background: 'none', borderRadius: 2 }} />
          </button>
        </div>
        {/* Highlight colour */}
        <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
          <button type="button" className="rte-btn" title="Highlight colour"
            style={{ width: 38, gap: 2, fontSize: 10 }} onMouseDown={e => e.preventDefault()}>
            BG
            <input type="color" defaultValue="#ffff00"
              onMouseDown={e => { e.stopPropagation(); saveRange() }}
              onChange={e => { restoreRange(); exec('backColor', e.target.value) }}
              style={{ width: 13, height: 13, border: 'none', padding: 0, cursor: 'pointer', background: 'none', borderRadius: 2 }} />
          </button>
        </div>

        <div className="rte-toolbar-sep" />

        <Btn cmd="justifyLeft"   icon={AlignLeft}   title="Align left" />
        <Btn cmd="justifyCenter" icon={AlignCenter} title="Align center" />
        <Btn cmd="justifyRight"  icon={AlignRight}  title="Align right" />
        <Btn cmd="justifyFull"   label="≡"          title="Justify" />

        <div className="rte-toolbar-sep" />

        <Btn cmd="insertUnorderedList" icon={List} title="Bullet list" />
        <Btn cmd="insertOrderedList"   label="1."  title="Numbered list" />
        <Btn cmd="indent"              label="⇥"   title="Indent" />
        <Btn cmd="outdent"             label="⇤"   title="Outdent" />

        <div className="rte-toolbar-sep" />

        {['H1','H2','H3','P'].map(tag => (
          <button key={tag} type="button" className="rte-btn" title={tag === 'P' ? 'Paragraph' : `Heading ${tag[1]}`}
            style={{ width: tag === 'P' ? 24 : 28 }}
            onMouseDown={e => { e.preventDefault(); saveRange(); exec('formatBlock', tag === 'P' ? 'p' : tag.toLowerCase()) }}>
            {tag}
          </button>
        ))}

        <div className="rte-toolbar-sep" />

        {/* Link */}
        <button type="button" className="rte-btn" title="Insert hyperlink"
          onMouseDown={e => { e.preventDefault(); insertLink() }}>
          <Link size={12} />
        </button>

        {/* Horizontal rule */}
        <button type="button" className="rte-btn" title="Horizontal divider line"
          onMouseDown={e => { e.preventDefault(); restoreRange(); exec('insertHorizontalRule') }}>
          <Minus size={12} />
        </button>

        {/* Table builder — fixed position to escape stacking context */}
        <div style={{ position: 'relative' }}>
          <button
            ref={tableBtnRef}
            type="button"
            className={`rte-btn${showTable ? ' active' : ''}`}
            title="Insert table"
            onMouseDown={e => { e.preventDefault(); saveRange(); setShowTable(s => !s); setShowEmoji(false) }}>
            <Table size={12} />
          </button>
          {showTable && tableBtnRef.current && (() => {
            const r = tableBtnRef.current.getBoundingClientRect()
            return (
              <div
                onMouseDown={e => e.stopPropagation()}
                style={{
                  position: 'fixed',
                  top: r.bottom + 4,
                  left: r.left,
                  zIndex: 999999,
                  background: '#0d1a3a',
                  border: '1px solid rgba(168,200,240,0.3)',
                  borderRadius: 10,
                  padding: 16,
                  width: 220,
                  boxShadow: '0 12px 40px rgba(0,0,0,0.8)',
                  color: '#f0f6fc',
                }}>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 12 }}>Insert Table</div>
                <div style={{ display: 'flex', gap: 10, marginBottom: 10 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, color: '#b0c4de', marginBottom: 4 }}>Rows</div>
                    <input type="number" value={tableRows} min={1} max={20}
                      onChange={e => setTableRows(+e.target.value)}
                      style={{ padding: '4px 6px', fontSize: 12 }} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, color: '#b0c4de', marginBottom: 4 }}>Columns</div>
                    <input type="number" value={tableCols} min={1} max={10}
                      onChange={e => setTableCols(+e.target.value)}
                      style={{ padding: '4px 6px', fontSize: 12 }} />
                  </div>
                </div>
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 11, color: '#b0c4de', marginBottom: 4 }}>Width: {tableWidth}%</div>
                  <input type="range" min={20} max={100} step={5} value={tableWidth}
                    onChange={e => setTableWidth(+e.target.value)}
                    style={{ width: '100%', padding: 0, border: 'none', cursor: 'pointer', accentColor: '#a8c8f0' }} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#8b949e', marginTop: 2 }}>
                    <span>20%</span><span>60%</span><span>100%</span>
                  </div>
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12, marginBottom: 12, cursor: 'pointer', color: '#f0f6fc' }}>
                  <input type="checkbox" checked={tableHeader} onChange={e => setTableHeader(e.target.checked)} style={{ width: 14, height: 14 }} />
                  Include header row
                </label>
                <button type="button" className="btn-primary" onClick={insertTable}
                  style={{ width: '100%', fontSize: 12, padding: '7px 0', marginBottom: 6 }}>
                  Insert {tableRows}×{tableCols} Table
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowTable(false)}
                  style={{ width: '100%', fontSize: 12, padding: '6px 0' }}>Cancel</button>
              </div>
            )
          })()}
        </div>

        {/* Emoji */}
        <div style={{ position: 'relative' }}>
          <button type="button" className={`rte-btn${showEmoji ? ' active' : ''}`} title="Insert emoji"
            onMouseDown={e => { e.preventDefault(); saveRange(); setShowEmoji(s => !s); setShowTable(false) }}>
            <Smile size={12} />
          </button>
          {showEmoji && (
            <div style={{
              position: 'absolute', top: 'calc(100% + 4px)', left: 0, zIndex: 99999,
              background: '#0d1a3a',
              border: '1px solid rgba(168,200,240,0.3)', borderRadius: 8,
              padding: 8, display: 'flex', flexWrap: 'wrap', gap: 2, width: 240,
              boxShadow: '0 8px 32px rgba(0,0,0,0.7)',
            }}>
              {EMOJIS.map(em => (
                <button key={em} type="button"
                  onMouseDown={e => {
                    e.preventDefault()
                    restoreRange()
                    document.execCommand('insertText', false, em)
                    setShowEmoji(false); emit()
                  }}
                  style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', padding: '3px', borderRadius: 4, lineHeight: 1 }}>
                  {em}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* HTML source */}
        <div className="rte-toolbar-sep" />
        <button type="button" className={`rte-btn${showHtml ? ' active' : ''}`} title="Edit raw HTML source"
          onMouseDown={e => {
            e.preventDefault()
            setShowHtml(s => {
              if (!s) setHtmlVal(editorRef.current?.innerHTML || '')
              return !s
            })
            setShowEmoji(false); setShowTable(false)
          }}>
          <Code size={12} />
        </button>
      </div>

      {/* ── Editor body ── */}
      {showHtml ? (
        <div style={{ background: 'var(--surface)', padding: 10 }}>
          <textarea value={htmlVal} onChange={e => setHtmlVal(e.target.value)}
            style={{ minHeight: 240, fontFamily: 'var(--mono)', fontSize: 12, borderRadius: 6, resize: 'vertical' }} />
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button type="button" className="btn-primary" onClick={applyHtml} style={{ fontSize: 12, padding: '6px 14px' }}>Apply HTML</button>
            <button type="button" className="btn-secondary" onClick={() => setShowHtml(false)} style={{ fontSize: 12, padding: '6px 14px' }}>Cancel</button>
          </div>
        </div>
      ) : (
        <div
          ref={editorRef}
          className="rte-body"
          contentEditable
          suppressContentEditableWarning
          data-placeholder="Write your email here. Drag variable pills into the text, or use the toolbar above..."
          onInput={emit}
          onMouseUp={saveRange}
          onKeyUp={saveRange}
          onFocus={saveRange}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        />
      )}
    </div>
  )
}

// ── Subject input with variable dropdown ─────────────────────────
function SubjectInput({ value, onChange, variables }) {
  const [open, setOpen] = useState(false)
  const inputRef = useRef(null)

  const insertVar = (v) => {
    const el = inputRef.current
    if (!el) { onChange(value + `{{${v}}}`); setOpen(false); return }
    const s = el.selectionStart, e = el.selectionEnd
    const next = value.slice(0, s) + `{{${v}}}` + value.slice(e)
    onChange(next)
    setOpen(false)
    setTimeout(() => { el.focus(); const p = s + v.length + 4; el.setSelectionRange(p, p) }, 0)
  }

  return (
    <div style={{ position: 'relative', display: 'flex' }}>
      <input ref={inputRef} value={value} onChange={e => onChange(e.target.value)}
        placeholder="Hi {{name}}, message for {{company}}..."
        style={{ borderRadius: '8px 0 0 8px', borderRight: 'none', flex: 1 }} />
      <button type="button" onClick={() => setOpen(s => !s)} title="Insert variable at cursor"
        style={{
          flexShrink: 0, padding: '0 10px', background: 'var(--surface)',
          border: '1px solid var(--border)', borderRadius: '0 8px 8px 0',
          cursor: 'pointer', color: 'var(--accent-lit)', display: 'flex',
          alignItems: 'center', gap: 4, fontSize: 12, fontFamily: 'var(--mono)',
        }}>
        {'{{x}}'}<ChevronDown size={11} />
      </button>
      {open && variables.length > 0 && (
        <div className="subject-var-dropdown">
          <div style={{ fontSize: 10, color: 'var(--subtext)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.4, padding: '2px 10px 6px' }}>
            Insert variable
          </div>
          {variables.map(v => (
            <button key={v} className="subject-var-item" onClick={() => insertVar(v)}>
              {`{{${v}}}`}
            </button>
          ))}
        </div>
      )}
      {/* close on outside click */}
      {open && <div style={{ position: 'fixed', inset: 0, zIndex: 99 }} onClick={() => setOpen(false)} />}
    </div>
  )
}

// ── Main TemplatePage ─────────────────────────────────────────────
export default function TemplatePage() {
  const qc = useQueryClient()
  const { user }    = useAuth()
  const { varNames: excelVarNames } = useData()

  const [selected,       setSelected]       = useState(null)
  const [form,           setForm]           = useState({ name: '', subject: '', body_html: '', is_shared: false })
  const [selectedAttIds, setSelectedAttIds] = useState([])
  const [previewMode,    setPreviewMode]    = useState(false)
  const [rteKey,         setRteKey]         = useState(0)

  const { data: templates   = [] } = useQuery({ queryKey: ['templates'],   queryFn: templatesApi.list })
  const { data: attachments = [] } = useQuery({ queryKey: ['attachments'], queryFn: templatesApi.listAttachments })

  // Variable list: prefer Excel vars; fall back to detecting from body/subject
  const detectedVars = [...new Set(
    (form.body_html + ' ' + form.subject).match(/\{\{(\w+)\}\}/g)?.map(m => m.slice(2, -2)) || []
  )]
  const editorVars = excelVarNames.length > 0 ? excelVarNames
    : detectedVars.length > 0 ? detectedVars
    : ['name', 'company', 'position']

  const saveMut = useMutation({
    mutationFn: d => selected ? templatesApi.update(selected.id, d) : templatesApi.create(d),
    onSuccess: () => { toast.success(selected ? 'Template updated!' : 'Template created!'); qc.invalidateQueries(['templates']) },
    onError: e => toast.error(e?.response?.data?.detail || 'Save failed'),
  })
  const deleteMut = useMutation({
    mutationFn: templatesApi.delete,
    onSuccess: () => { toast.success('Deleted'); qc.invalidateQueries(['templates']); handleNew() },
  })
  const uploadAttMut = useMutation({
    mutationFn: ({ file, shared }) => templatesApi.uploadAttachment(file, shared),
    onSuccess: att => {
      toast.success(`${att.original_filename} uploaded`)
      qc.invalidateQueries(['attachments'])
      setSelectedAttIds(p => [...p, att.id])
    },
  })
  const deleteAttMut = useMutation({
    mutationFn: templatesApi.deleteAttachment,
    onSuccess: () => { toast.success('Attachment deleted'); qc.invalidateQueries(['attachments']) },
  })

  const testSendMut = useMutation({
    mutationFn: (id) => templatesApi.testSend(id),
    onSuccess: () => toast.success('Test email sent! Check your inbox (or console in dev).'),
    onError: (e) => toast.error(e?.response?.data?.detail || 'Test send failed'),
  })

  const selectTemplate = t => {
    setSelected(t)
    setForm({ name: t.name, subject: t.subject, body_html: t.body_html || '', is_shared: t.is_shared })
    setSelectedAttIds(t.attachments?.map(a => a.id) || [])
    setPreviewMode(false)
    setRteKey(k => k + 1)
  }

  const handleNew = () => {
    setSelected(null)
    setForm({ name: '', subject: '', body_html: '', is_shared: false })
    setSelectedAttIds([])
    setPreviewMode(false)
    setRteKey(k => k + 1)
  }

  // Strip any styled var spans → plain {{var}} text before saving
  const sanitizeHtml = (html) => {
    if (!html) return ''
    // Replace <span data-var="xxx">{{xxx}}</span> with plain {{xxx}}
    return html.replace(/<span[^>]*data-var="([^"]+)"[^>]*>.*?<\/span>/g, '{{$1}}')
  }

  const handleSave = () => {
    if (!form.name.trim())    { toast.error('Template name is required');  return }
    if (!form.subject.trim()) { toast.error('Subject line is required');   return }
    const cleanHtml = sanitizeHtml(form.body_html)
    saveMut.mutate({
      name: form.name, subject: form.subject,
      body_html: cleanHtml,
      body_text: cleanHtml.replace(/<[^>]+>/g, ''),
      is_shared: form.is_shared,
      attachment_ids: selectedAttIds,
    })
  }

  const fmtSize = b => b > 1048576 ? `${(b/1048576).toFixed(1)}MB` : `${Math.round(b/1024)}KB`
  const visibleTemplates = templates.filter(t => {
    if (!user) return t.is_shared
    return user.is_admin || t.creator_id === user.id || t.is_shared
  })

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Templates</h1>
        <p>Create rich email templates with drag-and-drop variables, tables, and formatting</p>
      </div>

      <div className="res-grid" style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: 20, alignItems: 'start' }}>

        {/* Template list */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Templates ({visibleTemplates.length})</span>
            <button className="btn-icon" onClick={handleNew} title="New template"><Plus size={14} /></button>
          </div>
          <div style={{ padding: '6px 10px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 12, fontSize: 11, color: 'var(--subtext)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><Globe size={10} color="var(--accent-lit)" /> Shared</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><Lock size={10} /> Private</span>
          </div>
          <div style={{ maxHeight: 560, overflowY: 'auto' }}>
            {visibleTemplates.map(t => (
              <div key={t.id} onClick={() => selectTemplate(t)} title={`Edit: ${t.name}`} style={{
                padding: '10px 14px', cursor: 'pointer', borderBottom: '1px solid var(--border)',
                background: selected?.id === t.id ? 'rgba(28,48,94,0.12)' : 'transparent',
                borderLeft: `3px solid ${selected?.id === t.id ? 'var(--accent-lit)' : 'transparent'}`,
                transition: 'all 0.1s',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 2 }}>
                  {t.is_shared ? <Globe size={11} color="var(--accent-lit)" /> : <Lock size={11} color="var(--subtext)" />}
                  <span style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.name}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--subtext)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.subject}</div>
                {t.attachments?.length > 0 && (
                  <div style={{ fontSize: 10, color: 'var(--subtext)', marginTop: 2 }}>📎 {t.attachments.length} file{t.attachments.length > 1 ? 's' : ''}</div>
                )}
              </div>
            ))}
            {!visibleTemplates.length && (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--subtext)', fontSize: 12 }}>
                No templates yet.<br />Click + to create one.
              </div>
            )}
          </div>
        </div>

        {/* Editor */}
        <div className="card">
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600 }}>
              {selected ? `Editing: ${selected.name}` : 'New Template'}
            </h3>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-secondary" onClick={() => setPreviewMode(p => !p)}
                style={{ fontSize: 12, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 5 }}
                title={previewMode ? 'Back to editor' : 'Preview email in browser'}>
                {previewMode ? <><EyeOff size={13} /> Editor</> : <><Eye size={13} /> Preview</>}
              </button>
              {selected && (
                <button className="btn-secondary" onClick={() => testSendMut.mutate(selected.id)}
                  disabled={testSendMut.isPending}
                  title="Send a sample of this email to yourself"
                  style={{ fontSize: 12, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 5, color: 'var(--accent-lit)', borderColor: 'var(--accent-lit)' }}>
                  {testSendMut.isPending ? <span className="spinner" style={{ width: 13, height: 13 }} /> : <Send size={13} />}
                  Test Email
                </button>
              )}
              {selected && (
                <button className="btn-danger" onClick={() => { if (confirm('Delete this template?')) deleteMut.mutate(selected.id) }}
                  title="Delete permanently" style={{ fontSize: 12, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Trash2 size={13} /> Delete
                </button>
              )}
              <button className="btn-primary" onClick={handleSave} disabled={saveMut.isPending}
                title="Save to database" style={{ fontSize: 12, padding: '6px 16px', display: 'flex', alignItems: 'center', gap: 6 }}>
                <Save size={13} /> {saveMut.isPending ? 'Saving...' : 'Save Template'}
              </button>
            </div>
          </div>

          {previewMode ? (
            /* Preview */
            <div>
              <div style={{ padding: '10px 14px', background: 'var(--surface)', borderRadius: 8, border: '1px solid var(--border)', marginBottom: 12, fontSize: 13 }}>
                <span style={{ color: 'var(--subtext)', marginRight: 8, fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.4 }}>Subject</span>
                <strong style={{ color: 'var(--text)' }}>{form.subject || '(empty)'}</strong>
              </div>
              <div style={{ background: 'white', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}>
                <iframe
                  srcDoc={getPreviewDoc(form.body_html)}
                  style={{ width: '100%', minHeight: 400, border: 'none', display: 'block' }}
                  title="Preview" sandbox="allow-same-origin"
                  onLoad={e => {
                    try {
                      const h = e.target.contentDocument?.body?.scrollHeight
                      if (h && h > 400) e.target.style.height = h + 32 + 'px'
                    } catch {}
                  }} />
              </div>
            </div>
          ) : (
            /* Edit */
            <>
              <div className="res-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
                <div className="form-row" style={{ marginBottom: 0 }}>
                  <label>Template Name *</label>
                  <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="My Email Template" />
                </div>
                <div className="form-row" style={{ marginBottom: 0 }}>
                  <label>Subject Line * <span style={{ fontSize: 10, color: 'var(--subtext)', fontWeight: 400 }}>— click {'{{x}}'} to insert variable</span></label>
                  <SubjectInput value={form.subject} onChange={v => setForm(f => ({ ...f, subject: v }))} variables={editorVars} />
                </div>
              </div>

              {/* Share toggle */}
              {user?.is_admin ? (
                <div style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'rgba(28,48,94,0.08)', borderRadius: 6, border: '1px solid rgba(136,180,224,0.2)' }}>
                  <input type="checkbox" id="shared" checked={form.is_shared}
                    onChange={e => setForm(f => ({ ...f, is_shared: e.target.checked }))} style={{ width: 15, height: 15 }} />
                  <label htmlFor="shared" style={{ fontSize: 13, cursor: 'pointer', color: 'var(--text)' }}>
                    <Globe size={13} style={{ marginRight: 5, verticalAlign: 'middle', color: 'var(--accent-lit)' }} />
                    Share with all team members
                  </label>
                </div>
              ) : (
                <div style={{ marginBottom: 14, fontSize: 12, color: 'var(--subtext)', padding: '7px 12px', background: 'var(--surface)', borderRadius: 6, border: '1px solid var(--border)' }}>
                  <Lock size={11} style={{ marginRight: 5, verticalAlign: 'middle' }} />
                  Private — only admins can share templates with the team.
                </div>
              )}

              {/* RTE — key forces fresh mount on template switch */}
              <div style={{ marginBottom: 16 }}>
                <label className="label">Email Body</label>
                <RTE
                  key={rteKey}
                  initialValue={form.body_html}
                  onChange={v => setForm(f => ({ ...f, body_html: v }))}
                  variables={editorVars}
                />
              </div>

              {/* Attachments */}
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <label className="label" style={{ marginBottom: 0 }}>Attachments</label>
                  <label title="Upload a file to attach" style={{ cursor: 'pointer' }}>
                    <input type="file" style={{ display: 'none' }}
                      onChange={e => { const f = e.target.files[0]; if (f) uploadAttMut.mutate({ file: f, shared: user?.is_admin && form.is_shared }); e.target.value = '' }} />
                    <span className="btn-secondary" style={{ fontSize: 11, padding: '4px 10px', display: 'inline-flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                      <Upload size={12} /> Upload File
                    </span>
                  </label>
                </div>

                {!attachments.length && (
                  <p style={{ fontSize: 12, color: 'var(--subtext)' }}>No files uploaded yet.</p>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {attachments.map(att => {
                    const isSel = selectedAttIds.includes(att.id)
                    return (
                      <div key={att.id} style={{
                        display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px',
                        borderRadius: 6, border: `1px solid ${isSel ? 'var(--accent-lit)' : 'var(--border)'}`,
                        background: isSel ? 'rgba(28,48,94,0.1)' : 'var(--surface)', transition: 'all 0.15s',
                      }}>
                        <input type="checkbox" checked={isSel}
                          onChange={() => setSelectedAttIds(p => isSel ? p.filter(id => id !== att.id) : [...p, att.id])}
                          style={{ width: 14, height: 14, cursor: 'pointer', flexShrink: 0 }} />
                        <FileText size={13} color={isSel ? 'var(--accent-lit)' : 'var(--subtext)'} style={{ flexShrink: 0 }} />
                        <span style={{ flex: 1, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text)' }}>
                          {att.original_filename}
                        </span>
                        <span style={{ fontSize: 11, color: 'var(--subtext)', flexShrink: 0 }}>{fmtSize(att.file_size)}</span>
                        {att.is_shared && <Globe size={11} color="var(--accent-lit)" style={{ flexShrink: 0 }} />}
                        {(user?.is_admin || att.uploaded_by === user?.id) && (
                          <button className="btn-icon" title="Delete from library permanently"
                            onClick={e => { e.stopPropagation(); if (confirm(`Delete ${att.original_filename}?`)) deleteAttMut.mutate(att.id) }}
                            style={{ color: 'var(--error)', width: 22, height: 22, flexShrink: 0 }}>
                            <X size={11} />
                          </button>
                        )}
                      </div>
                    )
                  })}
                </div>
                <p style={{ fontSize: 11, color: 'var(--subtext)', marginTop: 8 }}>
                  ☑ = attached to this template · ✕ = remove from file library
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
