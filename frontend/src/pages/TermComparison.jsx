import { useState, useEffect } from 'react'
import { useData } from '../App'
import { getTermComparison } from '../api'
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    CartesianGrid, Legend, LineChart, Line, Label,
} from 'recharts'
import {
    TrendingUp, TrendingDown, Minus, Loader2, Award,
    Users, BookOpen, ChevronDown, ChevronUp,
} from 'lucide-react'

// ── Colour palette: Term 1=blue, Term 2=amber, Term 3=emerald ───────
const TERM_COLORS = ['#0f3460', '#f59e0b', '#10b981']
const TERM_LIGHT = ['#dbeafe', '#fef3c7', '#d1fae5']

function studentLabel(name, studentId) {
    const n = (name || '').toString().trim()
    const sid = (studentId || '').toString().trim()
    if (n && sid && n.toLowerCase() !== sid.toLowerCase()) return `${n} (${sid})`
    return n || sid || 'Unknown Student'
}

function TrendBadge({ delta, trend }) {
    if (!delta && trend === 'baseline') return (
        <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
            Baseline
        </span>
    )
    if (delta === null || delta === undefined) return null
    const positive = delta >= 0
    const stable = trend === 'stable'
    return (
        <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full
            ${stable ? 'bg-gray-100 text-gray-600'
                : positive ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-red-100 text-red-700'}`}>
            {stable ? <Minus size={10} /> : positive ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
            {positive && !stable ? '+' : ''}{delta !== null ? delta.toFixed(1) : '0'}%
        </span>
    )
}

function GradeBadge({ grade }) {
    const colors = {
        'EE': 'bg-emerald-100 text-emerald-800', 'ME': 'bg-blue-100 text-blue-800',
        'AE': 'bg-amber-100 text-amber-800', 'BE': 'bg-red-100 text-red-800',
        'A': 'bg-emerald-100 text-emerald-800', 'A-': 'bg-emerald-100 text-emerald-700',
        'B+': 'bg-blue-100 text-blue-800', 'B': 'bg-blue-100 text-blue-700',
        'B-': 'bg-blue-100 text-blue-600', 'C+': 'bg-amber-100 text-amber-800',
        'C': 'bg-amber-100 text-amber-700', 'C-': 'bg-orange-100 text-orange-700',
        'D+': 'bg-red-100 text-red-700', 'D': 'bg-red-100 text-red-800',
        'D-': 'bg-red-200 text-red-900', 'E': 'bg-red-300 text-red-900',
        '—': 'bg-gray-100 text-gray-400',
    }
    const cls = colors[grade] || 'bg-gray-100 text-gray-500'
    return (
        <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${cls}`}>{grade}</span>
    )
}

// ── School-level summary cards ────────────────────────────────────
function TermSummaryCards({ schoolByTerm, terms }) {
    return (
        <div className={`grid gap-4 mb-6`} style={{ gridTemplateColumns: `repeat(${terms.length}, minmax(0,1fr))` }}>
            {schoolByTerm.map((t, i) => (
                <div key={t.term}
                    className="bg-card rounded-xl p-4 shadow-sm border border-gray-100 animate-fade-in"
                    style={{ borderTop: `3px solid ${TERM_COLORS[i % TERM_COLORS.length]}` }}>
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-bold uppercase tracking-wider"
                            style={{ color: TERM_COLORS[i % TERM_COLORS.length] }}>
                            {t.term}
                        </p>
                        <GradeBadge grade={t.grade} />
                    </div>
                    <p className="text-2xl font-bold text-gray-900">
                        {t.mean != null ? `${t.mean.toFixed(1)}%` : '—'}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">School Mean</p>
                    <div className="mt-2 flex items-center justify-between">
                        <span className="text-xs text-gray-500">{t.pass_rate?.toFixed(1)}% pass rate</span>
                        <TrendBadge delta={t.delta} trend={t.trend} />
                    </div>
                </div>
            ))}
        </div>
    )
}

// ── Subject grouped bar chart ─────────────────────────────────────
function SubjectTermChart({ subjectsByTerm, terms }) {
    // Build chart data: [{subject, 'Term 1': mean, 'Term 2': mean, ...}]
    const chartData = subjectsByTerm.map(s => {
        const row = { subject: s.subject.length > 10 ? s.subject.slice(0, 10) + '…' : s.subject }
        terms.forEach(t => { row[t] = s.terms[t]?.mean ?? 0 })
        return row
    })

    return (
        <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
            <div className="flex items-center gap-2 mb-4">
                <BookOpen size={16} className="text-brand-accent" />
                <h3 className="text-sm font-semibold text-gray-700">Subject Performance by Term</h3>
            </div>
            <ResponsiveContainer width="100%" height={340}>
                <BarChart data={chartData} barCategoryGap="15%">
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="subject" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#e2e8f0' }}>
                        <Label value="Subjects" position="insideBottom" offset={-2} style={{ fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                    </XAxis>
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} domain={[0, 100]} tickFormatter={v => `${v}%`}>
                        <Label value="Mean Score (%)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                    </YAxis>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#0f172a',
                            border: '1px solid #334155',
                            borderRadius: 8,
                            fontSize: 12,
                            color: '#f8fafc',
                        }}
                        labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                        itemStyle={{ color: '#f8fafc' }}
                        formatter={(v, name) => [`${Number(v).toFixed(1)}%`, name]}
                        cursor={{ fill: 'rgba(15,52,96,0.06)' }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    {terms.map((t, i) => (
                        <Bar key={t} dataKey={t} fill={TERM_COLORS[i % TERM_COLORS.length]} radius={[4, 4, 0, 0]} maxBarSize={28} />
                    ))}
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}

// ── Student delta table ───────────────────────────────────────────
function StudentDeltaTable({ studentsByTerm, terms }) {
    const [showAll, setShowAll] = useState(false)
    const displayed = showAll ? studentsByTerm : studentsByTerm.slice(0, 15)

    return (
        <div className="bg-card rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-6">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                    <Users size={16} className="text-brand-accent" />
                    <h3 className="text-sm font-semibold text-gray-700">Student Term-by-Term Performance</h3>
                </div>
                <span className="text-xs text-gray-400">{studentsByTerm.length} students</span>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-xs">
                    <thead className="bg-surface-alt">
                        <tr>
                            <th className="px-4 py-2 text-left font-semibold text-gray-500 w-8">#</th>
                            <th className="px-4 py-2 text-left font-semibold text-gray-500">Student</th>
                            <th className="px-3 py-2 text-left font-semibold text-gray-500">Class</th>
                            {terms.map(t => (
                                <th key={t} className="px-3 py-2 text-center font-semibold text-gray-500">{t}</th>
                            ))}
                            <th className="px-3 py-2 text-center font-semibold text-gray-500">Overall</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {displayed.map((s, i) => (
                            <tr key={s.student_id}
                                className={`hover:bg-gray-50 transition-colors ${s.overall_trend === 'improving' ? '' : s.overall_trend === 'declining' ? 'bg-red-50/40' : ''}`}>
                                <td className="px-4 py-2 text-gray-400">{s.rank}</td>
                                <td className="px-4 py-2 font-medium text-gray-800">{studentLabel(s.name, s.student_id)}</td>
                                <td className="px-3 py-2 text-gray-500">{s.class || '—'}</td>
                                {terms.map((t, ti) => {
                                    const td = s.terms[t]
                                    return (
                                        <td key={t} className="px-3 py-2 text-center">
                                            {td ? (
                                                <div className="flex flex-col items-center gap-0.5">
                                                    <span className="font-medium text-gray-800">
                                                        {td.mean != null ? `${td.mean.toFixed(1)}%` : '—'}
                                                    </span>
                                                    <div className="flex items-center gap-1">
                                                        <GradeBadge grade={td.grade} />
                                                        {ti > 0 && <TrendBadge delta={td.delta} trend={td.trend} />}
                                                    </div>
                                                </div>
                                            ) : <span className="text-gray-300">—</span>}
                                        </td>
                                    )
                                })}
                                <td className="px-3 py-2 text-center">
                                    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full
                                        ${s.overall_trend === 'improving' ? 'bg-emerald-100 text-emerald-700'
                                            : s.overall_trend === 'declining' ? 'bg-red-100 text-red-700'
                                                : 'bg-gray-100 text-gray-600'}`}>
                                        {s.overall_trend === 'improving' ? <TrendingUp size={10} /> : s.overall_trend === 'declining' ? <TrendingDown size={10} /> : <Minus size={10} />}
                                        {s.overall_trend}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {studentsByTerm.length > 15 && (
                <button
                    onClick={() => setShowAll(v => !v)}
                    className="w-full py-2.5 text-xs text-brand-accent hover:bg-gray-50 flex items-center justify-center gap-1 transition-colors border-t border-gray-100">
                    {showAll ? <><ChevronUp size={14} /> Show less</> : <><ChevronDown size={14} /> Show all {studentsByTerm.length} students</>}
                </button>
            )}
        </div>
    )
}

// ── Improvers / Decliners ──────────────────────────────────────────
function LeaderCards({ improvers, decliners, firstTerm, lastTerm }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-card rounded-xl shadow-sm border border-emerald-100 p-5">
                <div className="flex items-center gap-2 mb-3">
                    <TrendingUp size={16} className="text-emerald-600" />
                    <h3 className="text-sm font-semibold text-gray-700">Most Improved</h3>
                    <span className="text-xs text-gray-400 ml-auto">{firstTerm} → {lastTerm}</span>
                </div>
                <div className="space-y-2">
                    {improvers.map((s, i) => (
                        <div key={i} className="flex items-center justify-between">
                            <span className="text-sm text-gray-700">{studentLabel(s.name, s.student_id)}</span>
                            <TrendBadge delta={s.delta} trend="improving" />
                        </div>
                    ))}
                    {improvers.length === 0 && <p className="text-xs text-gray-400">No data yet</p>}
                </div>
            </div>
            <div className="bg-card rounded-xl shadow-sm border border-red-100 p-5">
                <div className="flex items-center gap-2 mb-3">
                    <TrendingDown size={16} className="text-red-500" />
                    <h3 className="text-sm font-semibold text-gray-700">Most Declined</h3>
                    <span className="text-xs text-gray-400 ml-auto">{firstTerm} → {lastTerm}</span>
                </div>
                <div className="space-y-2">
                    {decliners.map((s, i) => (
                        <div key={i} className="flex items-center justify-between">
                            <span className="text-sm text-gray-700">{studentLabel(s.name, s.student_id)}</span>
                            <TrendBadge delta={s.delta} trend="declining" />
                        </div>
                    ))}
                    {decliners.length === 0 && <p className="text-xs text-gray-400">No data yet</p>}
                </div>
            </div>
        </div>
    )
}

