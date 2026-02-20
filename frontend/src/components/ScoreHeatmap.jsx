import { useMemo } from 'react'

const HEAT_COLORS = [
    { max: 30, bg: '#fee2e2', text: '#991b1b' },   // deep red
    { max: 40, bg: '#fed7aa', text: '#9a3412' },   // orange
    { max: 50, bg: '#fef08a', text: '#854d0e' },   // yellow
    { max: 60, bg: '#d9f99d', text: '#3f6212' },   // lime
    { max: 70, bg: '#bbf7d0', text: '#166534' },   // light green
    { max: 80, bg: '#86efac', text: '#14532d' },   // green
    { max: 100, bg: '#6ee7b7', text: '#064e3b' },  // emerald
]

function getHeatColor(score) {
    if (score == null || isNaN(score)) return { bg: '#f3f4f6', text: '#9ca3af' }
    for (const c of HEAT_COLORS) {
        if (score <= c.max) return c
    }
    return HEAT_COLORS[HEAT_COLORS.length - 1]
}

export default function ScoreHeatmap({ data, rowLabel = 'Class', colLabel = 'Subject' }) {
    // data: [{ row, col, value }]
    const { rows, cols, matrix } = useMemo(() => {
        const rowSet = [...new Set(data.map(d => d.row))].sort()
        const colSet = [...new Set(data.map(d => d.col))].sort()
        const m = {}
        data.forEach(d => { m[`${d.row}|${d.col}`] = d.value })
        return { rows: rowSet, cols: colSet, matrix: m }
    }, [data])

    if (!data?.length) {
        return (
            <div className="bg-card rounded-xl p-6 text-center text-gray-400 text-sm">
                No heatmap data available
            </div>
        )
    }

    return (
        <div className="bg-card rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="bg-surface-alt">
                            <th className="px-3 py-2 text-left font-semibold text-gray-500 uppercase tracking-wider sticky left-0 bg-surface-alt z-10">
                                {rowLabel}
                            </th>
                            {cols.map(c => (
                                <th key={c} className="px-3 py-2 text-center font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
                                    {c}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {rows.map(r => (
                            <tr key={r} className="hover:bg-gray-50/50 transition-colors">
                                <td className="px-3 py-2 font-medium text-gray-700 sticky left-0 bg-card z-10 whitespace-nowrap">
                                    {r}
                                </td>
                                {cols.map(c => {
                                    const val = matrix[`${r}|${c}`]
                                    const color = getHeatColor(val)
                                    return (
                                        <td key={c} className="px-1 py-1 text-center">
                                            <div
                                                className="mx-auto w-14 py-1.5 rounded-md font-bold text-xs transition-transform hover:scale-110"
                                                style={{ backgroundColor: color.bg, color: color.text }}
                                                title={`${r} — ${c}: ${val != null ? val.toFixed(1) : 'N/A'}`}
                                            >
                                                {val != null ? val.toFixed(1) : '—'}
                                            </div>
                                        </td>
                                    )
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {/* Legend */}
            <div className="flex items-center justify-center gap-1 px-4 py-2 border-t border-gray-100">
                <span className="text-[10px] text-gray-400 mr-1">Low</span>
                {HEAT_COLORS.map((c, i) => (
                    <div
                        key={i}
                        className="w-6 h-3 rounded-sm"
                        style={{ backgroundColor: c.bg }}
                        title={`≤ ${c.max}%`}
                    />
                ))}
                <span className="text-[10px] text-gray-400 ml-1">High</span>
            </div>
        </div>
    )
}
