import Link from 'next/link';
import { ArrowRight, Brain, Zap, LineChart, ShieldCheck, Database, LayoutDashboard } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#030712] selection:bg-brand-500/30 overflow-hidden relative">
      {/* Dynamic Background Effects */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-brand-600/20 blur-[120px] mix-blend-screen animate-pulse-slow" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-600/10 blur-[150px] mix-blend-screen" />
        <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] rounded-full bg-emerald-600/10 blur-[100px] mix-blend-screen" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
      </div>

      {/* Navigation */}
      <nav className="border-b border-white/5 bg-black/20 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg text-white tracking-tight">PriceIQ</span>
          </div>
          <div className="flex gap-4">
            <Link href="/login" className="text-sm font-medium text-slate-300 hover:text-white transition-colors px-4 py-2">
              Sign In
            </Link>
            <Link href="/signup" className="text-sm font-medium bg-white text-black hover:bg-slate-200 transition-all px-4 py-2 rounded-full shadow-[0_0_20px_rgba(255,255,255,0.1)]">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-6 pt-32 pb-24 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs font-semibold mb-8 animate-fade-in-up">
          <span className="flex h-2 w-2 rounded-full bg-brand-400 animate-ping-slow" />
          Powered by GPT-4o Multi-Agent Architecture
        </div>
        
        <h1 className="text-6xl md:text-8xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 tracking-tight mb-8 animate-fade-in-up [animation-delay:100ms]">
          Pricing Intelligence, <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-brand-400 to-indigo-400">
            Automated.
          </span>
        </h1>
        
        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed animate-fade-in-up [animation-delay:200ms]">
          Deploy autonomous AI agents to monitor competitors, forecast demand, and execute optimal pricing strategies with human-in-the-loop compliance.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up [animation-delay:300ms]">
          <Link href="/signup" className="group relative inline-flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold px-8 py-4 rounded-full overflow-hidden transition-all duration-300 hover:scale-105 hover:shadow-[0_0_40px_rgba(14,165,233,0.4)]">
            <span className="relative z-10 flex items-center gap-2">
              Create Workspace <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-brand-400/0 via-white/20 to-brand-400/0 -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
          </Link>
          <Link href="/join" className="inline-flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium px-8 py-4 rounded-full transition-all duration-300 hover:border-white/20">
            Join with Invite Code
          </Link>
        </div>
      </div>

      {/* Feature Grid */}
      <div className="max-w-7xl mx-auto px-6 py-24 border-t border-white/5 relative">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px] bg-gradient-to-r from-transparent via-brand-500/50 to-transparent" />
        
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: Brain,
              title: 'Multi-Agent AI',
              desc: '5 specialized agents analyze market intel, inventory, and demand in parallel for precise recommendations.',
              color: 'from-brand-500 to-indigo-500'
            },
            {
              icon: LineChart,
              title: 'Dynamic Forecasting',
              desc: 'Real-time competitive analysis combined with seasonality and velocity to maximize margins.',
              color: 'from-emerald-500 to-teal-500'
            },
            {
              icon: ShieldCheck,
              title: 'Human-in-the-Loop',
              desc: 'Set confidence thresholds for auto-execution, routing complex cases to analysts with full reasoning.',
              color: 'from-amber-500 to-orange-500'
            }
          ].map((feature, i) => (
            <div key={i} className="group p-8 rounded-3xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-all duration-500 hover:-translate-y-2">
              <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${feature.color} p-0.5 mb-6 opacity-80 group-hover:opacity-100 transition-opacity`}>
                <div className="w-full h-full bg-black/50 backdrop-blur-xl rounded-[14px] flex items-center justify-center">
                  <feature.icon className="w-5 h-5 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
              <p className="text-slate-400 leading-relaxed text-sm">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
