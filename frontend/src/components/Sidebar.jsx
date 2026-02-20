import { NavLink } from 'react-router-dom'
import {
    UploadCloud, LayoutDashboard, AlertTriangle, BarChart3,
    BookOpen, FileText, TrendingUp, Users,
} from 'lucide-react'

const links = [
    { to: '/', icon: UploadCloud, label: 'Upload', always: true },
    { to: '/overview', icon: LayoutDashboard, label: 'Overview' },
    { to: '/at-risk', icon: AlertTriangle, label: 'At Risk' },
    { to: '/gaps', icon: BarChart3, label: 'Gap Analysis' },
    { to: '/subjects', icon: BookOpen, label: 'Subjects' },
    { to: '/term-comparison', icon: TrendingUp, label: 'Term Comparison' },
    { to: '/reports', icon: FileText, label: 'Reports' },
]

export default function Sidebar({
    hasData,
    schoolName = '',
    classOptions = [],
    selectedClass = '',
    setSelectedClass = () => {},
    className = '',
    onNavigate = () => {},
}) {
    return (
        <aside className={`w-64 bg-brand-dark text-white flex flex-col shrink-0 shadow-2xl ${className}`}>
            {/* Logo */}
            <div className="px-6 py-6 border-b border-white/10">
                <div className="flex items-center gap-3">
                    <img src="/edumetrics-logo.svg" alt="EduMetrics logo" className="w-10 h-10 rounded-xl object-cover" />
                    <div>
                        <h1 className="text-lg font-bold tracking-tight">EduMetrics</h1>
                        <p className="text-xs text-white/50">{schoolName || 'Student Analytics'}</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                {classOptions.length > 0 && (
                    <div className="mx-2 mb-3 p-3 rounded-lg bg-white/5 border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                            <Users size={14} className="text-white/70" />
                            <p className="text-[11px] uppercase tracking-wide text-white/60">Analysis Class</p>
                        </div>
                        <select
                            value={selectedClass}
                            onChange={(e) => setSelectedClass(e.target.value)}
                            className="w-full text-xs px-2 py-1.5 rounded bg-white/10 border border-white/20 text-white focus:outline-none"
                        >
                            {classOptions.map((cls) => (
                                <option key={cls} value={cls} className="text-black">{cls}</option>
                            ))}
                        </select>
                    </div>
                )}
                {links.map(({ to, icon: Icon, label, always }) => {
                    const disabled = !always && !hasData
                    return (
                        <NavLink
                            key={to}
                            to={disabled ? '#' : to}
                            onClick={e => {
                                if (disabled) {
                                    e.preventDefault()
                                    return
                                }
                                onNavigate()
                            }}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${isActive && !disabled
                                    ? 'bg-brand-highlight text-white shadow-lg shadow-brand-highlight/20'
                                    : disabled
                                        ? 'text-white/25 cursor-not-allowed'
                                        : 'text-white/70 hover:bg-white/10 hover:text-white'
                                }`
                            }
                        >
                            <Icon size={18} />
                            {label}
                        </NavLink>
                    )
                })}
            </nav>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-white/10">
                <p className="text-xs text-white/40 leading-relaxed">
                    100% offline analytics.
                    <br />Zero AI dependency.
                </p>
            </div>
        </aside>
    )
}
