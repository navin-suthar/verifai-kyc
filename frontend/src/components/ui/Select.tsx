import type { SelectHTMLAttributes } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  options: SelectOption[];
  placeholder?: string;
}

export default function Select({ options, placeholder, className, ...rest }: SelectProps) {
  return (
    <div className="relative">
      <select
        className={cn(
          'h-9.5 w-full appearance-none rounded-lg border bg-surface pr-9 pl-3 text-sm text-fg focus:border-brand-500',
          className,
        )}
        {...rest}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute top-1/2 right-3 h-4 w-4 -translate-y-1/2 text-fg-subtle" aria-hidden="true" />
    </div>
  );
}
