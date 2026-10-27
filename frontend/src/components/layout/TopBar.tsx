import { useNavigate } from 'react-router-dom';
import { LogOut, Menu, Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useToast } from '@/contexts/ToastContext';
import { ROUTES } from '@/app/routes';

interface TopBarProps {
  onOpenSidebar: () => void;
}

export default function TopBar({ onOpenSidebar }: TopBarProps) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    toast({ title: 'Signed out', variant: 'info' });
    navigate(ROUTES.login, { replace: true });
  };

  const initials = (user?.display_name ?? 'D')
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b bg-surface/80 px-4 backdrop-blur sm:px-6">
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onOpenSidebar} aria-label="Open navigation">
        <Menu className="h-5 w-5" />
      </Button>

      <div className="hidden items-center gap-2 text-sm text-fg-muted sm:flex">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-warning/40 bg-warning-soft px-2.5 py-0.5 text-xs font-medium text-amber-800 dark:text-amber-300">
          <span className="h-1.5 w-1.5 rounded-full bg-warning" aria-hidden="true" />
          MOCK verification · synthetic data only
        </span>
      </div>

      <div className="ml-auto flex items-center gap-1.5">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun className="h-4.5 w-4.5" /> : <Moon className="h-4.5 w-4.5" />}
        </Button>

        <div className="mx-1 hidden h-6 w-px bg-line sm:block" aria-hidden="true" />

        <div className="flex items-center gap-2.5 pl-1">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
            {initials}
          </span>
          <span className="hidden leading-tight md:block">
            <span className="block text-sm font-medium text-fg">{user?.display_name ?? 'Demo user'}</span>
            <span className="block text-[11px] capitalize text-fg-subtle">{user?.role ?? 'guest'}</span>
          </span>
          <Button variant="ghost" size="icon" onClick={handleLogout} aria-label="Sign out">
            <LogOut className="h-4.5 w-4.5" />
          </Button>
        </div>
      </div>
    </header>
  );
}
