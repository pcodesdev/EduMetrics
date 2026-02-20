import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid, Label } from 'recharts'

const PALETTE = ['#0f3460', '#e94560', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']

export default function GapChart({ data, title, xKey = 'group', bars = [], height = 320 }) {
    // data: [{ group, value1, value2, ... }]
    // bars: [{ key, label, color? }]

    if (!data?.length) {
        return (
            <div className="bg-card rounded-xl p-6 text-center text-gray-400 text-sm shadow-sm">
                No gap data available
            </div>
        )
    }

    return (
        <div className="bg-card rounded-xl shadow-sm border border-gray-100 p-5">
            {title && (
                <h3 className="text-sm font-semibold text-gray-700 mb-4">{title}</h3>
            )}
            <ResponsiveContainer width="100%" height={height}>
                <BarChart data={data} barGap={2} barCategoryGap="20%">
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis
                        dataKey={xKey}
                        tick={{ fontSize: 11, fill: '#64748b' }}
                        axisLine={{ stroke: '#e2e8f0' }}
                        tickLine={false}
                    >
                        <Label value="Group" position="insideBottom" offset={-2} style={{ fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                    </XAxis>
                    <YAxis
                        tick={{ fontSize: 11, fill: '#64748b' }}
                        axisLine={false}
                        tickLine={false}
                        domain={[0, 100]}
                        tickFormatter={v => `${v}%`}
                    >
                        <Label value="Score (%)" angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fill: '#475569', fontSize: 12, fontWeight: 600 }} />
                    </YAxis>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#0f172a',
                            border: '1px solid #334155',
                            borderRadius: 8,
                            fontSize: 12,
                            color: '#f8fafc',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                        }}
                        labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                        itemStyle={{ color: '#f8fafc' }}
                        formatter={(value) => [`${Number(value).toFixed(1)}%`]}
                        cursor={{ fill: 'rgba(15, 52, 96, 0.06)' }}
                    />
                    <Legend
                        wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
                    />
                    {bars.map((bar, i) => (
                        <Bar
                            key={bar.key}
                            dataKey={bar.key}
                            name={bar.label || bar.key}
                            fill={bar.color || PALETTE[i % PALETTE.length]}
                            radius={[4, 4, 0, 0]}
                            maxBarSize={40}
                        />
                    ))}
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}
