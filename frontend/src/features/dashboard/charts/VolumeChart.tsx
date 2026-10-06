import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
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
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }} barCategoryGap="30%">
          <CartesianGrid strokeDasharray="3 3" stroke={grid} vertical={false} />
          <XAxis dataKey="date" tickFormatter={formatShortDate} tick={{ fill: tick, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: tick, fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip
            cursor={{ fill: grid, opacity: 0.4 }}
            labelFormatter={(label) => formatShortDate(String(label))}
            contentStyle={{
              background: 'var(--c-surface)',
              border: '1px solid var(--c-line)',
              borderRadius: 10,
              fontSize: 12,
              color: 'var(--c-fg)',
            }}
          />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
          {SERIES.map((s, i) => (
            <Bar
              key={s.key}
              dataKey={s.key}
              name={s.label}
              stackId="volume"
              fill={s.color}
              radius={i === SERIES.length - 1 ? [4, 4, 0, 0] : 0}
              maxBarSize={28}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
