'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/lib/auth-store';
import { Zap, KeyRound } from 'lucide-react';

export default function JoinPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [form, setForm] = useState({ invite_code: '', full_name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authApi.join({ ...form, invite_code: form.invite_code.toUpperCase() });
      setAuth(res.data.user, res.data.access_token);
      toast.success('Joined workspace! Welcome to PriceIQ 🎉');
      router.push('/recommendations');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Join failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-indigo-600 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-2xl font-black gradient-text">PriceIQ</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Join a workspace</h1>
          <p className="text-slate-400 mt-1 text-sm">Enter your invite code to join as an analyst</p>
        </div>

        <form onSubmit={handleSubmit} className="glass rounded-2xl p-6 space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-300">Invite Code</label>
            <div className="relative">
              <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input id="invite-code" type="text" required value={form.invite_code}
                onChange={(e) => setForm({ ...form, invite_code: e.target.value.toUpperCase() })}
                className="w-full bg-slate-800/60 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 font-mono tracking-widest text-center uppercase"
                placeholder="XXXXXXXX" maxLength={8} />
            </div>
          </div>
          {['full_name', 'email', 'password'].map((key) => (
            <div key={key} className="space-y-1">
              <label className="text-sm font-medium text-slate-300 capitalize">{key.replace('_', ' ')}</label>
              <input id={key} type={key === 'password' ? 'password' : key === 'email' ? 'email' : 'text'}
                required minLength={key === 'password' ? 8 : undefined}
                value={(form as any)[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className="w-full bg-slate-800/60 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm" />
            </div>
          ))}
          <button id="join-submit" type="submit" disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-all">
            {loading ? 'Joining...' : 'Join Workspace'}
          </button>
        </form>
        <p className="text-center text-slate-400 text-sm">
          <Link href="/login" className="text-brand-400 hover:text-brand-300">Sign in instead</Link>
          {' '}·{' '}
          <Link href="/signup" className="text-brand-400 hover:text-brand-300">Create org</Link>
        </p>
      </div>
    </div>
  );
}
