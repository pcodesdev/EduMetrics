const riskConfig = {
    high: { bg: 'bg-danger/10', text: 'text-danger', ring: 'ring-danger/20', dot: 'bg-danger' },
    medium: { bg: 'bg-warning/10', text: 'text-warning', ring: 'ring-warning/20', dot: 'bg-warning' },
    low: { bg: 'bg-success/10', text: 'text-success', ring: 'ring-success/20', dot: 'bg-success' },
    none: { bg: 'bg-gray-100', text: 'text-gray-500', ring: 'ring-gray-200', dot: 'bg-gray-400' },
}

export default function RiskBadge({ level = 'none', size = 'md' }) {
    const normalised = (level || 'none').toLowerCase()
    const config = riskConfig[normalised] || riskConfig.none
    const label = normalised.charAt(0).toUpperCase() + normalised.slice(1)

    const sizeClasses = size === 'sm'
        ? 'text-[10px] px-2 py-0.5 gap-1'
        : 'text-xs px-2.5 py-1 gap-1.5'
    const dotSize = size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2'

    return (
        <span
            className={`inline-flex items-center ${sizeClasses} font-semibold tracking-wide rounded-full
                         ring-1 ${config.bg} ${config.text} ${config.ring}`}
        >
            <span className={`${dotSize} rounded-full ${config.dot} animate-pulse-soft`} />
            {label}
        </span>
    )
}
