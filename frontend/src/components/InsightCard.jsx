import { AlertTriangle, TrendingDown, TrendingUp, Info, AlertCircle, CheckCircle } from 'lucide-react'

const severityConfig = {
    critical: {
        border: 'border-l-danger',
        bg: 'bg-red-50',
        icon: AlertCircle,
        iconColor: 'text-danger',
        badge: 'bg-danger text-white',
    },
    high: {
        border: 'border-l-brand-highlight',
        bg: 'bg-red-50/50',
        icon: AlertTriangle,
        iconColor: 'text-brand-highlight',
        badge: 'bg-brand-highlight text-white',
    },
    medium: {
        border: 'border-l-warning',
        bg: 'bg-amber-50',
        icon: TrendingDown,
        iconColor: 'text-warning',
        badge: 'bg-warning text-white',
    },
    low: {
        border: 'border-l-info',
        bg: 'bg-blue-50',
        icon: Info,
        iconColor: 'text-info',
        badge: 'bg-info text-white',
    },
    positive: {
        border: 'border-l-success',
        bg: 'bg-green-50',
        icon: CheckCircle,
        iconColor: 'text-success',
        badge: 'bg-success text-white',
    },
}

export default function InsightCard({ title, description, severity = 'low', category }) {
    const config = severityConfig[severity] || severityConfig.low
    const Icon = config.icon

    return (
        <div
            className={`${config.bg} ${config.border} border-l-4 rounded-lg p-4 shadow-sm
                         hover:shadow-md transition-all duration-200 animate-fade-in`}
        >
            <div className="flex items-start gap-3">
                <div className={`mt-0.5 ${config.iconColor}`}>
                    <Icon size={18} />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                        <h4 className="text-sm font-semibold text-gray-800">{title}</h4>
                        <span className={`${config.badge} text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider`}>
                            {severity}
                        </span>
                        {category && (
                            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                                {category}
                            </span>
                        )}
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed">{description}</p>
                </div>
            </div>
        </div>
    )
}
