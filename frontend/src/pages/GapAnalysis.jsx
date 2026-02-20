import { useState, useEffect, useMemo } from 'react'
import { useData } from '../App'
import { getGaps } from '../api'
import GapChart from '../components/GapChart'
import { Loader2, BarChart3 } from 'lucide-react'

const TABS = [
    { key: 'gender', label: 'Gender' },
    { key: 'class', label: 'Class' },
    { key: 'region', label: 'Region' },
    { key: 'term', label: 'Term' },
]

export default function GapAnalysis() {
    const { data } = useData()
    const [gapData, setGapData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [tab, setTab] = useState('gender')

    useEffect(() => {
        if (!data) return
        setLoading(true)
        getGaps(data)
            .then(r => setGapData(r))
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [data])

    // Transform gap data for charts — maps backend shape to { group, mean, pass_rate, count }
    const chartData = useMemo(() => {
        if (!gapData) return { gender: [], class: [], region: [], term: [] }

        // ── Gender: backend returns array of { label, male_mean, female_mean, gap, ... }
        const genderGaps = gapData.gender_gaps || []
        const gender = genderGaps.map(g => ({
            group: g.label,
            male_mean: g.male_mean ?? 0,
            female_mean: g.female_mean ?? 0,
            mean: ((g.male_mean ?? 0) + (g.female_mean ?? 0)) / 2,
            gap: Math.abs(g.gap ?? 0),
            significant: g.statistically_significant,
            direction: g.direction,
        }))

        // ── Class: backend returns array of one object with class_means: [{class, mean}, ...]
        const classGaps = gapData.class_gaps || []
        let classData = []
        if (classGaps.length > 0 && Array.isArray(classGaps[0].class_means)) {
            classData = classGaps[0].class_means.map(c => ({
                group: c.class,
                mean: c.mean ?? 0,
                pass_rate: 0,
                count: 0,
            }))
        }

        // ── Region: same pattern as class
        const regionGaps = gapData.regional_gaps || []
        let regionData = []
        if (regionGaps.length > 0 && Array.isArray(regionGaps[0].region_means)) {
            regionData = regionGaps[0].region_means.map(r => ({
                group: r.region,
                mean: r.mean ?? 0,
                pass_rate: 0,
                count: 0,
            }))
        }

        // ── Term: backend returns array of one object with term_means: [{term, mean}, ...]
        const termGaps = gapData.term_gaps || []
        let termData = []
        if (termGaps.length > 0 && Array.isArray(termGaps[0].term_means)) {
            termData = termGaps[0].term_means.map(t => ({
                group: t.term,
                mean: t.mean ?? 0,
                pass_rate: 0,
                count: 0,
            }))
        }

        return { gender, class: classData, region: regionData, term: termData }
    }, [gapData])

    if (loading) {
        return (
            <div className="flex items-center justify-center py-32">
                <Loader2 size={32} className="text-brand-accent animate-spin" />
                <span className="ml-3 text-sm text-gray-500">Analysing gaps…</span>
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

    const current = chartData[tab] || []

    // Gender tab has male_mean/female_mean — other tabs have plain mean
    const genderBars = [
        { key: 'male_mean', label: 'Boys Mean', color: '#3498db' },
        { key: 'female_mean', label: 'Girls Mean', color: '#e94560' },
    ]
    const defaultBars = [
        { key: 'mean', label: 'Mean Score', color: '#0f3460' },
    ]

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Gap Analysis</h1>
                <p className="text-sm text-gray-500 mt-1">
                    Identify performance disparities across demographic and organisational dimensions
                </p>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 bg-surface-alt rounded-xl p-1 w-fit">
                {TABS.map(t => (
                    <button
                        key={t.key}
                        onClick={() => setTab(t.key)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
                            ${tab === t.key
                                ? 'bg-card text-brand-accent shadow-sm'
                                : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            {current.length > 0 ? (
                <>
                    {/* Chart — gender shows male vs female bars; others show mean */}
                    <GapChart
                        data={current}
                        title={`${tab === 'gender' ? 'Boys vs Girls' : 'Mean Score'} by ${tab.charAt(0).toUpperCase() + tab.slice(1)}`}
                        xKey="group"
                        bars={tab === 'gender' ? genderBars : defaultBars}
                        height={350}
                    />

                    {/* Summary Table */}
                    <div className="bg-card rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="px-5 py-3 bg-surface-alt border-b border-gray-100">
                            <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                                <BarChart3 size={14} />
                                Detailed Breakdown
                            </h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-gray-100 bg-surface-alt/50">
                                        <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Group</th>
                                        {tab === 'gender' ? (
                                            <>
                                                <th className="px-4 py-2 text-right text-xs font-semibold text-gray-500 uppercase">Boys</th>
                                                <th className="px-4 py-2 text-right text-xs font-semibold text-gray-500 uppercase">Girls</th>
                                                <th className="px-4 py-2 text-right text-xs font-semibold text-gray-500 uppercase">Gap</th>
                                                <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Significant</th>
                                            </>
                                        ) : (
                                            <>
                                                <th className="px-4 py-2 text-right text-xs font-semibold text-gray-500 uppercase">Mean</th>
                                                <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Gap vs Best</th>
                                            </>
                                        )}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50">
                                    {tab === 'gender' ? (
                                        current.map((row, i) => (
                                            <tr key={i} className="hover:bg-surface-alt transition-colors">
                                                <td className="px-4 py-3 font-medium text-gray-700">{row.group}</td>
                                                <td className="px-4 py-3 text-right font-semibold text-blue-600">{(row.male_mean ?? 0).toFixed(1)}%</td>
                                                <td className="px-4 py-3 text-right font-semibold text-pink-600">{(row.female_mean ?? 0).toFixed(1)}%</td>
                                                <td className={`px-4 py-3 text-right font-semibold ${row.gap > 10 ? 'text-danger' : row.gap > 5 ? 'text-warning' : 'text-gray-600'}`}>
                                                    {(row.gap ?? 0).toFixed(1)}pp
                                                </td>
                                                <td className="px-4 py-3">
                                                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${row.significant ? 'bg-danger/10 text-danger' : 'bg-gray-100 text-gray-500'}`}>
                                                        {row.significant ? 'Yes' : 'No'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (() => {
                                        const maxMean = Math.max(...current.map(d => d.mean || 0))
                                        return current.map((row, i) => {
                                            const gap = maxMean - (row.mean || 0)
                                            return (
                                                <tr key={i} className="hover:bg-surface-alt transition-colors">
                                                    <td className="px-4 py-3 font-medium text-gray-700">{row.group}</td>
                                                    <td className="px-4 py-3 text-right font-semibold text-gray-800">
                                                        {(row.mean ?? 0).toFixed(1)}%
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <div className="flex items-center gap-2">
                                                            <div className="flex-1 bg-gray-100 rounded-full h-2 max-w-[120px]">
                                                                <div
                                                                    className={`h-2 rounded-full ${gap > 10 ? 'bg-danger' : gap > 5 ? 'bg-warning' : 'bg-success'}`}
                                                                    style={{ width: `${maxMean > 0 ? Math.min((gap / maxMean) * 100, 100) : 0}%` }}
                                                                />
                                                            </div>
                                                            <span className="text-xs text-gray-500">{gap.toFixed(1)}pp</span>
                                                        </div>
                                                    </td>
                                                </tr>
                                            )
                                        })
                                    })()}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            ) : (
                <div className="bg-card rounded-xl shadow-sm p-12 text-center text-gray-400 text-sm">
                    No {tab} gap data available. Ensure your dataset includes a <strong>{tab}</strong> column.
                </div>
            )}
        </div>
    )
}
