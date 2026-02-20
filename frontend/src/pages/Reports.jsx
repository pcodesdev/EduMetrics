import { useState, useMemo } from 'react'
import { useData } from '../App'
import {
    downloadClassPdf, downloadStudentPdf, downloadExcel,
    openClassPdf, openStudentPdf,
} from '../api'
import {
    FileText, Download, Loader2, CheckCircle, AlertCircle,
    Users, User, Table, Eye, Printer,
} from 'lucide-react'

function ReportCard({
    icon: Icon, title, description, onPreview = () => {}, onDownload = () => {},
    loading, done, error, disablePreview, disableDownload,
}) {
    return (
        <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-all duration-200">
            <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-brand-accent/10 flex items-center justify-center shrink-0">
                    <Icon size={22} className="text-brand-accent" />
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed">{description}</p>
                    {error && (
                        <div className="flex items-center gap-1.5 mt-2 text-xs text-danger">
                            <AlertCircle size={12} /> {error}
                        </div>
                    )}
                    {done && (
                        <div className="flex items-center gap-1.5 mt-2 text-xs text-success">
                            <CheckCircle size={12} /> Downloaded!
                        </div>
                    )}
                </div>
                <div className="flex items-center gap-2 shrink-0 flex-wrap">
                    <button
                        onClick={onPreview}
                        disabled={loading || disablePreview}
                        className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium
                                   border border-brand-accent text-brand-accent hover:bg-brand-accent/10 transition-colors
                                   disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? <Loader2 size={16} className="animate-spin" /> : <Eye size={16} />}
                        Preview
                    </button>
                    <button
                        onClick={onDownload}
                        disabled={loading || disableDownload}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                                   bg-brand-accent text-white hover:bg-brand-dark transition-colors
                                   shadow-md shadow-brand-accent/20
                                   disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                        Download
                    </button>
                </div>
            </div>
        </div>
    )
}

