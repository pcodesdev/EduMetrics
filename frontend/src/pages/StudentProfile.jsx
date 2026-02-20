import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useData } from '../App'
import { getStudentProfile } from '../api'
import RiskBadge from '../components/RiskBadge'
import {
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Label,
} from 'recharts'
import { Loader2, ArrowLeft, User, Award, TrendingUp, BookOpen } from 'lucide-react'

export default function StudentProfile() {
    const { id } = useParams()
    const navigate = useNavigate()
    const { data } = useData()
    const [profile, setProfile] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!data || !id) return
        setLoading(true)
        getStudentProfile(decodeURIComponent(id), data)
            .then(p => setProfile(p))
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [data, id])

    if (loading) {
        return (
            <div className="flex items-center justify-center py-32">
                <Loader2 size={32} className="text-brand-accent animate-spin" />
                <span className="ml-3 text-sm text-gray-500">Loading profile…</span>
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

    if (!profile) {
        return (
            <div className="text-center py-16 text-gray-400">
                <p>Student not found.</p>
                <button onClick={() => navigate(-1)} className="mt-2 text-brand-accent underline text-sm">Go back</button>
            </div>
        )
    }

    // subject_scores is an array: [{subject, score}, ...]
    const radarData = Array.isArray(profile.subject_scores)
        ? profile.subject_scores.map(s => ({
            subject: s.subject,
            score: Number(s.score) || 0,
            fullMark: 100,
        }))
        : []

    // term_trends: [{term, mean, ...}, ...]
    const trendData = profile.term_trends || profile.trend || profile.term_scores || []

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Back button */}
            <button
                onClick={() => navigate(-1)}
                className="flex items-center gap-2 text-sm text-gray-500 hover:text-brand-accent transition-colors"
            >
                <ArrowLeft size={16} /> Back
            </button>

            {/* Header Card */}
            <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-start justify-between flex-wrap gap-4">
                    <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-brand-accent/10 flex items-center justify-center">
                            <User size={24} className="text-brand-accent" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">
                                {profile.name || profile.student_name || id}
                            </h1>
                            <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                                {profile.student_id && <span>ID: {profile.student_id}</span>}
                                {profile.class && <span>Class: {profile.class}</span>}
                                {profile.gender && <span>Gender: {profile.gender}</span>}
                            </div>
                        </div>
                    </div>
                    <RiskBadge level={profile.risk_level || 'none'} />
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-card rounded-xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-info/10 flex items-center justify-center">
                            <TrendingUp size={18} className="text-info" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-400">Average Score</p>
                            <p className="text-xl font-bold text-gray-900">
                                {profile.overall_mean != null ? `${Number(profile.overall_mean).toFixed(1)}%` : '—'}
                            </p>
                        </div>
                    </div>
                </div>
                <div className="bg-card rounded-xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-warning/10 flex items-center justify-center">
                            <Award size={18} className="text-warning" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-400">Rank in Class</p>
                            <p className="text-xl font-bold text-gray-900">
                                {profile.class_rank != null ? `#${profile.class_rank}` : '—'}
                                {profile.class_total && <span className="text-xs text-gray-400 font-normal"> / {profile.class_total}</span>}
                            </p>
                        </div>
                    </div>
                </div>
                <div className="bg-card rounded-xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
                            <BookOpen size={18} className="text-success" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-400">School Rank</p>
                            <p className="text-xl font-bold text-gray-900">
                                {profile.school_rank != null ? `#${profile.school_rank}` : '—'}
                                {profile.school_total && <span className="text-xs text-gray-400 font-normal"> / {profile.school_total}</span>}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Radar Chart */}
                {radarData.length > 0 && (
                    <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5">
                        <h3 className="text-sm font-semibold text-gray-700 mb-4">Subject Profile</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <RadarChart data={radarData}>
                                <PolarGrid stroke="#e2e8f0" />
                                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: '#64748b' }} />
                                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9, fill: '#94a3b8' }} />
                                <Radar
                                    name="Score"
                                    dataKey="score"
                                    stroke="#0f3460"
                                    fill="#0f3460"
                                    fillOpacity={0.15}
                                    strokeWidth={2}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 12, color: '#f8fafc' }}
                                    labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                                    itemStyle={{ color: '#f8fafc' }}
                                    formatter={v => [`${Number(v).toFixed(1)}%`]}
                                />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Trend Line Chart */}
                {trendData.length > 0 && (
                    <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5">
                        <h3 className="text-sm font-semibold text-gray-700 mb-4">Score Trend</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={trendData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                <XAxis
                                    dataKey="term"
                                    tick={{ fontSize: 11, fill: '#64748b' }}
                                    tickLine={false}
                                    axisLine={{ stroke: '#e2e8f0' }}
                                >
                                    <Label value="Terms" position="insideBottom" offset={-2} style={{ fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                                </XAxis>
                                <YAxis
                                    tick={{ fontSize: 11, fill: '#64748b' }}
                                    tickLine={false}
                                    axisLine={false}
                                    domain={[0, 100]}
                                    tickFormatter={v => `${v}%`}
                                >
                                    <Label value="Mean Score (%)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                                </YAxis>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 12, color: '#f8fafc' }}
                                    labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                                    itemStyle={{ color: '#f8fafc' }}
                                    formatter={v => [`${Number(v).toFixed(1)}%`]}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="mean"
                                    stroke="#e94560"
                                    strokeWidth={2.5}
                                    dot={{ fill: '#e94560', r: 4, strokeWidth: 2, stroke: '#fff' }}
                                    activeDot={{ r: 6, strokeWidth: 0 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>

            {/* Subject Scores Table */}
            {radarData.length > 0 && (
                <div className="bg-card rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="px-5 py-3 bg-surface-alt border-b border-gray-100">
                        <h3 className="text-sm font-semibold text-gray-700">Subject Scores</h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-100">
                                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Subject</th>
                                    <th className="px-4 py-2 text-right text-xs font-semibold text-gray-500 uppercase">Score</th>
                                    <th className="px-4 py-2 text-center text-xs font-semibold text-gray-500 uppercase">Status</th>
                                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Performance</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {radarData.map(({ subject, score }) => (
                                    <tr key={subject} className="hover:bg-surface-alt transition-colors">
                                        <td className="px-4 py-3 font-medium text-gray-700">{subject}</td>
                                        <td className={`px-4 py-3 text-right font-bold ${score >= 70 ? 'text-success' : score >= 50 ? 'text-warning' : 'text-danger'}`}>
                                            {Number(score).toFixed(1)}%
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <span className={`inline-block w-2 h-2 rounded-full ${score >= 50 ? 'bg-success' : 'bg-danger'}`} />
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-2">
                                                <div className="flex-1 bg-gray-100 rounded-full h-2 max-w-[150px]">
                                                    <div
                                                        className={`h-2 rounded-full transition-all duration-500 ${score >= 70 ? 'bg-success' : score >= 50 ? 'bg-warning' : 'bg-danger'}`}
                                                        style={{ width: `${Math.min(score, 100)}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
