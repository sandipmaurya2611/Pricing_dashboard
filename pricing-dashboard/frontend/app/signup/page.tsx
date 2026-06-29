'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/lib/auth-store';
import { Box, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function SignupPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [form, setForm] = useState({
    org_name: '', slug: '', full_name: '', email: '', password: '',
  });
  const [loading, setLoading] = useState(false);

  const handleOrgName = (name: string) => {
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    setForm({ ...form, org_name: name, slug });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authApi.signup(form);
      setAuth(res.data.user, res.data.access_token);
      toast.success('Workspace created! Welcome to PriceIQ');
      router.push('/dashboard');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Signup failed. Please check your details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-premium-bg px-6 py-12 relative overflow-hidden font-sans text-white">
      {/* Premium subtle background glow */}
      <div className="absolute top-1/3 right-1/4 w-[800px] h-[800px] bg-premium-accent/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-10 pointer-events-none" />

      <div className="w-full max-w-5xl relative z-10 grid md:grid-cols-2 gap-16 items-center">
        {/* Left Side Info */}
        <div className="hidden md:block space-y-10 animate-fade-in-up">
          <Link href="/" className="inline-flex items-center gap-4 group">
            <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center transition-transform group-hover:scale-105">
              <Box className="w-6 h-6 text-black" />
            </div>
            <span className="font-bold text-2xl tracking-wide text-white">PriceIQ</span>
          </Link>
          
          <div className="space-y-4">
            <h2 className="text-[44px] font-light text-white tracking-tight leading-[1.1]">
              Deploy your AI pricing engine in seconds.
            </h2>
            <p className="text-premium-subtext text-[18px] font-light max-w-md">
              Join elite teams maximizing revenue with autonomous, data-driven pricing intelligence.
            </p>
          </div>

          <ul className="space-y-6 pt-4">
            {[
              'Multi-agent AI architecture',
              'Automated competitive intelligence',
              'Demand forecasting & elasticity',
              'Full human-in-the-loop workflows'
            ].map((item, i) => (
              <li key={i} className="flex items-center gap-4 text-[16px] text-premium-subtext font-light">
                <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                </div>
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Form */}
        <div className="w-full max-w-[440px] ml-auto animate-fade-in-up [animation-delay:200ms]">
          <form onSubmit={handleSubmit} className="bg-premium-card border border-premium-border rounded-[24px] p-10 shadow-2xl relative">
            {/* Inner highlight */}
            <div className="absolute inset-0 rounded-[24px] shadow-inner-premium pointer-events-none" />
            
            <div className="md:hidden text-center mb-8">
              <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center mx-auto mb-4">
                <Box className="w-6 h-6 text-black" />
              </div>
              <h2 className="text-2xl font-light text-white tracking-tight">Create Workspace</h2>
            </div>

            <div className="space-y-5 relative z-10">
              {[
                { key: 'org_name', label: 'Company Name', type: 'text', placeholder: 'Acme Corp', onChange: handleOrgName },
                { key: 'full_name', label: 'Your Name', type: 'text', placeholder: 'Jane Doe' },
                { key: 'email', label: 'Work Email', type: 'email', placeholder: 'jane@acme.com' },
                { key: 'password', label: 'Password', type: 'password', placeholder: 'Min 8 characters' },
              ].map(({ key, label, type, placeholder, onChange }) => (
                <div key={key} className="space-y-2">
                  <label className="text-[13px] font-medium text-premium-subtext tracking-wide uppercase">{label}</label>
                  <input
                    type={type}
                    required
                    minLength={key === 'password' ? 8 : undefined}
                    value={(form as any)[key]}
                    onChange={(e) => onChange ? onChange(e.target.value) : setForm({ ...form, [key]: e.target.value })}
                    className="w-full bg-premium-surface border border-premium-border rounded-xl px-4 py-3.5 text-[15px] font-light text-white placeholder-premium-subtext/40 focus:outline-none focus:border-premium-subtext transition-colors shadow-inner-premium"
                    placeholder={placeholder}
                  />
                </div>
              ))}

              {form.slug && (
                <div className="text-[13px] font-light text-premium-subtext bg-premium-surface/50 p-3 rounded-xl border border-premium-border/50">
                  Workspace URL: <span className="text-white font-medium ml-1">priceiq.app/{form.slug}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full relative group overflow-hidden rounded-xl bg-white text-black font-semibold text-[15px] py-4 mt-4 transition-all hover:bg-gray-100 disabled:opacity-50 flex items-center justify-center gap-3"
              >
                {loading ? 'Creating workspace...' : 'Create Workspace'}
                {!loading && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
              </button>
            </div>
          </form>

          <div className="text-center mt-8 text-[14px] font-light text-premium-subtext">
            Already have an account?{' '}
            <Link href="/login" className="text-white font-medium hover:underline underline-offset-4 transition-all">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
