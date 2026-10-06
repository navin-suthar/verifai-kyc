import type { ReactNode } from 'react';
import { cn } from '@/lib/utils/cn';

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
  align?: 'left' | 'right' | 'center';
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  emptyState?: ReactNode;
  className?: string;
  dense?: boolean;
}

const ALIGN = { left: 'text-left', right: 'text-right', center: 'text-center' } as const;

export default function Table<T>({ columns, rows, rowKey, onRowClick, emptyState, className, dense }: TableProps<T>) {
  if (rows.length === 0 && emptyState) return <>{emptyState}</>;
  return (
    <div className={cn('overflow-x-auto scrollbar-thin', className)}>
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <thead>
          <tr className="border-b">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={cn(
                  'px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-fg-subtle',
                  ALIGN[col.align ?? 'left'],
                  col.className,
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              onKeyDown={
                onRowClick
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onRowClick(row);
                      }
                    }
                  : undefined
              }
              tabIndex={onRowClick ? 0 : undefined}
              className={cn(
                'border-b last:border-b-0 transition-colors',
                onRowClick && 'cursor-pointer hover:bg-surface-2 focus-visible:bg-surface-2',
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn('px-3', dense ? 'py-2' : 'py-3', ALIGN[col.align ?? 'left'], col.className)}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
