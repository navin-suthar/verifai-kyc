import { NavLink } from 'react-router-dom';
import { ShieldCheck, X } from 'lucide-react';
import { NAV_ITEMS, NAV_SECTIONS } from '@/app/routes';
import { env } from '@/config/env';
import { cn } from '@/lib/utils/cn';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile backdrop */}
      <div
        aria-hidden="true"
        onClick={onClose}
        className={cn(
          'fixed inset-0 z-30 bg-black/40 backdrop-blur-sm transition-opacity lg:hidden',
          isOpen ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
      />
      <aside
        aria-label="Primary navigation"
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r bg-surface transition-transform lg:static lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-16 items-center justify-between border-b px-5">
          <NavLink to="/" className="flex items-center gap-2.5" onClick={onClose}>
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white shadow-sm">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </span>
            <span className="leading-tight">
              <span className="block text-sm font-semibold text-fg">{env.appName}</span>
              <span className="block text-[11px] text-fg-subtle">KYC Document Intelligence</span>
            </span>
          </NavLink>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation"
            className="rounded-md p-1.5 text-fg-subtle hover:bg-surface-2 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 scrollbar-thin">
          {NAV_SECTIONS.map((section) => (
            <div key={section.id} className="mb-5">
              <p className="mb-1.5 px-2 text-[11px] font-semibold uppercase tracking-wider text-fg-subtle">
                {section.label}
              </p>
              <ul className="space-y-0.5">
                {NAV_ITEMS.filter((i) => i.section === section.id).map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      end={item.path === '/'}
                      onClick={onClose}
                      className={({ isActive }) =>
                        cn(
                          'group flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors',
                          isActive
                            ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
                            : 'text-fg-muted hover:bg-surface-2 hover:text-fg',
                        )
                      }
                    >
                      <item.icon className="h-4.5 w-4.5 shrink-0" aria-hidden="true" />
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        <div className="border-t p-4">
          <div className="rounded-lg border border-warning/30 bg-warning-soft/60 p-3">
            <p className="text-xs font-semibold text-amber-800 dark:text-amber-300">Demo environment</p>
            <p className="mt-0.5 text-[11px] leading-snug text-amber-800/80 dark:text-amber-200/80">
              All documents and identities are synthetic. Verification providers are mocked.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
