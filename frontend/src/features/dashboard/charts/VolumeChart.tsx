import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DailyVolume } from '@/types/domain';
import { formatShortDate } from '@/lib/utils/format';
import { useTheme } from '@/contexts/ThemeContext';

interface VolumeChartProps {
  data: DailyVolume[];
}

const SERIES = [
  { key: 'verified', label: 'Verified', color: '#16a34a' },
  { key: 'needs_review', label: 'Needs review', color: '#d97706' },
  { key: 'rejected', label: 'Rejected', color: '#dc2626' },
] as const;

export default function VolumeChart({ data }: VolumeChartProps) {
  const { theme } = useTheme();
  const grid = theme === 'dark' ? '#243044' : '#e2e8f0';
  const tick = theme === 'dark' ? '#9ca3af' : '#64748b';

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            {SERIES.map((s) => (
              <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={s.color} stopOpacity={0.35} />
                <stop offset="95%" stopColor={s.color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={grid} vertical={false} />
          <XAxis dataKey="date" tickFormatter={formatShortDate} tick={{ fill: tick, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: tick, fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip
            labelFormatter={(label) => formatShortDate(String(label))}
            contentStyle={{
              background: 'var(--c-surface)',
              border: '1px solid var(--c-line)',
              borderRadius: 10,
              fontSize: 12,
              color: 'var(--c-fg)',
            }}
          />
          {SERIES.map((s) => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stroke={s.color}
              strokeWidth={2}
              fill={`url(#grad-${s.key})`}
              stackId="1"
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
