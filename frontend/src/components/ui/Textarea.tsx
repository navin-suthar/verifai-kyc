import { forwardRef, type TextareaHTMLAttributes } from 'react';
import { cn } from '@/lib/utils/cn';

const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(function Textarea(
  { className, ...rest },
  ref,
) {
  return (
    <textarea
      ref={ref}
      className={cn(
        'min-h-24 w-full rounded-lg border bg-surface px-3 py-2 text-sm text-fg placeholder:text-fg-subtle focus:border-brand-500',
        className,
      )}
      {...rest}
    />
  );
});

export default Textarea;