// ── School trend line chart ───────────────────────────────────────
function SchoolTrendLine({ schoolByTerm }) {
    return (
        <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
            <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={16} className="text-brand-accent" />
                <h3 className="text-sm font-semibold text-gray-700">School Mean Trend Across Terms</h3>
            </div>
            <ResponsiveContainer width="100%" height={180}>
                <LineChart data={schoolByTerm}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="term" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#e2e8f0' }}>
                        <Label value="Terms" position="insideBottom" offset={-2} style={{ fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                    </XAxis>
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} domain={['auto', 'auto']} tickFormatter={v => `${v}%`}>
                        <Label value="Score / Pass Rate (%)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                    </YAxis>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#0f172a',
                            border: '1px solid #334155',
                            borderRadius: 8,
                            fontSize: 12,
                            color: '#f8fafc',
                        }}
                        labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                        itemStyle={{ color: '#f8fafc' }}
                        formatter={v => [`${Number(v).toFixed(1)}%`, 'Mean Score']}
                    />
                    <Line type="monotone" dataKey="mean" stroke="#0f3460" strokeWidth={2.5} dot={{ r: 5, fill: '#0f3460' }} activeDot={{ r: 7 }} name="School Mean" />
                    <Line type="monotone" dataKey="pass_rate" stroke="#10b981" strokeWidth={2} strokeDasharray="4 2" dot={{ r: 4, fill: '#10b981' }} name="Pass Rate %" />
                </LineChart>
            </ResponsiveContainer>
        </div>
    )
}

