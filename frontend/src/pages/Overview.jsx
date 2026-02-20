import { useState, useEffect } from 'react'
import { useData } from '../App'
import { getOverview, getSubjects, getInsights } from '../api'
import InsightCard from '../components/InsightCard'
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
    PieChart, Pie, Legend, Label,
} from 'recharts'
import {
    Users, TrendingUp, Award, AlertTriangle, Loader2, BookOpen, Target,
} from 'lucide-react'

const PALETTE = ['#0f3460', '#e94560', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22']

function KpiCard({ icon: Icon, label, value, sub, accent = 'brand-accent' }) {
    return (
        <div className="bg-card rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all duration-200 animate-fade-in">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">{label}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
                    {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
                </div>
                <div className={`w-10 h-10 rounded-lg bg-${accent}/10 flex items-center justify-center`}>
                    <Icon size={20} className={`text-${accent}`} />
                </div>
            </div>
        </div>
    )
}

export default function Overview() {
    const { data } = useData()
    const [overview, setOverview] = useState(null)
    const [subjects, setSubjects] = useState(null)
    const [insights, setInsights] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!data) return
        setLoading(true)
        Promise.all([
            getOverview(data),
            getSubjects(data),
            getInsights(data),
        ])
            .then(([ov, subj, ins]) => {
                setOverview(ov)
                setSubjects(subj)
                setInsights(ins)
            })
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [data])

    if (loading) {
        return (
            <div className="flex items-center justify-center py-32">
                <Loader2 size={32} className="text-brand-accent animate-spin" />
                <span className="ml-3 text-sm text-gray-500">Crunching numbers…</span>
            </div>
        )
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-100 rounded-xl p-6 text-sm text-danger">
                <p className="font-medium">Analysis Error</p>
                <p className="mt-1 text-red-600/80">{error}</p>
            </div>
        )
    }

    // subjects.subjects is an array of {subject, mean, pass_rate, ...}
    const subjectList = Array.isArray(subjects?.subjects)
        ? subjects.subjects
        : []
    const subjectChartData = subjectList.map(s => ({
        name: s.subject,
        mean: s.mean ?? 0,
        pass_rate: s.pass_rate ?? 0,
    }))

    // overview.distribution = { bins: [...], counts: [...] }
    const dist = overview?.distribution
    const distributionData = dist
        ? dist.bins.map((bin, i) => ({ range: bin, count: dist.counts[i] ?? 0 }))
        : []

    const passFailData = overview ? [
        { name: 'Pass', value: overview.pass_count ?? 0, color: '#2ecc71' },
        { name: 'Fail', value: overview.fail_count ?? 0, color: '#e74c3c' },
    ] : []

    // at_risk is derived from risk summary (high + medium), surfaced via insights
    const highRisk = insights?.summary?.by_severity?.critical ?? null
    const atRiskDisplay = highRisk != null ? highRisk : '—'

    const insightsList = insights?.insights || insights?.all_insights || []

    // School mean/median from overview
    const schoolMean = overview?.overall_mean
    const schoolMedian = overview?.overall_median

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
                <p className="text-sm text-gray-500 mt-1">
                    Performance snapshot across all students and subjects
                </p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <KpiCard
                    icon={Users} label="Total Students"
                    value={overview?.total_students ?? '—'}
                    sub={`${overview?.total_records ?? '—'} records`}
                />
                <KpiCard
                    icon={TrendingUp} label="School Mean"
                    value={schoolMean != null ? `${schoolMean.toFixed(1)}%` : '—'}
                    sub={`Median: ${schoolMedian != null ? schoolMedian.toFixed(1) : '—'}%`}
                    accent="info"
                />
                <KpiCard
                    icon={Award} label="Pass Rate"
                    value={overview?.pass_rate != null ? `${overview.pass_rate.toFixed(1)}%` : '—'}
                    sub={`${overview?.pass_count ?? 0} passed / ${overview?.fail_count ?? 0} failed`}
                    accent="success"
                />
                <KpiCard
                    icon={AlertTriangle} label="Critical Insights"
                    value={atRiskDisplay}
                    sub="Flagged for attention"
                    accent="brand-highlight"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Subject Performance Bar Chart */}
                <div className="lg:col-span-2 bg-card rounded-xl shadow-sm border border-gray-100 p-5">
                    <div className="flex items-center gap-2 mb-4">
                        <BookOpen size={16} className="text-brand-accent" />
                        <h3 className="text-sm font-semibold text-gray-700">Subject Performance</h3>
                    </div>
                    {subjectChartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={subjectChartData} barCategoryGap="20%">
                                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#e2e8f0' }}>
                                    <Label value="Subjects" position="insideBottom" offset={-2} style={{ fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                                </XAxis>
                                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} domain={[0, 100]}
                                    tickFormatter={v => `${v}%`}>
                                    <Label value="Mean Score (%)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                                </YAxis>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 8,
                                        fontSize: 12, color: '#f8fafc',
                                    }}
                                    labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                                    itemStyle={{ color: '#f8fafc' }}
                                    formatter={(v) => [`${Number(v).toFixed(1)}%`]}
                                    cursor={{ fill: 'rgba(15,52,96,0.06)' }}
                                />
                                <Bar dataKey="mean" name="Mean Score" radius={[6, 6, 0, 0]} maxBarSize={50}>
                                    {subjectChartData.map((_, i) => (
                                        <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <p className="text-center text-gray-400 py-12 text-sm">No subject data</p>
                    )}
                </div>

                {/* Pass / Fail Pie */}
                <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5">
                    <div className="flex items-center gap-2 mb-4">
                        <Target size={16} className="text-brand-accent" />
                        <h3 className="text-sm font-semibold text-gray-700">Pass / Fail</h3>
                    </div>
                    {passFailData.some(d => d.value > 0) ? (
                        <ResponsiveContainer width="100%" height={260}>
                            <PieChart>
                                <Pie
                                    data={passFailData}
                                    dataKey="value"
                                    nameKey="name"
                                    cx="50%" cy="50%"
                                    innerRadius={55} outerRadius={85}
                                    paddingAngle={4}
                                    strokeWidth={0}
                                >
                                    {passFailData.map((d, i) => (
                                        <Cell key={i} fill={d.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 12, color: '#f8fafc' }}
                                    labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                                    itemStyle={{ color: '#f8fafc' }}
                                />
                                <Legend wrapperStyle={{ fontSize: 12 }} />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <p className="text-center text-gray-400 py-12 text-sm">No data</p>
                    )}
                </div>
            </div>

            {/* Score Distribution */}
            {distributionData.length > 0 && (
                <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5">
                    <h3 className="text-sm font-semibold text-gray-700 mb-4">Score Distribution</h3>
                    <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={distributionData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis dataKey="range" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#e2e8f0' }}>
                                <Label value="Score Range (%)" position="insideBottom" offset={-2} style={{ fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                            </XAxis>
                            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false}>
                                <Label value="Students" angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                            </YAxis>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 12, color: '#f8fafc' }}
                                labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                                itemStyle={{ color: '#f8fafc' }}
                            />
                            <Bar dataKey="count" name="Students" fill="#0f3460" radius={[4, 4, 0, 0]} maxBarSize={45} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Top Insights */}
            {insightsList.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Key Insights</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {insightsList.slice(0, 6).map((ins, i) => (
                            <InsightCard
                                key={i}
                                title={ins.title || ins.message || `Insight ${i + 1}`}
                                description={ins.narrative || ins.description || ins.detail || ins.message || ''}
                                severity={ins.severity || ins.level || 'info'}
                                category={ins.category}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
