'use client';
import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/auth-store';
import {
  LayoutDashboard, TrendingUp, History, Settings,
  LogOut, Box, Users, ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Overview', id: 'nav-dashboard' },
  { href: '/products', icon: Box, label: 'Catalog', id: 'nav-products' },
  { href: '/recommendations', icon: TrendingUp, label: 'Recommendations', id: 'nav-recommendations' },
  { href: '/audit', icon: History, label: 'Audit Trail', id: 'nav-audit' },
  { href: '/admin/config', icon: Settings, label: 'Configuration', id: 'nav-config', adminOnly: true },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, loadFromStorage, logout } = useAuthStore();

  useEffect(() => {
    loadFromStorage();
  }, []);

  useEffect(() => {
    if (!isAuthenticated && !localStorage.getItem('auth_token')) {
      router.push('/login');
    }
  }, [isAuthenticated]);

  const filteredNav = navItems.filter((item) => !item.adminOnly || user?.role === 'admin');

  return (
    <div className="flex h-screen bg-premium-bg overflow-hidden text-premium-text">
      {/* Sidebar - Deep Dark */}
      <aside className="w-[280px] flex-shrink-0 bg-premium-surface border-r border-premium-border flex flex-col relative z-10">
        {/* Logo Section */}
        <div className="pt-10 pb-8 px-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center">
              <Box className="w-5 h-5 text-black" />
            </div>
            <div>
              <div className="font-bold text-xl tracking-wide leading-none text-white">PriceIQ</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 space-y-2 overflow-y-auto pt-2">
          {filteredNav.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                id={item.id}
                className={cn(
                  'flex items-center gap-4 px-4 py-3 rounded-xl text-[15px] transition-all duration-300 group',
                  active
                    ? 'bg-premium-card text-white shadow-inner-premium'
                    : 'text-premium-subtext font-light hover:text-white hover:bg-premium-card/50'
                )}
              >
                <item.icon className={cn('w-5 h-5 transition-colors duration-300', active ? 'text-premium-accent' : 'text-premium-subtext group-hover:text-white')} />
                <span className={active ? 'font-medium' : ''}>{item.label}</span>
                {active && <div className="w-1.5 h-1.5 rounded-full bg-premium-accent ml-auto shadow-[0_0_8px_rgba(59,130,246,0.8)]" />}
              </Link>
            );
          })}
        </nav>

        {/* User Profile / Logout */}
        <div className="p-6">
          <div className="bg-premium-card border border-premium-border rounded-2xl p-4 shadow-inner-premium">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-premium-surface border border-premium-border flex items-center justify-center text-sm font-semibold text-white">
                {user?.full_name?.[0] || user?.email?.[0] || '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[14px] font-medium text-white truncate">{user?.full_name || user?.email}</div>
                <div className="text-[12px] text-premium-subtext capitalize font-light">
                  {user?.role} Account
                </div>
              </div>
            </div>
            <button
              id="logout-btn"
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 text-premium-subtext hover:text-white text-[13px] font-medium px-4 py-2 rounded-xl bg-premium-surface border border-premium-border hover:border-premium-subtext transition-all duration-300"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto bg-premium-bg relative">
        {/* Subtle top glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-premium-accent/5 blur-[120px] rounded-full pointer-events-none" />
        <div className="p-12 min-h-full max-w-[1400px] mx-auto animate-fade-in-up relative z-10">
          {children}
        </div>
      </main>
    </div>
  );
}
