import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/utils/cn';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leftIcon?: ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(function Input({ leftIcon, className, ...rest }, ref) {
  return (
    <div className="relative">
      {leftIcon && (
        <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-fg-subtle" aria-hidden="true">
          {leftIcon}
        </span>
      )}
      <input
        ref={ref}
        className={cn(
          'h-9.5 w-full rounded-lg border bg-surface text-sm text-fg placeholder:text-fg-subtle focus:border-brand-500',
          leftIcon ? 'pl-9 pr-3' : 'px-3',
          className,
        )}
        {...rest}
      />
    </div>
  );
});

export default Input;