function EarlyPerformanceCard({ earlyPerformance, summary }) {
    if (!earlyPerformance?.baseline_label || !earlyPerformance?.latest_label) return null
    const delta = earlyPerformance.delta
    return (
        <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
            <div className="flex items-center gap-2 mb-3">
                <Award size={16} className="text-brand-accent" />
                <h3 className="text-sm font-semibold text-gray-700">Early Performance Comparison</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-50 rounded-lg p-3">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide">Baseline</p>
                    <p className="text-sm font-semibold text-gray-700">{earlyPerformance.baseline_label}</p>
                    <p className="text-lg font-bold text-gray-900 mt-1">
                        {earlyPerformance.baseline_mean != null ? `${earlyPerformance.baseline_mean.toFixed(1)}%` : '—'}
                    </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide">Latest</p>
                    <p className="text-sm font-semibold text-gray-700">{earlyPerformance.latest_label}</p>
                    <p className="text-lg font-bold text-gray-900 mt-1">
                        {earlyPerformance.latest_mean != null ? `${earlyPerformance.latest_mean.toFixed(1)}%` : '—'}
                    </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3 flex flex-col justify-between">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wide">Change</p>
                    <div className="mt-1"><TrendBadge delta={delta} trend={earlyPerformance.trend} /></div>
                    {summary && (
                        <p className="text-[11px] text-gray-500 mt-2">
                            Students: {summary.improved} improved, {summary.stable} stable, {summary.declined} declined
                        </p>
                    )}
                </div>
            </div>
        </div>
    )
}

