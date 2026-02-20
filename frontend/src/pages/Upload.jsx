import { useState, useCallback, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useData } from '../App'
import { uploadFile, confirmMapping, loadSample, endUploadSession } from '../api'
import {
    UploadCloud, FileSpreadsheet, AlertCircle,
    ChevronRight, Loader2, X, ArrowRight, CalendarDays,
} from 'lucide-react'

const TERM_SLOTS = ['Term 1', 'Term 2', 'Term 3']
const REQUIRED_FIELDS = ['student_name', 'student_id']
const OPTIONAL_FIELDS = ['class', 'gender', 'region', 'term', 'year', 'exam_name']

function emptyTermState() {
    return TERM_SLOTS.reduce((acc, t) => {
        acc[t] = null
        return acc
    }, {})
}

export default function Upload() {
    const navigate = useNavigate()
    const { setData, sessionId, setSessionId, setFileName } = useData()
    const fileInput = useRef(null)

    const now = new Date().getFullYear()
    const [selectedYear, setSelectedYear] = useState(String(now))
    const [activeTerm, setActiveTerm] = useState(null)

    const [step, setStep] = useState('upload')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [dragOver, setDragOver] = useState(false)

    const [uploadResult, setUploadResult] = useState(null)
    const [mapping, setMapping] = useState({})
    const [termRows, setTermRows] = useState(emptyTermState())
    const [termMeta, setTermMeta] = useState(emptyTermState())

    const uploadedTerms = TERM_SLOTS.filter(t => Array.isArray(termRows[t]) && termRows[t]?.length > 0)
    const combinedRows = TERM_SLOTS.flatMap(t => termRows[t] || [])

    useEffect(() => {
        const onBeforeUnload = () => {
            try {
                const form = new FormData()
                if (sessionId) form.append('session_id', sessionId)
                navigator.sendBeacon('/api/upload/end-session', form)
            } catch {
                // no-op
            }
        }
        window.addEventListener('beforeunload', onBeforeUnload)
        return () => window.removeEventListener('beforeunload', onBeforeUnload)
    }, [sessionId])

    const handleStartTermUpload = (term) => {
        if (loading) return
        setActiveTerm(term)
        setError(null)
        fileInput.current?.click()
    }

    const handleFile = useCallback(async (file) => {
        if (!file || !activeTerm) return
        setError(null)
        setLoading(true)
        try {
            const result = await uploadFile(file)
            setUploadResult(result)
            setMapping(result.suggested_mapping || {})
            setFileName(file.name)
            setSessionId(result.session_id)
            setStep('mapping')
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
            if (fileInput.current) fileInput.current.value = ''
        }
    }, [activeTerm, setFileName, setSessionId])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files[0]
        if (file) handleFile(file)
    }, [handleFile])

    const handleConfirmMapping = async () => {
        if (!uploadResult || !activeTerm) return
        setError(null)
        setLoading(true)
        try {
            const result = await confirmMapping(uploadResult.session_id, mapping)
            const cleaned = Array.isArray(result.cleaned_data) ? result.cleaned_data : (result.preview || [])
            const normalized = cleaned.map((row) => ({
                ...row,
                term: activeTerm,
                year: row?.year ? String(row.year) : String(selectedYear),
            }))

            setTermRows(prev => {
                const next = { ...prev, [activeTerm]: normalized }
                setData(TERM_SLOTS.flatMap(t => next[t] || []))
                return next
            })
            setTermMeta(prev => ({
                ...prev,
                [activeTerm]: {
                    file_name: uploadResult.filename,
                    row_count: normalized.length,
                    uploaded_at: new Date().toISOString(),
                },
            }))

            setStep('upload')
            setUploadResult(null)
            setMapping({})
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    const handleLoadSample = async (type = 'secondary') => {
        setError(null)
        setLoading(true)
        try {
            const result = await loadSample(type)
            const byTerm = emptyTermState()
            for (const row of (result.preview || [])) {
                if (TERM_SLOTS.includes(row.term)) {
                    byTerm[row.term] = byTerm[row.term] || []
                    byTerm[row.term].push({ ...row, year: row?.year ? String(row.year) : String(selectedYear) })
                }
            }
            setTermRows(prev => {
                const next = { ...prev, ...byTerm }
                setData(TERM_SLOTS.flatMap(t => next[t] || []))
                return next
            })
            setFileName(result.filename)
            setSessionId(result.session_id)
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    const resetYear = (year) => {
        setSelectedYear(year)
        setTermRows(emptyTermState())
        setTermMeta(emptyTermState())
        setData(null)
        setStep('upload')
        setUploadResult(null)
        setMapping({})
        setActiveTerm(null)
        setError(null)
    }

    const handleEndSecureSession = async () => {
        setError(null)
        setLoading(true)
        try {
            await endUploadSession()
            setTermRows(emptyTermState())
            setTermMeta(emptyTermState())
            setData(null)
            setSessionId(null)
            setFileName('')
            setStep('upload')
            setUploadResult(null)
            setMapping({})
            setActiveTerm(null)
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    const updateMapping = (field, col) => {
        setMapping(m => ({ ...m, [field]: col }))
    }

    return (
        <div className="max-w-4xl mx-auto animate-fade-in">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900">Annual Term Upload (3 Terms)</h1>
                <p className="text-sm text-gray-500 mt-1">
                    Upload one dataset per term. The system supports only Term 1, Term 2, and Term 3 for the selected year.
                </p>
            </div>

            <div className="mb-6 p-4 rounded-xl border border-amber-200 bg-amber-50">
                <p className="text-xs font-semibold text-amber-800">Data Security Notice</p>
                <p className="text-xs text-amber-700 mt-1">
                    Uploaded files are temporary. They are deleted after processing, sessions auto-expire, and you can end the session at any time to purge all in-memory data.
                </p>
                <button
                    onClick={handleEndSecureSession}
                    disabled={loading}
                    className="mt-3 text-xs px-3 py-1.5 rounded-md bg-amber-700 text-white hover:bg-amber-800 disabled:opacity-50"
                >
                    End Session & Delete Data
                </button>
            </div>

            {error && (
                <div className="mb-6 flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-xl text-sm text-danger animate-fade-in">
                    <AlertCircle size={18} className="mt-0.5 shrink-0" />
                    <div>
                        <p className="font-medium">Upload Error</p>
                        <p className="text-red-600/80 mt-0.5">{error}</p>
                    </div>
                    <button onClick={() => setError(null)} className="ml-auto"><X size={16} /></button>
                </div>
            )}

            <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
                <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <CalendarDays size={16} className="text-brand-accent" />
                        <p className="text-sm font-semibold text-gray-700">Academic Year</p>
                    </div>
                    <select
                        value={selectedYear}
                        onChange={e => resetYear(e.target.value)}
                        className="text-sm px-3 py-2 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-accent/30"
                    >
                        {[now - 1, now, now + 1].map(y => <option key={y} value={String(y)}>{y}</option>)}
                    </select>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                    Uploaded terms: {uploadedTerms.length}/3
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {TERM_SLOTS.map((term, i) => {
                    const meta = termMeta[term]
                    const isDone = !!meta
                    return (
                        <div key={term} className={`rounded-xl border p-4 ${isDone ? 'border-emerald-200 bg-emerald-50/50' : 'border-gray-200 bg-white'}`}>
                            <p className="text-sm font-semibold text-gray-800">{term}</p>
                            <p className="text-xs text-gray-500 mt-1">
                                {isDone ? `${meta.row_count} rows uploaded` : 'Not uploaded'}
                            </p>
                            <button
                                onClick={() => handleStartTermUpload(term)}
                                disabled={loading}
                                className="mt-3 w-full text-xs px-3 py-2 rounded-lg bg-brand-accent text-white hover:bg-brand-dark disabled:opacity-50"
                            >
                                {isDone ? 'Replace Upload' : 'Upload Scores'}
                            </button>
                            {i > 0 && !termMeta[TERM_SLOTS[i - 1]] && (
                                <p className="text-[11px] text-amber-700 mt-2">Upload {TERM_SLOTS[i - 1]} first for progressive comparison.</p>
                            )}
                        </div>
                    )
                })}
            </div>

            {step === 'upload' && (
                <div className="space-y-4">
                    <div
                        onDrop={handleDrop}
                        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                        onDragLeave={() => setDragOver(false)}
                        onClick={() => activeTerm && fileInput.current?.click()}
                        className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-300
                            ${dragOver ? 'border-brand-accent bg-brand-accent/5' : 'border-gray-200 bg-white'}`}
                    >
                        <input
                            ref={fileInput}
                            type="file"
                            accept=".csv,.xlsx,.xls,.ods"
                            onChange={e => handleFile(e.target.files[0])}
                            className="hidden"
                        />
                        {loading ? (
                            <div className="flex flex-col items-center gap-3">
                                <Loader2 size={36} className="text-brand-accent animate-spin" />
                                <p className="text-sm text-gray-500">Processing upload…</p>
                            </div>
                        ) : (
                            <>
                                <div className="w-14 h-14 mx-auto rounded-xl bg-brand-accent/10 flex items-center justify-center mb-3">
                                    <UploadCloud size={24} className="text-brand-accent" />
                                </div>
                                <p className="text-sm font-medium text-gray-700">
                                    {activeTerm
                                        ? `Selected slot: ${activeTerm}. Drag/drop or click to upload.`
                                        : 'Select a term slot above first, then upload.'}
                                </p>
                                <p className="text-xs text-gray-400 mt-2">Supports CSV, XLSX, XLS, ODS</p>
                            </>
                        )}
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                        <button
                            onClick={() => handleLoadSample('secondary')}
                            disabled={loading}
                            className="text-xs px-3 py-2 rounded-lg bg-brand-dark text-white hover:bg-brand-accent disabled:opacity-50"
                        >
                            Load Secondary Sample
                        </button>
                        <button
                            onClick={() => handleLoadSample('cbc')}
                            disabled={loading}
                            className="text-xs px-3 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
                        >
                            Load Alternative Sample
                        </button>
                        {uploadedTerms.length >= 1 && (
                            <button
                                onClick={() => navigate('/term-comparison')}
                                className="text-xs px-3 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
                            >
                                Open Term Comparison
                            </button>
                        )}
                        {uploadedTerms.length === 3 && (
                            <button
                                onClick={() => navigate('/overview')}
                                className="text-xs px-3 py-2 rounded-lg bg-emerald-700 text-white hover:bg-emerald-800"
                            >
                                Open Full Dashboard
                            </button>
                        )}
                    </div>
                </div>
            )}

            {step === 'mapping' && uploadResult && (
                <div className="animate-fade-in">
                    <div className="bg-card rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="flex items-center gap-3 px-5 py-4 bg-surface-alt border-b border-gray-100">
                            <FileSpreadsheet size={20} className="text-brand-accent" />
                            <div>
                                <p className="text-sm font-medium text-gray-700">
                                    {uploadResult.filename} {'->'} {activeTerm} ({selectedYear})
                                </p>
                                <p className="text-xs text-gray-400">
                                    {uploadResult.columns?.length} columns · {Object.values(uploadResult.sheet_row_counts || {})[0] || '?'} rows
                                </p>
                            </div>
                        </div>

                        <div className="p-5 space-y-3">
                            <p className="text-xs text-gray-500 mb-4">
                                Map only metadata columns. Keep subject columns unmapped when your sheet is wide-format.
                            </p>

                            {[...REQUIRED_FIELDS, ...OPTIONAL_FIELDS].map(field => (
                                <div key={field} className="flex items-center gap-3">
                                    <label className="w-36 text-xs font-medium text-gray-600 capitalize">
                                        {field.replace(/_/g, ' ')}
                                        {REQUIRED_FIELDS.includes(field) && <span className="text-danger ml-1">*</span>}
                                    </label>
                                    <select
                                        value={mapping[field] || ''}
                                        onChange={e => updateMapping(field, e.target.value)}
                                        className="flex-1 text-sm px-3 py-2 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-accent/30 focus:border-brand-accent"
                                    >
                                        <option value="">— skip —</option>
                                        {(uploadResult.columns || []).map(col => <option key={col} value={col}>{col}</option>)}
                                    </select>
                                </div>
                            ))}
                        </div>

                        <div className="flex items-center justify-between px-5 py-4 bg-surface-alt border-t border-gray-100">
                            <button
                                onClick={() => { setStep('upload'); setUploadResult(null) }}
                                className="text-sm text-gray-500 hover:text-gray-700"
                            >
                                ← Back
                            </button>
                            <button
                                onClick={handleConfirmMapping}
                                disabled={loading}
                                className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium bg-brand-accent text-white hover:bg-brand-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
                                Save {activeTerm} Upload
                            </button>
                        </div>
                    </div>

                    {uploadResult.preview?.length > 0 && (
                        <div className="mt-6">
                            <h3 className="text-sm font-semibold text-gray-700 mb-3">Preview</h3>
                            <div className="overflow-x-auto rounded-xl border border-gray-100 bg-card shadow-sm">
                                <table className="w-full text-xs">
                                    <thead>
                                        <tr className="bg-surface-alt">
                                            {Object.keys(uploadResult.preview[0]).map(col => (
                                                <th key={col} className="px-3 py-2 text-left font-semibold text-gray-500 whitespace-nowrap">{col}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50">
                                        {uploadResult.preview.slice(0, 5).map((row, i) => (
                                            <tr key={i}>
                                                {Object.values(row).map((val, j) => (
                                                    <td key={j} className="px-3 py-2 text-gray-600 whitespace-nowrap">{String(val ?? '')}</td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="mt-8 bg-slate-50 border border-slate-200 rounded-xl p-4">
                <p className="text-xs font-semibold text-slate-700 mb-2">Current merged dataset</p>
                <p className="text-xs text-slate-600">
                    {combinedRows.length} rows across {uploadedTerms.length} term(s) for {selectedYear}.
                </p>
                <div className="flex items-center gap-2 mt-3 text-[11px] text-slate-500">
                    {TERM_SLOTS.map((t, i) => (
                        <span key={t} className={`px-2 py-1 rounded ${termRows[t] ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'}`}>
                            {t}
                        </span>
                    ))}
                    <ChevronRight size={12} />
                    <span>Max uploads per year: 3</span>
                </div>
            </div>
        </div>
    )
}
