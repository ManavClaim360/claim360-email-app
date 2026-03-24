import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { dataApi } from '../utils/api'
import { Upload, Plus, Download, Zap, AlertTriangle, CheckCircle, Edit2, X, RefreshCw, FileSpreadsheet, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useData } from '../context/DataContext'

export let globalContacts = []
export let globalVarNames = []

function parseEmails(cell) {
  if (!cell) return []
  return String(cell).split(/[,;|\n]+/).map(e => e.trim().toLowerCase()).filter(e => /^[^@]+@[^@]+\.[^@]+$/.test(e))
}

export default function DataPage() {
  const { setContacts: setCtxContacts, setVarNames: setCtxVarNames } = useData()
  const [tab, setTab]                   = useState('variables')
  const [varNames, setVarNames]         = useState([])
  const [newVar, setNewVar]             = useState('')
  const [parsedData, setParsedData]     = useState(null)
  const [uploadedFileName, setUploadedFileName] = useState('')
  const [editingRows, setEditingRows]   = useState({})
  const [parseErrors, setParseErrors]   = useState([])
  const [dummyData, setDummyData]       = useState(null)
  const [editingDummy, setEditingDummy] = useState({})
  const [dummyCount, setDummyCount]     = useState(10)
  const [loading, setLoading]           = useState(false)

  const syncVars = (next) => {
    setVarNames(next)
    globalVarNames = next
    setCtxVarNames(next)
  }
  const syncContacts = (next) => {
    globalContacts = next
    setCtxContacts(next)
  }

  // ── Add variable — handles comma-separated input too ───────────
  const addVar = () => {
    const raw = newVar.trim()
    if (!raw) return
    // Support comma-separated: "name, company, position"
    const parts = raw.split(',').map(s => s.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')).filter(Boolean)
    const toAdd = parts.filter(v => !varNames.includes(v))
    const dupes = parts.filter(v => varNames.includes(v))
    if (dupes.length) toast.error(`Already exists: ${dupes.join(', ')}`)
    if (!toAdd.length) { setNewVar(''); return }
    syncVars([...varNames, ...toAdd])
    setNewVar('')
    toast.success(`Added: ${toAdd.join(', ')}`)
  }

  const removeVar = (i) => syncVars(varNames.filter((_, idx) => idx !== i))

  const clearVars = () => { syncVars([]); toast('Variables cleared') }

  // ── Excel Upload ────────────────────────────────────────────────
  const onDrop = useCallback(async (files) => {
    const file = files[0]; if (!file) return
    setUploadedFileName(file.name)
    setLoading(true)
    try {
      const result = await dataApi.parseExcel(file)
      setParsedData(result)
      setParseErrors(result.errors || [])
      setEditingRows({})
      const emailCol = result.headers.find(h => h.toLowerCase().includes('email'))
      const extras = result.headers.filter(h => h !== emailCol && h.toLowerCase() !== 'cc')
      const merged = [...new Set([...varNames, ...extras])]
      syncVars(merged)
      toast.success(`${result.total_rows} rows parsed from ${file.name}`)
    } catch { toast.error('Failed to parse file') } finally { setLoading(false) }
  }, [varNames])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
  })

  const deleteExcelRow = (i) => {
    const rows = parsedData.rows.filter((_, idx) => idx !== i)
    setParsedData({ ...parsedData, rows, total_rows: rows.length })
  }
  const startEditRow  = (i) => setEditingRows(p => ({ ...p, [i]: { ...parsedData.rows[i] } }))
  const cancelEditRow = (i) => setEditingRows(p => { const n = { ...p }; delete n[i]; return n })
  const saveEditRow   = (i) => {
    const rows = [...parsedData.rows]; rows[i] = editingRows[i]
    setParsedData({ ...parsedData, rows }); cancelEditRow(i)
  }
  const clearExcel = () => { setParsedData(null); setParseErrors([]); setEditingRows({}); setUploadedFileName('') }

  const useExcelData = () => {
    if (!parsedData) return
    const headers = parsedData.headers
    const emailCol = headers.find(h => h.toLowerCase().includes('receivers email') || h.toLowerCase() === 'email')
    if (!emailCol) { toast.error('No email column found'); return }

    const contacts = []
    for (const row of parsedData.rows) {
      const emailCell = row[emailCol] || ''
      const emails = parseEmails(emailCell)
      if (!emails.length) continue
      // All emails go to "to" — user controls CC in Send page
      const variables = Object.fromEntries(
        Object.entries(row).filter(([k]) => k !== emailCol)
      )
      contacts.push({ email: emails[0], extra_to: emails.slice(1), cc_emails: [], variables })
    }
    syncContacts(contacts)
    toast.success(`${contacts.length} contacts loaded!`)
  }

  const downloadSample = async () => {
    if (!varNames.length) { toast.error('Add variables first'); return }
    try {
      const blob = await dataApi.sampleExcel(varNames.join(','))
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = 'sample_contacts.xlsx'; a.click()
      URL.revokeObjectURL(url)
    } catch { toast.error('Download failed') }
  }

  // ── Dummy data ──────────────────────────────────────────────────
  const generateDummy = async () => {
    if (!varNames.length) { toast.error('Add variables first'); return }
    setLoading(true)
    try {
      const result = await dataApi.generateDummy(varNames, dummyCount)
      setDummyData(result.rows); setEditingDummy({})
      toast.success(`${result.rows.length} rows generated`)
    } catch { } finally { setLoading(false) }
  }
  const deleteDummyRow  = (i) => setDummyData(p => p.filter((_, idx) => idx !== i))
  const startEditDummy  = (i) => setEditingDummy(p => ({ ...p, [i]: { ...dummyData[i] } }))
  const cancelEditDummy = (i) => setEditingDummy(p => { const n = { ...p }; delete n[i]; return n })
  const saveEditDummy   = (i) => {
    const rows = [...dummyData]; rows[i] = editingDummy[i]; setDummyData(rows); cancelEditDummy(i)
  }
  const useDummyData = () => {
    if (!dummyData) return
    const contacts = dummyData.map(r => { const { email, ...vars } = r; return { email, cc_emails: [], variables: vars } })
    syncContacts(contacts)
    toast.success(`${contacts.length} contacts loaded!`)
  }

  const TABS = [
    { id: 'variables', label: '① Variables' },
    { id: 'upload',    label: '② Upload Excel' },
    { id: 'dummy',     label: '③ Dummy Data' },
  ]
  const tabStyle = (id) => ({
    padding: '8px 16px', borderRadius: '6px 6px 0 0', border: '1px solid transparent',
    cursor: 'pointer', fontSize: 13, fontWeight: 500, marginBottom: -1,
    background: tab === id ? 'rgba(255,255,255,0.08)' : 'transparent',
    color: tab === id ? 'var(--accent-lit)' : 'var(--subtext)',
    borderColor: tab === id ? 'rgba(255,255,255,0.15)' : 'transparent',
    borderBottom: tab === id ? '2px solid var(--accent-lit)' : '2px solid transparent',
    transition: 'all 0.15s',
  })

  // Shared editable table component
  const DataTable = ({ headers, rows, editingMap, onEdit, onSave, onCancel, onDelete, onEditChange }) => (
    <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: 400, borderRadius: 8, border: '1px solid var(--border)' }}>
      <table style={{ minWidth: 'max-content', width: '100%' }}>
        <thead>
          <tr>
            <th style={{ position: 'sticky', left: 0, background: 'var(--card)', zIndex: 2 }}>#</th>
            {headers.map(h => <th key={h} title={h}>{h === 'Receivers Email' ? 'Receivers Email' : h}</th>)}
            <th style={{ width: 72, position: 'sticky', right: 0, background: 'var(--card)', zIndex: 2 }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              <td style={{ position: 'sticky', left: 0, background: 'var(--surface)', color: 'var(--subtext)', fontSize: 11, zIndex: 1 }}>{i + 1}</td>
              {headers.map(h => (
                <td key={h} style={{ minWidth: 120, maxWidth: 200 }}>
                  {editingMap[i] ? (
                    <input value={editingMap[i][h] || ''} onChange={e => onEditChange(i, h, e.target.value)}
                      style={{ padding: '3px 6px', fontSize: 12, minWidth: 100 }} />
                  ) : (
                    <span style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 180 }} title={String(row[h] || '')}>{row[h] || ''}</span>
                  )}
                </td>
              ))}
              <td style={{ position: 'sticky', right: 0, background: 'var(--surface)', zIndex: 1 }}>
                <div style={{ display: 'flex', gap: 4 }}>
                  {editingMap[i] ? (
                    <>
                      <button className="btn-icon" onClick={() => onSave(i)} title="Save" style={{ color: 'var(--success)', width: 26, height: 26 }}>✓</button>
                      <button className="btn-icon" onClick={() => onCancel(i)} title="Cancel" style={{ width: 26, height: 26 }}><X size={11} /></button>
                    </>
                  ) : (
                    <>
                      <button className="btn-icon" onClick={() => onEdit(i)} title="Edit" style={{ width: 26, height: 26 }}><Edit2 size={11} /></button>
                      <button className="btn-icon" onClick={() => onDelete(i)} title="Delete" style={{ color: 'var(--error)', width: 26, height: 26 }}><Trash2 size={11} /></button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Data & Variables</h1>
        <p>Define merge variables, upload contacts, or generate test data</p>
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border)' }}>
        {TABS.map(t => <button key={t.id} onClick={() => setTab(t.id)} style={tabStyle(t.id)}>{t.label}</button>)}
      </div>

      {/* ── VARIABLES TAB ── */}
      {tab === 'variables' && (
        <div className="res-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600 }}>Define Variables</h3>
              {varNames.length > 0 && (
                <button className="btn-icon" onClick={clearVars} title="Clear all variables" style={{ width: 24, height: 24 }}>
                  <Trash2 size={11} />
                </button>
              )}
            </div>
            <p style={{ fontSize: 12, color: 'var(--subtext)', marginBottom: 14 }}>
              Type one name or multiple comma-separated: <code style={{ background: 'var(--hover)', padding: '1px 5px', borderRadius: 3, fontSize: 11, fontFamily: 'var(--mono)', color: 'var(--accent-lit)' }}>name, company, position</code>
            </p>

            {/* Input row */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
              <input
                value={newVar}
                onChange={e => setNewVar(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addVar()}
                placeholder="name, company, position (comma-separated)"
              />
              <button className="btn-primary" onClick={addVar} title="Add variable(s)" style={{ flexShrink: 0, padding: '8px 14px', display: 'flex', alignItems: 'center', gap: 5 }}>
                <Plus size={14} /> Add
              </button>
            </div>

            {/* Tag cloud — variables as chips, not full rows */}
            {varNames.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {varNames.map((v, i) => (
                  <div key={v} style={{
                    display: 'inline-flex', alignItems: 'center', gap: 5,
                    padding: '4px 10px', borderRadius: 20,
                    background: 'rgba(168,200,240,0.12)',
                    border: '1px solid rgba(168,200,240,0.3)',
                    fontSize: 13, fontFamily: 'var(--mono)', color: 'var(--accent-lit)',
                    flexShrink: 0,
                  }}>
                    <span>{`{{${v}}}`}</span>
                    <button
                      onClick={() => removeVar(i)}
                      title={`Remove {{${v}}}`}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0 0 0 2px', color: 'rgba(168,200,240,0.6)', display: 'flex', alignItems: 'center', lineHeight: 1 }}>
                      <X size={11} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--subtext)', fontSize: 12, fontStyle: 'italic' }}>No variables yet — type above and press Enter or Add.</p>
            )}
          </div>

          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>Download Sample Excel</h3>
            <p style={{ fontSize: 12, color: 'var(--subtext)', marginBottom: 14 }}>
              Download a pre-formatted Excel with your variable columns ready to fill.
            </p>
            <button className="btn-primary" onClick={downloadSample} title="Download Excel template"
              style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 14 }}>
              <Download size={14} /> Download Sample (.xlsx)
            </button>

            {varNames.length > 0 && (
              <div style={{ padding: '10px 12px', background: 'var(--surface)', borderRadius: 6, border: '1px solid var(--border)', marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: 'var(--subtext)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.4 }}>Columns in download</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  <span className="badge badge-info">Receivers Email</span>
                  {varNames.map(v => <span key={v} className="badge badge-info">{v}</span>)}
                </div>
              </div>
            )}

            <div style={{ padding: '10px 12px', background: 'rgba(210,153,34,0.08)', borderRadius: 6, border: '1px solid rgba(210,153,34,0.25)', fontSize: 12, color: 'var(--subtext)' }}>
              <strong style={{ color: 'var(--warning)', display: 'block', marginBottom: 4 }}>📌 Multiple emails in one cell</strong>
              Put multiple emails separated by comma in the email column:<br/>
              <code style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--accent-lit)' }}>abc@gmail.com,xyz@yahoo.com</code><br/>
              <span style={{ fontSize: 11, marginTop: 4, display: 'block' }}>First = primary To, rest go to additional To addresses.</span>
              <strong style={{ color: 'var(--warning)', display: 'block', marginTop: 8, marginBottom: 2 }}>📌 CC emails</strong>
              CC recipients are added in the <strong>Send Email</strong> page and apply to all emails in the campaign.
            </div>
          </div>
        </div>
      )}

      {/* ── UPLOAD TAB ── */}
      {tab === 'upload' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {parsedData ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px', background: 'rgba(63,185,80,0.08)', borderRadius: 8, border: '1px solid rgba(63,185,80,0.25)' }}>
              <FileSpreadsheet size={20} color="var(--success)" style={{ flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text)' }}>{uploadedFileName}</div>
                <div style={{ fontSize: 12, color: 'var(--subtext)' }}>{parsedData.total_rows} rows · {parsedData.headers.length} columns</div>
              </div>
              <label style={{ cursor: 'pointer', flexShrink: 0 }}>
                <input type="file" accept=".xlsx,.xls,.csv" style={{ display: 'none' }}
                  onChange={e => { if (e.target.files[0]) onDrop([e.target.files[0]]) }} />
                <span className="btn-secondary" style={{ fontSize: 12, padding: '5px 12px', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                  <Upload size={12} /> Replace
                </span>
              </label>
              <button className="btn-secondary" onClick={clearExcel}
                style={{ fontSize: 12, padding: '5px 12px', display: 'flex', alignItems: 'center', gap: 4, color: 'var(--error)', borderColor: 'rgba(248,81,73,0.35)', flexShrink: 0 }}>
                <X size={12} /> Clear
              </button>
            </div>
          ) : (
          <div {...getRootProps()} style={{
            border: `2px dashed ${isDragActive ? 'var(--accent-lit)' : 'var(--border)'}`,
            borderRadius: 10, padding: 36, textAlign: 'center', cursor: 'pointer',
            background: isDragActive ? 'rgba(168,200,240,0.06)' : 'var(--surface)',
            transition: 'all 0.2s',
          }}>
              <input {...getInputProps()} />
              <Upload size={26} color={isDragActive ? 'var(--accent-lit)' : 'var(--subtext)'} style={{ marginBottom: 10 }} />
              <div style={{ fontWeight: 600, marginBottom: 4, fontSize: 14, color: 'var(--text)' }}>
                {isDragActive ? 'Drop your file here' : 'Drag & drop Excel or CSV'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--subtext)' }}>.xlsx · .xls · .csv — must have a "Receivers Email" column</div>
            </div>
          )}

          {loading && <div style={{ textAlign: 'center', padding: 16 }}><span className="spinner" /></div>}

          {parseErrors.length > 0 && (
            <div style={{ padding: '10px 14px', background: 'rgba(210,153,34,0.08)', border: '1px solid rgba(210,153,34,0.25)', borderRadius: 8 }}>
              {parseErrors.slice(0, 5).map((e, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, fontSize: 12, color: 'var(--warning)', marginBottom: 3 }}>
                  <AlertTriangle size={12} style={{ marginTop: 2, flexShrink: 0 }} /> {e}
                </div>
              ))}
            </div>
          )}

          {parsedData && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <CheckCircle size={15} color="var(--success)" />
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{parsedData.total_rows} rows · {parsedData.headers.length} columns</span>
                </div>
                <button className="btn-success" onClick={useExcelData} style={{ fontSize: 12, padding: '5px 14px' }}>
                  ✅ Use This Data
                </button>
              </div>
              <div style={{ padding: '8px 14px' }}>
                <DataTable
                  headers={parsedData.headers}
                  rows={parsedData.rows}
                  editingMap={editingRows}
                  onEdit={startEditRow}
                  onSave={saveEditRow}
                  onCancel={cancelEditRow}
                  onDelete={deleteExcelRow}
                  onEditChange={(i, h, v) => setEditingRows(p => ({ ...p, [i]: { ...p[i], [h]: v } }))}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── DUMMY TAB ── */}
      {tab === 'dummy' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>Generate Test Data</h3>
            <p style={{ fontSize: 12, color: 'var(--subtext)', marginBottom: 14 }}>
              Generate realistic fake contacts based on your variable names.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <label style={{ fontSize: 13, color: 'var(--subtext)', whiteSpace: 'nowrap' }}>Count:</label>
                <input type="number" value={dummyCount} onChange={e => setDummyCount(+e.target.value)}
                  min={1} max={100} style={{ width: 80 }} />
              </div>
              <button className="btn-primary" onClick={generateDummy} disabled={loading || !varNames.length}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {loading ? <span className="spinner" style={{ width: 13, height: 13 }} /> : <Zap size={13} />} Generate
              </button>
              {dummyData && (
                <>
                  <button className="btn-secondary" onClick={generateDummy}
                    style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12 }}>
                    <RefreshCw size={12} /> Regenerate
                  </button>
                  <button className="btn-success" onClick={useDummyData} style={{ fontSize: 12 }}>
                    ✅ Use This Data
                  </button>
                  <button className="btn-secondary" onClick={() => setDummyData(null)}
                    style={{ fontSize: 12, color: 'var(--error)', borderColor: 'rgba(248,81,73,0.35)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <X size={12} /> Clear
                  </button>
                </>
              )}
            </div>
            {!varNames.length && (
              <p style={{ fontSize: 12, color: 'var(--warning)', marginTop: 10 }}>⚠ Add variables in the Variables tab first.</p>
            )}
          </div>

          {dummyData && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{dummyData.length} test contacts</span>
                <button className="btn-success" onClick={useDummyData} style={{ fontSize: 12, padding: '5px 14px' }}>✅ Use This Data</button>
              </div>
              <div style={{ padding: '8px 14px' }}>
                <DataTable
                  headers={Object.keys(dummyData[0] || {})}
                  rows={dummyData}
                  editingMap={editingDummy}
                  onEdit={startEditDummy}
                  onSave={saveEditDummy}
                  onCancel={cancelEditDummy}
                  onDelete={deleteDummyRow}
                  onEditChange={(i, h, v) => setEditingDummy(p => ({ ...p, [i]: { ...p[i], [h]: v } }))}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
