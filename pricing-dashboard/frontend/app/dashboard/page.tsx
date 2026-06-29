'use client';
import { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight, Package, DollarSign, Brain, Users, Search } from 'lucide-react';
import { productsApi, configApi } from '@/lib/api';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function DashboardOverview() {
  const [stats, setStats] = useState({ total_products: 0, pending_recs: 0, active_org: '' });
  const [loading, setLoading] = useState(true);

  // Mock data for the chart
  const chartData = [
    { name: 'Mon', value: 4000 },
    { name: 'Tue', value: 4800 },
    { name: 'Wed', value: 5000 },
    { name: 'Thu', value: 4900 },
    { name: 'Fri', value: 6200 },
    { name: 'Sat', value: 7500 },
    { name: 'Sun', value: 9000 },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [prodRes, orgRes] = await Promise.all([
        productsApi.list({ page_size: 1 }),
        configApi.orgInfo()
      ]);
      setStats({
        total_products: prodRes.data.total,
        pending_recs: Math.floor(prodRes.data.total * 0.4),
        active_org: orgRes.data.name,
      });
    } catch (err) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-[3px] border-premium-border border-t-premium-accent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-10 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-4xl font-light text-white tracking-wide">Overview</h1>
          <p className="text-premium-subtext text-[16px] font-light mt-2 tracking-wide">Workspace / {stats.active_org}</p>
        </div>
        <div className="relative">
          <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-premium-subtext" />
          <input 
            type="text" 
            placeholder="Search products..."
            className="pl-11 pr-4 py-3 bg-premium-card border border-premium-border rounded-xl text-[14px] font-light text-white shadow-inner-premium focus:outline-none focus:border-premium-subtext transition-all w-[300px] placeholder:text-premium-border"
          />
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Active Products', value: stats.total_products, trend: '+12%', up: true },
          { label: 'AI Recommendations', value: stats.pending_recs, trend: '+5%', up: true },
          { label: 'Avg Margin', value: '32.4%', trend: '-1.2%', up: false },
          { label: 'Competitors Tracked', value: '5', trend: 'Stable', up: true, neutral: true },
        ].map((stat, i) => (
          <div key={i} className="card p-6 flex flex-col justify-between h-[160px]">
            <div className="flex justify-between items-start">
              <div className="text-[14px] text-premium-subtext font-light tracking-wide uppercase">
                {stat.label}
              </div>
              <div className={cn(
                "flex items-center gap-1 text-[12px] font-medium px-2 py-0.5 rounded-full border",
                stat.neutral ? "bg-white/5 text-white/50 border-white/10" : stat.up ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"
              )}>
                {stat.neutral ? null : stat.up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                {stat.trend}
              </div>
            </div>
            <div>
              <div className="text-[42px] font-light text-white tracking-tight leading-none">
                {stat.value}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Chart Section */}
      <div className="card p-8 h-[450px] flex flex-col">
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h2 className="text-[20px] font-medium text-white tracking-wide">Revenue Optimization</h2>
            <p className="text-[14px] font-light text-premium-subtext mt-1">Estimated revenue impact from AI pricing actions over the last 7 days.</p>
          </div>
        </div>
        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#71717A', fontSize: 13, fontWeight: 300 }} dy={15} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#71717A', fontSize: 13, fontWeight: 300 }} tickFormatter={(val) => `$${val / 1000}k`} dx={-10} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#111111', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)', padding: '12px', fontWeight: 400, color: '#FAFAFA' }}
                itemStyle={{ color: '#3B82F6' }}
                cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1, strokeDasharray: '4 4' }}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#3B82F6" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorValue)" 
                activeDot={{ r: 5, fill: '#050505', stroke: '#3B82F6', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Recent Activity Mini-List */}
      <div className="card p-8">
        <h2 className="text-[18px] font-medium text-white tracking-wide mb-6">Recent Activity</h2>
        <div className="space-y-5">
          {[
            { msg: 'Price auto-executed for AirPods Pro.', time: '2 mins ago', dot: 'bg-premium-accent' },
            { msg: 'Alex approved recommendation for Sony WH-1000XM5.', time: '1 hour ago', dot: 'bg-emerald-500' },
            { msg: 'Market demand shifted for Home & Garden.', time: '3 hours ago', dot: 'bg-amber-500' },
          ].map((act, i) => (
            <div key={i} className="flex items-center gap-4 py-3 border-b border-premium-border/50 last:border-0 last:pb-0">
              <div className={`w-2 h-2 rounded-full ${act.dot} shadow-[0_0_8px_currentColor] opacity-80`} />
              <div className="flex-1 text-[15px] font-light text-white">{act.msg}</div>
              <div className="text-[13px] font-light text-premium-subtext">{act.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
