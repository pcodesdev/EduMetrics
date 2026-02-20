import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useData } from '../App'
import { getRisk } from '../api'
import DataTable from '../components/DataTable'
import RiskBadge from '../components/RiskBadge'
import { AlertTriangle, Loader2, ChevronDown, ChevronRight } from 'lucide-react'

export default function AtRisk() {
    const { data } = useData()
    const navigate = useNavigate()
    const [riskData, setRiskData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [expandedId, setExpandedId] = useState(null)

    useEffect(() => {
        if (!data) return
        setLoading(true)
        getRisk(data)
            .then(r => setRiskData(r))
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [data])

    if (loading) {
        return (
            <div className="flex items-center justify-center py-32">
                <Loader2 size={32} className="text-brand-accent animate-spin" />
                <span className="ml-3 text-sm text-gray-500">Analysing risk factors…</span>
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

    // Backend returns { students: [...], summary: { total, high_risk, medium_risk, low_risk } }
    const students = riskData?.students || riskData?.at_risk_students || []
    const summary = riskData?.summary || {}

    const columns = [
        {
            key: 'expand', label: '', sortable: false,
            render: (_, row) => {
                const id = row.student_id || row.name
                return (
                    <button
                        onClick={e => { e.stopPropagation(); setExpandedId(expandedId === id ? null : id) }}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        {expandedId === id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </button>
                )
            }
        },
        // Backend field is `name` (not `student_name`)
        { key: 'name', label: 'Name', sortable: true, render: v => <span className="font-medium">{v || '—'}</span> },
        { key: 'student_id', label: 'ID', sortable: true },
        { key: 'class', label: 'Class', sortable: true },
        {
            // Backend field is `overall_mean` (not `average`)
            key: 'overall_mean', label: 'Avg Score', sortable: true,
            render: v => v != null ? (
                <span className={`font-semibold ${v < 50 ? 'text-danger' : v < 70 ? 'text-warning' : 'text-success'}`}>
                    {Number(v).toFixed(1)}%
                </span>
            ) : '—'
        },
        {
            key: 'risk_score', label: 'Risk Score', sortable: true,
            render: v => v != null ? <span className="font-mono text-xs">{Number(v).toFixed(1)}</span> : '—'
        },
        {
            key: 'risk_level', label: 'Risk Level', sortable: true,
            render: v => <RiskBadge level={v} size="sm" />
        },
    ]

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">At-Risk Students</h1>
                <p className="text-sm text-gray-500 mt-1">Students identified as needing additional support</p>
            </div>

            {/* Summary Cards — backend uses high_risk / medium_risk / low_risk */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                    { label: 'High Risk', count: summary.high_risk ?? students.filter(s => (s.risk_level || '').toLowerCase() === 'high').length, color: 'danger' },
                    { label: 'Medium Risk', count: summary.medium_risk ?? students.filter(s => (s.risk_level || '').toLowerCase() === 'medium').length, color: 'warning' },
                    { label: 'Low Risk', count: summary.low_risk ?? students.filter(s => (s.risk_level || '').toLowerCase() === 'low').length, color: 'success' },
                ].map(({ label, count, color }) => (
                    <div key={label} className="bg-card rounded-xl p-5 shadow-sm border border-gray-100">
                        <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-lg bg-${color}/10 flex items-center justify-center`}>
                                <AlertTriangle size={18} className={`text-${color}`} />
                            </div>
                            <div>
                                <p className="text-xs font-medium text-gray-400 uppercase">{label}</p>
                                <p className="text-xl font-bold text-gray-900">{count}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Table */}
            <DataTable
                columns={columns}
                data={students}
                pageSize={20}
                searchable
                onRowClick={row => {
                    const id = row.student_id || row.name
                    navigate(`/student/${encodeURIComponent(id)}`)
                }}
                emptyMessage="No at-risk students detected 🎉"
            />

            {/* Expanded Recommendations */}
            {expandedId && (() => {
                const student = students.find(s => (s.student_id || s.name) === expandedId)
                if (!student) return null
                // Backend returns `recommendation` (string) and `factors` (array)
                const recommendation = student.recommendation
                const factors = student.factors || []
                return (
                    <div className="bg-surface-alt rounded-xl p-5 border border-gray-100 animate-slide-in">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">
                            Recommendations for {student.name || expandedId}
                        </h4>
                        {recommendation && (
                            <p className="text-xs text-gray-600 mb-3">{recommendation}</p>
                        )}
                        {factors.filter(f => f.triggered).length > 0 && (
                            <div>
                                <p className="text-xs font-medium text-gray-500 mb-1">Triggered Risk Factors:</p>
                                <ul className="space-y-1 text-xs text-gray-600">
                                    {factors.filter(f => f.triggered).map((f, i) => (
                                        <li key={i} className="flex items-start gap-2">
                                            <span className="mt-1 w-1.5 h-1.5 rounded-full bg-brand-accent shrink-0" />
                                            <span><strong>{f.factor}</strong> — {f.detail}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {!recommendation && factors.filter(f => f.triggered).length === 0 && (
                            <p className="text-xs text-gray-400">No specific recommendations available.</p>
                        )}
                    </div>
                )
            })()}
        </div>
    )
}
