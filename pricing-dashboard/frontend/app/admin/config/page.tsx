'use client';
import { useEffect, useState } from 'react';
import { configApi } from '@/lib/api';
import { Settings, Shield, Copy, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function AdminConfigPage() {
  const [config, setConfig] = useState<any>(null);
  const [orgInfo, setOrgInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [form, setForm] = useState({
    auto_execute_threshold: 85,
    margin_floor_default: 15,
  });

  useEffect(() => {
    (async () => {
      try {
        const [configRes, orgRes] = await Promise.all([configApi.get(), configApi.orgInfo()]);
        setConfig(configRes.data);
        setOrgInfo(orgRes.data);
        setForm({
          auto_execute_threshold: configRes.data.auto_execute_threshold,
          margin_floor_default: configRes.data.margin_floor_default,
        });
      } catch { toast.error('Failed to load config'); }
      finally { setLoading(false); }
    })();
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await configApi.update(form);
      toast.success('Configuration saved!');
    } catch { toast.error('Save failed'); }
    finally { setSaving(false); }
  };

  const copyCode = () => {
    navigator.clipboard.writeText(orgInfo?.invite_code || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Invite code copied!');
  };

  if (loading) return (
    <div className="card h-64 animate-pulse flex items-center justify-center border border-premium-border">
      <div className="w-8 h-8 border-[3px] border-premium-border border-t-premium-accent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-8 max-w-2xl pb-12">
      <div>
        <h1 className="text-3xl font-light text-white flex items-center gap-4 tracking-wide">
          <Settings className="w-7 h-7 text-premium-accent" /> Configuration
        </h1>
        <p className="text-premium-subtext text-[15px] font-light mt-2 tracking-wide">Admin-only: configure AI thresholds and organization settings.</p>
      </div>

      {/* AI Engine Config */}
      <div className="card p-8 space-y-8 shadow-2xl relative">
        <h2 className="text-[18px] font-medium text-white flex items-center gap-3 tracking-wide">
          <Shield className="w-5 h-5 text-premium-accent" /> AI Engine Thresholds
        </h2>

        <div className="space-y-2">
          <label className="text-[14px] font-medium text-white tracking-wide">Auto-Execute Threshold (%)</label>
          <p className="text-[13px] font-light text-premium-subtext">Recommendations above this confidence score execute automatically without analyst review.</p>
          <div className="flex items-center gap-6 mt-4">
            <input
              id="auto-execute-threshold"
              type="range"
              min={50}
              max={99}
              value={form.auto_execute_threshold}
              onChange={(e) => setForm({ ...form, auto_execute_threshold: Number(e.target.value) })}
              className="flex-1 accent-premium-accent h-1.5 bg-premium-surface rounded-full appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-premium-accent [&::-webkit-slider-thumb]:rounded-full cursor-pointer"
            />
            <div className="w-20 text-right">
              <span className="text-[28px] font-light text-premium-accent leading-none">{form.auto_execute_threshold}%</span>
            </div>
          </div>
          <div className="flex justify-between text-[11px] font-light text-premium-subtext/60 mt-2 uppercase tracking-widest">
            <span>50% (High Automation)</span>
            <span>99% (Manual)</span>
          </div>
        </div>

        <div className="space-y-2 pt-2 border-t border-premium-border/50">
          <label className="text-[14px] font-medium text-white tracking-wide mt-6 block">Default Margin Floor (%)</label>
          <p className="text-[13px] font-light text-premium-subtext">AI will never recommend prices that result in margins below this percentage.</p>
          <div className="flex items-center gap-6 mt-4">
            <input
              id="margin-floor"
              type="range"
              min={5}
              max={50}
              value={form.margin_floor_default}
              onChange={(e) => setForm({ ...form, margin_floor_default: Number(e.target.value) })}
              className="flex-1 accent-emerald-500 h-1.5 bg-premium-surface rounded-full appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-emerald-500 [&::-webkit-slider-thumb]:rounded-full cursor-pointer"
            />
            <div className="w-20 text-right">
              <span className="text-[28px] font-light text-emerald-400 leading-none">{form.margin_floor_default}%</span>
            </div>
          </div>
        </div>

        <button
          id="save-config-btn"
          onClick={save}
          disabled={saving}
          className="w-full bg-white hover:bg-gray-200 text-black font-semibold text-[14px] py-3.5 rounded-xl transition-all disabled:opacity-50 mt-4"
        >
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>

      {/* Org Info */}
      {orgInfo && (
        <div className="card p-8 space-y-6">
          <h2 className="text-[18px] font-medium text-white tracking-wide">Organization</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center text-[14px] pb-4 border-b border-premium-border/50">
              <span className="text-premium-subtext font-light">Name</span>
              <span className="text-white font-medium">{orgInfo.name}</span>
            </div>
            <div className="flex justify-between items-center text-[14px] pb-4 border-b border-premium-border/50">
              <span className="text-premium-subtext font-light">URL Slug</span>
              <span className="text-white font-mono bg-premium-surface px-2 py-1 rounded-md border border-premium-border text-[12px]">{orgInfo.slug}</span>
            </div>
            <div className="flex justify-between items-center text-[14px]">
              <span className="text-premium-subtext font-light">Invite Code</span>
              <button
                id="copy-invite-btn"
                onClick={copyCode}
                className="flex items-center gap-2 bg-premium-surface hover:bg-white/5 text-white font-mono text-[13px] px-3 py-2 rounded-lg border border-premium-border transition-colors shadow-inner-premium"
              >
                {orgInfo.invite_code}
                {copied ? <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-premium-subtext" />}
              </button>
            </div>
          </div>
          <p className="text-[12px] font-light text-premium-subtext/80 pt-2">Share this invite code with analysts to let them join your workspace securely.</p>
        </div>
      )}
    </div>
  );
}