export default function Reports() {
    const { data } = useData()
    const [loading, setLoading] = useState({})
    const [done, setDone] = useState({})
    const [errors, setErrors] = useState({})
    const [selectedClass, setSelectedClass] = useState('')
    const [selectedStudent, setSelectedStudent] = useState('')
    const [studentQuery, setStudentQuery] = useState('')

    // Extract unique classes and students from data
    const { classes, students } = useMemo(() => {
        if (!data || !Array.isArray(data)) return { classes: [], students: [] }
        const classCol = ['class', 'grade', 'stream', 'form'].find(c =>
            data[0] && c in data[0]
        )
        const classSet = classCol ? [...new Set(data.map(r => r[classCol]).filter(Boolean))] : []

        const nameCol = ['student_name', 'name', 'student'].find(c =>
            data[0] && c in data[0]
        )
        const idCol = ['student_id', 'id', 'admission_no'].find(c =>
            data[0] && c in data[0]
        )
        const studentList = []
        const seen = new Set()
        data.forEach(r => {
            const sid = String(r[idCol] || r[nameCol] || '').trim()
            const nm = String(r[nameCol] || sid || '').trim()
            if (sid && !seen.has(sid)) {
                seen.add(sid)
                studentList.push({ id: sid, name: nm })
            }
        })

        return { classes: classSet.sort(), students: studentList.sort((a, b) => String(a.name).localeCompare(String(b.name))) }
    }, [data])

    const filteredStudents = useMemo(() => {
        const q = studentQuery.trim().toLowerCase()
        if (!q) return students.slice(0, 12)
        return students.filter(s =>
            String(s.id).toLowerCase().includes(q) || String(s.name).toLowerCase().includes(q)
        ).slice(0, 12)
    }, [students, studentQuery])

    const resolvedStudentId = useMemo(() => {
        if (selectedStudent) return selectedStudent
        const q = studentQuery.trim().toLowerCase()
        if (!q) return ''

        const exactId = students.find(s => String(s.id).toLowerCase() === q)
        if (exactId) return exactId.id

        const exactName = students.find(s => String(s.name).toLowerCase() === q)
        if (exactName) return exactName.id

        const partial = students.filter(s =>
            String(s.id).toLowerCase().includes(q) || String(s.name).toLowerCase().includes(q)
        )
        return partial.length === 1 ? partial[0].id : ''
    }, [selectedStudent, studentQuery, students])

    const generate = async (key, fn) => {
        setLoading(l => ({ ...l, [key]: true }))
        setErrors(e => ({ ...e, [key]: null }))
        setDone(d => ({ ...d, [key]: false }))
        try {
            await fn()
            setDone(d => ({ ...d, [key]: true }))
            setTimeout(() => setDone(d => ({ ...d, [key]: false })), 3000)
        } catch (e) {
            setErrors(er => ({ ...er, [key]: e.message }))
        } finally {
            setLoading(l => ({ ...l, [key]: false }))
        }
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Generate Reports</h1>
                <p className="text-sm text-gray-500 mt-1">
                    Download professionally formatted PDF reports and Excel exports
                </p>
            </div>

            <div className="space-y-4">
                {/* Class Performance Report (Merged School + Class) */}
                <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-6">
                    <div className="flex items-start gap-4 flex-wrap">
                        <div className="w-12 h-12 rounded-xl bg-brand-accent/10 flex items-center justify-center shrink-0">
                            <Users size={22} className="text-brand-accent" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <h3 className="text-sm font-semibold text-gray-800">Class Performance Report (PDF)</h3>
                            <p className="text-xs text-gray-500 mt-1">Merged report: school context + selected class analysis in one PDF.</p>
                            {errors.class && (
                                <div className="flex items-center gap-1.5 mt-2 text-xs text-danger">
                                    <AlertCircle size={12} /> {errors.class}
                                </div>
                            )}
                            {done.class && (
                                <div className="flex items-center gap-1.5 mt-2 text-xs text-success">
                                    <CheckCircle size={12} /> Downloaded!
                                </div>
                            )}
                        </div>
                        <div className="flex items-center gap-2 shrink-0 flex-wrap w-full lg:w-auto">
                            <select
                                value={selectedClass}
                                onChange={e => setSelectedClass(e.target.value)}
                                className="text-sm px-3 py-2.5 rounded-lg border border-gray-200 min-w-[10rem] flex-1 sm:flex-none
                                           focus:outline-none focus:ring-2 focus:ring-brand-accent/30"
                            >
                                <option value="">Select class…</option>
                                {classes.map(c => <option key={c} value={c}>{c}</option>)}
                            </select>
                            <button
                                onClick={() => generate('class', () => openClassPdf(data, selectedClass))}
                                disabled={loading.class || !selectedClass}
                                className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium
                                           border border-brand-accent text-brand-accent hover:bg-brand-accent/10 transition-colors
                                           disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading.class ? <Loader2 size={16} className="animate-spin" /> : <Eye size={16} />}
                                Preview
                            </button>
                            <button
                                onClick={() => generate('class', () => downloadClassPdf(data, selectedClass))}
                                disabled={loading.class || !selectedClass}
                                className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                                           bg-brand-accent text-white hover:bg-brand-dark transition-colors shadow-md shadow-brand-accent/20
                                           disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading.class ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                                Download
                            </button>
                        </div>
                    </div>
                </div>

                {/* Student Report */}
                <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-6">
                    <div className="flex items-start gap-4 flex-wrap">
                        <div className="w-12 h-12 rounded-xl bg-brand-accent/10 flex items-center justify-center shrink-0">
                            <User size={22} className="text-brand-accent" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <h3 className="text-sm font-semibold text-gray-800">Student Report Card (PDF)</h3>
                            <p className="text-xs text-gray-500 mt-1">Search by admission number or name. Exact match or a single unique match auto-selects the student.</p>
                            {errors.student && (
                                <div className="flex items-center gap-1.5 mt-2 text-xs text-danger">
                                    <AlertCircle size={12} /> {errors.student}
                                </div>
                            )}
                            {done.student && (
                                <div className="flex items-center gap-1.5 mt-2 text-xs text-success">
                                    <CheckCircle size={12} /> Downloaded!
                                </div>
                            )}
                        </div>
                        <div className="flex flex-col gap-2 shrink-0 w-full lg:w-[360px]">
                            <input
                                value={studentQuery}
                                onChange={e => {
                                    setStudentQuery(e.target.value)
                                    setSelectedStudent('')
                                }}
                                placeholder="Search by admission no or name..."
                                className="text-sm px-3 py-2 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-accent/30"
                            />
                            {filteredStudents.length > 0 && (
                                <div className="max-h-28 overflow-y-auto border border-gray-100 rounded-md bg-white">
                                    {filteredStudents.map(s => (
                                        <button
                                            key={s.id}
                                            type="button"
                                            onClick={() => {
                                                setSelectedStudent(s.id)
                                                setStudentQuery(`${s.name} (${s.id})`)
                                            }}
                                            className="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50"
                                        >
                                            {s.name} ({s.id})
                                        </button>
                                    ))}
                                </div>
                            )}
                            <select
                                value={selectedStudent}
                                onChange={e => setSelectedStudent(e.target.value)}
                                className="text-sm px-3 py-2 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-accent/30"
                            >
                                <option value="">Select student...</option>
                                {filteredStudents.map(s => (
                                    <option key={s.id} value={s.id}>{s.name} ({s.id})</option>
                                ))}
                            </select>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => generate('student', () => openStudentPdf(data, resolvedStudentId))}
                                    disabled={loading.student || !resolvedStudentId}
                                    className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium
                                               border border-brand-accent text-brand-accent hover:bg-brand-accent/10 transition-colors
                                               disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading.student ? <Loader2 size={16} className="animate-spin" /> : <Printer size={16} />}
                                    Preview/Print
                                </button>
                                <button
                                    onClick={() => generate('student', () => downloadStudentPdf(data, resolvedStudentId))}
                                    disabled={loading.student || !resolvedStudentId}
                                className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                                           bg-brand-accent text-white hover:bg-brand-dark transition-colors shadow-md shadow-brand-accent/20
                                           disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading.student ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                                    Download
                                </button>
                            </div>
                            {!resolvedStudentId && studentQuery.trim() && (
                                <p className="text-[11px] text-amber-700">
                                    Search matched multiple students. Select one from the list above.
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Excel Export */}
                <ReportCard
                    icon={Table}
                    title="Excel Export (XLSX)"
                    description="Full dataset with computed columns, per-class sheets, and conditional formatting."
                    onDownload={() => generate('excel', () => downloadExcel(data))}
                    disablePreview
                    loading={loading.excel}
                    done={done.excel}
                    error={errors.excel}
                />
            </div>
        </div>
    )
}
