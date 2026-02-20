import { useState, useEffect, useMemo } from 'react'
import { useData } from '../App'
import { getSubjects } from '../api'
import ScoreHeatmap from '../components/ScoreHeatmap'
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, Label,
} from 'recharts'
import { Loader2, BookOpen, TrendingUp, TrendingDown, Minus } from 'lucide-react'

const PALETTE = ['#0f3460', '#e94560', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22']

export default function SubjectAnalysis() {
    const { data } = useData()
    const [subjects, setSubjects] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!data) return
        setLoading(true)
        getSubjects(data)
            .then(s => setSubjects(s))
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [data])

    const subjectList = useMemo(() => {
        if (!subjects?.subjects) return []
        if (Array.isArray(subjects.subjects)) {
            return subjects.subjects.map((s) => ({
                ...s,
                name: s.subject || s.name || 'Unknown Subject',
            }))
        }
        return Object.entries(subjects.subjects).map(([name, stats]) => ({ name, ...stats }))
    }, [subjects])

    const passRateData = useMemo(() =>
        subjectList.map(s => ({ name: s.name, pass_rate: s.pass_rate ?? 0 })),
        [subjectList]
    )

    // Heatmap data: class × subject
    const heatmapData = useMemo(() => {
        if (!subjects?.class_subject_means) return []
        const result = []
        for (const [cls, subs] of Object.entries(subjects.class_subject_means)) {
            for (const [sub, val] of Object.entries(subs)) {
                result.push({ row: cls, col: sub, value: val })
            }
        }
        return result
    }, [subjects])

    if (loading) {
        return (
            <div className="flex items-center justify-center py-32">
                <Loader2 size={32} className="text-brand-accent animate-spin" />
                <span className="ml-3 text-sm text-gray-500">Analysing subjects…</span>
            </div>
        )
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-100 rounded-xl p-6 text-sm text-danger">
                <p className="font-medium">Error</p><p className="mt-1">{error}</p>
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Subject Analysis</h1>
                <p className="text-sm text-gray-500 mt-1">Deep dive into individual subject performance</p>
            </div>

            {/* Subject Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {subjectList.map((s, i) => {
                    const TrendIcon = (s.mean ?? 0) >= 60 ? TrendingUp : (s.mean ?? 0) >= 50 ? Minus : TrendingDown
                    const trendColor = (s.mean ?? 0) >= 60 ? 'text-success' : (s.mean ?? 0) >= 50 ? 'text-warning' : 'text-danger'
                    return (
                        <div key={s.name} className="bg-card rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                                        style={{ backgroundColor: `${PALETTE[i % PALETTE.length]}15` }}>
                                        <BookOpen size={14} style={{ color: PALETTE[i % PALETTE.length] }} />
                                    </div>
                                    <h3 className="text-sm font-semibold text-gray-800">{s.name}</h3>
                                </div>
                                <TrendIcon size={16} className={trendColor} />
                            </div>
                            <div className="space-y-2">
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Mean</span>
                                    <span className="font-bold text-gray-800">{(s.mean ?? 0).toFixed(1)}%</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Median</span>
                                    <span className="font-medium text-gray-600">{(s.median ?? 0).toFixed(1)}%</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Std Dev</span>
                                    <span className="font-medium text-gray-600">{(s.std ?? 0).toFixed(1)}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Pass Rate</span>
                                    <span className={`font-bold ${(s.pass_rate ?? 0) >= 60 ? 'text-success' : (s.pass_rate ?? 0) >= 50 ? 'text-warning' : 'text-danger'}`}>
                                        {(s.pass_rate ?? 0).toFixed(1)}%
                                    </span>
                                </div>
                                {/* Mini progress bar */}
                                <div className="w-full bg-gray-100 rounded-full h-1.5 mt-1">
                                    <div
                                        className={`h-1.5 rounded-full ${(s.pass_rate ?? 0) >= 60 ? 'bg-success' : (s.pass_rate ?? 0) >= 50 ? 'bg-warning' : 'bg-danger'}`}
                                        style={{ width: `${Math.min(s.pass_rate ?? 0, 100)}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Pass Rate Bar Chart */}
            {passRateData.length > 0 && (
                <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5">
                    <h3 className="text-sm font-semibold text-gray-700 mb-4">Pass Rate by Subject</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={passRateData} barCategoryGap="20%">
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis
                                dataKey="name"
                                interval={0}
                                angle={-28}
                                textAnchor="end"
                                height={80}
                                tick={{ fontSize: 11, fill: '#64748b' }}
                                tickLine={false}
                                axisLine={{ stroke: '#e2e8f0' }}
                            >
                                <Label value="Subjects" position="insideBottom" offset={-2} fill="#334155" />
                            </XAxis>
                            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} domain={[0, 100]}
                                tickFormatter={v => `${v}%`}>
                                <Label value="Pass Rate (%)" angle={-90} position="insideLeft" offset={2} fill="#334155" />
                            </YAxis>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 12, color: '#f8fafc' }}
                                labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                                itemStyle={{ color: '#f8fafc' }}
                                formatter={v => [`${Number(v).toFixed(1)}%`]}
                            />
                            <Bar dataKey="pass_rate" name="Pass Rate" radius={[6, 6, 0, 0]} maxBarSize={50}>
                                {passRateData.map((_, i) => (
                                    <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Heatmap */}
            {heatmapData.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Class × Subject Heatmap</h3>
                    <ScoreHeatmap data={heatmapData} rowLabel="Class" colLabel="Subject" />
                </div>
            )}
        </div>
    )
}