function ExamTimelineChart({ examTimeline }) {
    if (!examTimeline?.length) return null
    return (
        <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
            <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={16} className="text-brand-accent" />
                <h3 className="text-sm font-semibold text-gray-700">Exam-by-Exam Trend (Within Terms)</h3>
            </div>
            <ResponsiveContainer width="100%" height={220}>
                <LineChart data={examTimeline}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#e2e8f0' }} interval={0} angle={-18} textAnchor="end" height={56}>
                        <Label value="Exam Timeline" position="insideBottom" offset={-6} style={{ fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                    </XAxis>
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} domain={['auto', 'auto']} tickFormatter={v => `${v}%`}>
                        <Label value="Score / Pass Rate (%)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                    </YAxis>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#0f172a',
                            border: '1px solid #334155',
                            borderRadius: 8,
                            fontSize: 12,
                            color: '#f8fafc',
                        }}
                        labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                        itemStyle={{ color: '#f8fafc' }}
                        formatter={(v, name) => [`${Number(v).toFixed(1)}%`, name === 'mean' ? 'Mean Score' : name]}
                    />
                    <Line type="monotone" dataKey="mean" stroke="#0f3460" strokeWidth={2.5} dot={{ r: 4, fill: '#0f3460' }} name="Mean Score" />
                    <Line type="monotone" dataKey="pass_rate" stroke="#10b981" strokeWidth={2} strokeDasharray="4 2" dot={{ r: 3, fill: '#10b981' }} name="Pass Rate %" />
                </LineChart>
            </ResponsiveContainer>
        </div>
    )
}

// ── Main Page ─────────────────────────────────────────────────────
export default function TermComparison() {
    const { data } = useData()
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!data) return
        setLoading(true)
        getTermComparison(data)
            .then(setResult)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [data])

    if (loading) return (
        <div className="flex items-center justify-center py-32">
            <Loader2 size={32} className="text-brand-accent animate-spin" />
            <span className="ml-3 text-sm text-gray-500">Comparing terms…</span>
        </div>
    )

    if (error) return (
        <div className="bg-red-50 border border-red-100 rounded-xl p-6 text-sm text-danger">
            <p className="font-medium">Analysis Error</p>
            <p className="mt-1 text-red-600/80">{error}</p>
        </div>
    )

    if (!result || !result.terms?.length) return (
        <div className="bg-amber-50 border border-amber-100 rounded-xl p-6 text-sm text-amber-800">
            <p className="font-medium">No term data found</p>
            <p className="mt-1">Make sure your data includes a <code className="bg-amber-100 px-1 rounded">term</code> column with values like "Term 1", "Term 2", "Term 3".</p>
        </div>
    )

    const {
        terms, school_by_term, subjects_by_term, students_by_term,
        top_improvers, top_decliners, early_performance, exam_timeline, student_delta_summary,
    } = result

    const systemLabel = 'Universal Grading (A-F)'

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Term Comparison</h1>
                    <p className="text-sm text-gray-500 mt-1">
                        Track performance across all 3 terms of the academic calendar
                    </p>
                </div>
                <span className="text-xs bg-brand-accent/10 text-brand-accent font-medium px-3 py-1 rounded-full">
                    {systemLabel}
                </span>
            </div>

            {/* Term summary cards */}
            <TermSummaryCards schoolByTerm={school_by_term} terms={terms} />

            <EarlyPerformanceCard earlyPerformance={early_performance} summary={student_delta_summary} />

            {/* School trend line */}
            <SchoolTrendLine schoolByTerm={school_by_term} />

            <ExamTimelineChart examTimeline={exam_timeline} />

            {/* Subject grouped bar */}
            {subjects_by_term?.length > 0 && (
                <SubjectTermChart subjectsByTerm={subjects_by_term} terms={terms} />
            )}

            {/* Improvers / Decliners */}
            {terms.length >= 2 && (
                <LeaderCards
                    improvers={top_improvers || []}
                    decliners={top_decliners || []}
                    firstTerm={terms[0]}
                    lastTerm={terms[terms.length - 1]}
                />
            )}

            {/* Student table */}
            {students_by_term?.length > 0 && (
                <StudentDeltaTable studentsByTerm={students_by_term} terms={terms} />
            )}
        </div>
    )
}
