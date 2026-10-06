import {
  BarChart3,
  Bot,
  FileSearch,
  LayoutDashboard,
  ScrollText,
  Upload,
  UserCheck,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  section: 'operations' | 'intelligence' | 'governance';
}

export const ROUTES = {
  login: '/login',
  dashboard: '/',
  applications: '/applications',
  application: (id: string) => `/applications/${encodeURIComponent(id)}`,
  applicationResult: (id: string) => `/applications/${encodeURIComponent(id)}/result`,
  upload: '/upload',
  review: '/review',
  assistant: '/assistant',
  audit: '/audit',
  analytics: '/analytics',
} as const;

export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: ROUTES.dashboard, icon: LayoutDashboard, section: 'operations' },
  { label: 'Applications', path: ROUTES.applications, icon: FileSearch, section: 'operations' },
  { label: 'Upload Document', path: ROUTES.upload, icon: Upload, section: 'operations' },
  { label: 'Human Review', path: ROUTES.review, icon: UserCheck, section: 'operations' },
  { label: 'Knowledge Assistant', path: ROUTES.assistant, icon: Bot, section: 'intelligence' },
  { label: 'Analytics', path: ROUTES.analytics, icon: BarChart3, section: 'intelligence' },
  { label: 'Audit Logs', path: ROUTES.audit, icon: ScrollText, section: 'governance' },
];

export const NAV_SECTIONS: { id: NavItem['section']; label: string }[] = [
  { id: 'operations', label: 'Operations' },
  { id: 'intelligence', label: 'Intelligence' },
  { id: 'governance', label: 'Governance' },
];
