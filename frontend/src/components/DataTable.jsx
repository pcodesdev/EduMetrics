import { useState, useMemo } from 'react'
import { Search, ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from 'lucide-react'

export default function DataTable({
    columns,       // [{ key, label, sortable?, render?(value, row) }]
    data = [],
    pageSize = 15,
    searchable = true,
    onRowClick,
    emptyMessage = 'No data available',
    className = '',
}) {
    const [query, setQuery] = useState('')
    const [sortKey, setSortKey] = useState(null)
    const [sortDir, setSortDir] = useState('asc')
    const [page, setPage] = useState(0)

    // Filter
    const filtered = useMemo(() => {
        if (!query.trim()) return data
        const q = query.toLowerCase()
        return data.filter(row =>
            columns.some(col => String(row[col.key] ?? '').toLowerCase().includes(q))
        )
    }, [data, query, columns])

    // Sort
    const sorted = useMemo(() => {
        if (!sortKey) return filtered
        return [...filtered].sort((a, b) => {
            const av = a[sortKey] ?? ''
            const bv = b[sortKey] ?? ''
            if (typeof av === 'number' && typeof bv === 'number') {
                return sortDir === 'asc' ? av - bv : bv - av
            }
            return sortDir === 'asc'
                ? String(av).localeCompare(String(bv))
                : String(bv).localeCompare(String(av))
        })
    }, [filtered, sortKey, sortDir])

    // Paginate
    const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
    const safePage = Math.min(page, totalPages - 1)
    const paged = sorted.slice(safePage * pageSize, (safePage + 1) * pageSize)

    const handleSort = key => {
        if (sortKey === key) {
            setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
        } else {
            setSortKey(key)
            setSortDir('asc')
        }
        setPage(0)
    }

    const SortIcon = ({ col }) => {
        if (!col.sortable) return null
        if (sortKey !== col.key) return <ChevronsUpDown size={14} className="text-gray-300" />
        return sortDir === 'asc'
            ? <ChevronUp size={14} className="text-brand-accent" />
            : <ChevronDown size={14} className="text-brand-accent" />
    }

    return (
        <div className={`bg-card rounded-xl shadow-sm border border-gray-100 overflow-hidden ${className}`}>
            {/* Search bar */}
            {searchable && (
                <div className="px-4 pt-4 pb-2">
                    <div className="relative max-w-xs">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search…"
                            value={query}
                            onChange={e => { setQuery(e.target.value); setPage(0) }}
                            className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-gray-200 
                                       focus:outline-none focus:ring-2 focus:ring-brand-accent/30 focus:border-brand-accent
                                       transition-all placeholder:text-gray-400"
                        />
                    </div>
                </div>
            )}

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-gray-100 bg-surface-alt">
                            {columns.map(col => (
                                <th
                                    key={col.key}
                                    onClick={() => col.sortable && handleSort(col.key)}
                                    className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider
                                                ${col.sortable ? 'cursor-pointer select-none hover:text-gray-700' : ''}`}
                                >
                                    <span className="inline-flex items-center gap-1">
                                        {col.label}
                                        <SortIcon col={col} />
                                    </span>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {paged.length === 0 ? (
                            <tr>
                                <td colSpan={columns.length} className="px-4 py-12 text-center text-gray-400">
                                    {emptyMessage}
                                </td>
                            </tr>
                        ) : (
                            paged.map((row, i) => (
                                <tr
                                    key={i}
                                    onClick={() => onRowClick?.(row)}
                                    className={`hover:bg-surface-alt transition-colors duration-150
                                                ${onRowClick ? 'cursor-pointer' : ''}`}
                                >
                                    {columns.map(col => (
                                        <td key={col.key} className="px-4 py-3 text-gray-700 whitespace-nowrap">
                                            {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '—')}
                                        </td>
                                    ))}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            {sorted.length > pageSize && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 text-xs text-gray-500">
                    <span>
                        Showing {safePage * pageSize + 1}–{Math.min((safePage + 1) * pageSize, sorted.length)} of {sorted.length}
                    </span>
                    <div className="flex items-center gap-1">
                        <button
                            onClick={() => setPage(p => Math.max(0, p - 1))}
                            disabled={safePage === 0}
                            className="p-1.5 rounded-md hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                            <ChevronLeft size={14} />
                        </button>
                        {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                            let pageNum = i
                            if (totalPages > 5) {
                                const start = Math.min(Math.max(safePage - 2, 0), totalPages - 5)
                                pageNum = start + i
                            }
                            return (
                                <button
                                    key={pageNum}
                                    onClick={() => setPage(pageNum)}
                                    className={`w-7 h-7 rounded-md text-xs font-medium transition-colors
                                                ${safePage === pageNum
                                            ? 'bg-brand-accent text-white'
                                            : 'hover:bg-gray-100 text-gray-600'}`}
                                >
                                    {pageNum + 1}
                                </button>
                            )
                        })}
                        <button
                            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                            disabled={safePage >= totalPages - 1}
                            className="p-1.5 rounded-md hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                            <ChevronRight size={14} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
