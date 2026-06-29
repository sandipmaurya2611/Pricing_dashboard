'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/lib/auth-store';
import { Box, ArrowRight } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authApi.login({ email: form.email, password: form.password });
      setAuth(res.data.user, res.data.access_token);
      toast.success('Welcome back!');
      router.push('/dashboard');
    } catch (err) {
      toast.error('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const loadDemo = () => setForm({ email: 'admin@klypup.com', password: 'Admin@123' });

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-premium-bg px-6 relative overflow-hidden font-sans text-white">
      {/* Premium subtle background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-premium-accent/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-10 pointer-events-none" />

      <div className="w-full max-w-[440px] relative z-10 animate-fade-in-up">
        {/* Logo Header */}
        <div className="text-center mb-10">
          <Link href="/" className="inline-flex items-center gap-3 group mb-8">
            <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center transition-transform group-hover:scale-105">
              <Box className="w-6 h-6 text-black" />
            </div>
            <span className="font-bold text-2xl tracking-wide text-white">PriceIQ</span>
          </Link>
          <h1 className="text-[32px] font-light text-white tracking-tight leading-tight">
            Welcome back
          </h1>
          <p className="text-premium-subtext text-[16px] font-light mt-2">
            Sign in to your workspace
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-premium-card border border-premium-border rounded-[24px] p-10 shadow-2xl relative">
          {/* Inner highlight */}
          <div className="absolute inset-0 rounded-[24px] shadow-inner-premium pointer-events-none" />

          <div className="space-y-6 relative z-10">
            <div className="space-y-2">
              <label className="text-[13px] font-medium text-premium-subtext tracking-wide uppercase">Work Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full bg-premium-surface border border-premium-border rounded-xl px-4 py-3.5 text-[15px] font-light text-white placeholder-premium-subtext/40 focus:outline-none focus:border-premium-subtext transition-colors shadow-inner-premium"
                placeholder="jane@acme.com"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-[13px] font-medium text-premium-subtext tracking-wide uppercase">Password</label>
              </div>
              <input
                type="password"
                required
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full bg-premium-surface border border-premium-border rounded-xl px-4 py-3.5 text-[15px] font-light text-white placeholder-premium-subtext/40 focus:outline-none focus:border-premium-subtext transition-colors shadow-inner-premium"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full relative group overflow-hidden rounded-xl bg-white text-black font-semibold text-[15px] py-4 mt-2 transition-all hover:bg-gray-100 disabled:opacity-50 flex items-center justify-center gap-3"
            >
              {loading ? 'Signing in...' : 'Sign In'}
              {!loading && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
            </button>
          </div>
        </form>

        <div className="text-center mt-8 space-y-4">
          <div className="text-[14px] font-light text-premium-subtext">
            Don't have an account?{' '}
            <Link href="/signup" className="text-white font-medium hover:underline underline-offset-4 transition-all">
              Create workspace
            </Link>
          </div>
          
          <button 
            onClick={loadDemo}
            className="text-[13px] font-light text-premium-subtext hover:text-white transition-colors underline underline-offset-4"
          >
            Load Demo Admin Credentials
          </button>
        </div>
      </div>
    </div>
  );
}
