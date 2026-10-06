import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import type { StatusCount } from '@/types/domain';
import { statusLabel } from '@/lib/utils/format';

interface StatusDonutProps {
  data: StatusCount[];
  total: number;
}

const COLORS: Record<string, string> = {
  verified: '#16a34a',
  rejected: '#dc2626',
  needs_review: '#d97706',
  pending: '#94a3b8',
  processing: '#2563eb',
};

export default function StatusDonut({ data, total }: StatusDonutProps) {
  const chartData = data.map((d) => ({ name: statusLabel(d.status), value: d.count, status: d.status }));
  return (
    <div className="flex h-72 flex-col items-center sm:flex-row">
      <div className="relative h-48 w-full sm:h-full sm:w-1/2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={chartData} dataKey="value" nameKey="name" innerRadius="62%" outerRadius="85%" paddingAngle={2} stroke="none">
              {chartData.map((entry) => (
                <Cell key={entry.status} fill={COLORS[entry.status] ?? '#94a3b8'} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: 'var(--c-surface)',
                border: '1px solid var(--c-line)',
                borderRadius: 10,
                fontSize: 12,
                color: 'var(--c-fg)',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-semibold tabular-nums text-fg">{total}</span>
          <span className="text-[11px] uppercase tracking-wide text-fg-subtle">Total</span>
        </div>
      </div>
      <ul className="grid w-full grid-cols-2 gap-x-6 gap-y-3 sm:w-1/2 sm:grid-cols-1">
        {chartData.map((d) => (
          <li key={d.status} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex items-center gap-2 text-fg-muted">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: COLORS[d.status] }} aria-hidden="true" />
              {d.name}
            </span>
            <span className="font-medium tabular-nums text-fg">
              {d.value}
              <span className="ml-1 text-xs text-fg-subtle">({total ? Math.round((d.value / total) * 100) : 0}%)</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
