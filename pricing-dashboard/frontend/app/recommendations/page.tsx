'use client';
import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { recommendationsApi } from '@/lib/api';
import { formatCurrency, formatPct, getStatusColor, getConfidenceBg, cn, formatDate } from '@/lib/utils';
import { Brain, CheckCircle, XCircle, ChevronRight, TrendingDown, TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';

interface Rec {
  id: string;
  product: { id: string; name: string; sku: string; category: { name: string } | null } | null;
  recommended_price: number;
  current_price: number;
  confidence_score: number;
  price_change_pct: number;
  status: string;
  created_at: string;
  reasoning: { rationale: string } | null;
}

export default function RecommendationsPage() {
  const [recs, setRecs] = useState<Rec[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [processing, setProcessing] = useState<string | null>(null);
  const [rejectModal, setRejectModal] = useState<{ id: string } | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await recommendationsApi.list({ status_filter: statusFilter || undefined });
      setRecs(res.data.items);
    } catch {
      toast.error('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { load(); }, [load]);

  const approve = async (id: string) => {
    setProcessing(id);
    try {
      await recommendationsApi.approve(id);
      toast.success('Approved and executed!');
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Approval failed');
    } finally {
      setProcessing(null);
    }
  };

  const reject = async () => {
    if (!rejectModal) return;
    if (rejectReason.length < 5) { toast.error('Please provide a reason (min 5 chars)'); return; }
    setProcessing(rejectModal.id);
    try {
      await recommendationsApi.reject(rejectModal.id, rejectReason);
      toast.success('Recommendation rejected');
      setRejectModal(null);
      setRejectReason('');
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Rejection failed');
    } finally {
      setProcessing(null);
    }
  };

  const pendingCount = recs.filter(r => r.status === 'pending').length;

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-4 mb-2">
          <h1 className="text-3xl font-light text-white tracking-wide">Recommendations</h1>
          {pendingCount > 0 && statusFilter === 'pending' && (
            <span className="bg-amber-500/10 text-amber-500 border border-amber-500/20 text-[11px] font-medium px-2 py-0.5 rounded-md uppercase tracking-widest">
              {pendingCount} Pending
            </span>
          )}
        </div>
        <p className="text-premium-subtext text-[15px] font-light tracking-wide">AI-generated pricing actions prioritized by confidence score.</p>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex gap-2">
        {['pending', 'approved', 'rejected', 'auto_executed', 'modified', ''].map((s) => (
          <button
            key={s}
            id={`filter-${s || 'all'}`}
            onClick={() => setStatusFilter(s)}
            className={cn(
              'px-5 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-300 border',
              statusFilter === s
                ? 'bg-premium-card text-white border-premium-border shadow-inner-premium'
                : 'bg-transparent text-premium-subtext border-transparent hover:text-white hover:bg-premium-surface'
            )}
          >
            {s ? s.replace('_', ' ') : 'All'}
          </button>
        ))}
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="card p-6 animate-pulse flex items-start gap-6">
              <div className="w-16 h-16 bg-premium-border/50 rounded-2xl" />
              <div className="flex-1 space-y-4 pt-2">
                <div className="h-4 bg-premium-border/50 rounded w-1/3" />
                <div className="h-3 bg-premium-border/30 rounded w-1/2" />
              </div>
            </div>
          ))
        ) : recs.length === 0 ? (
          <div className="card p-20 text-center flex flex-col items-center justify-center">
            <Brain className="w-12 h-12 mb-6 text-premium-border" />
            <div className="text-white font-medium text-[16px] tracking-wide">No recommendations found</div>
            <p className="text-premium-subtext text-[14px] font-light mt-2 tracking-wide">Adjust your filters or run a new pricing analysis.</p>
          </div>
        ) : (
          recs.map((rec) => (
            <div key={rec.id} className="card p-6 slide-in">
              <div className="flex items-start gap-6">
                {/* Confidence Circle */}
                <div className="flex-shrink-0">
                  <div className={cn(
                    'w-16 h-16 rounded-2xl flex flex-col items-center justify-center text-center border border-white/5 shadow-inner-premium',
                    rec.confidence_score > 90 ? 'bg-emerald-500/10 text-emerald-400' :
                    rec.confidence_score > 70 ? 'bg-amber-500/10 text-amber-400' :
                    'bg-slate-500/10 text-slate-400'
                  )}>
                    <span className="text-[22px] font-light leading-none tracking-tight">{Math.round(rec.confidence_score)}</span>
                    <span className="text-[10px] uppercase font-medium tracking-widest mt-1 opacity-70">Conf</span>
                  </div>
                </div>

                {/* Main Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-medium text-[16px] text-white tracking-wide">{rec.product?.name}</span>
                        <span className="font-mono text-[11px] text-premium-subtext bg-premium-surface border border-premium-border px-2 py-0.5 rounded-md">{rec.product?.sku}</span>
                        <span className={cn('text-[10px] px-2 py-0.5 rounded-md font-medium uppercase tracking-widest border border-white/5', 
                          rec.status === 'pending' ? 'bg-amber-500/10 text-amber-400' :
                          rec.status === 'approved' || rec.status === 'auto_executed' ? 'bg-emerald-500/10 text-emerald-400' :
                          rec.status === 'rejected' ? 'bg-red-500/10 text-red-400' : 'bg-slate-500/10 text-slate-400'
                        )}>
                          {rec.status.replace('_', ' ')}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-4 text-[14px] mt-3 font-light">
                        <span className="text-premium-subtext">Current <span className="text-white font-medium ml-1">{formatCurrency(rec.current_price)}</span></span>
                        <div className="w-4 border-t border-premium-border border-dashed" />
                        <span className="text-premium-subtext">Target <span className="font-medium text-premium-accent ml-1">{formatCurrency(rec.recommended_price)}</span></span>
                        <span className={cn('flex items-center gap-1 font-medium text-[13px] ml-2',
                          rec.price_change_pct < 0 ? 'text-red-400' : 'text-emerald-400'
                        )}>
                          {rec.price_change_pct < 0 ? <TrendingDown className="w-3.5 h-3.5" /> : <TrendingUp className="w-3.5 h-3.5" />}
                          {formatPct(rec.price_change_pct)}
                        </span>
                      </div>

                      {rec.reasoning?.rationale && (
                        <p className="text-premium-subtext text-[14px] font-light mt-4 leading-relaxed max-w-3xl">{rec.reasoning.rationale}</p>
                      )}
                      <div className="text-[12px] font-light text-premium-subtext/60 mt-4 tracking-wide">{formatDate(rec.created_at)}</div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Link
                        href={`/recommendations/${rec.id}`}
                        className="flex items-center gap-1.5 text-[13px] font-medium text-white hover:bg-premium-surface border border-premium-border px-4 py-2 rounded-xl transition-all"
                      >
                        Details <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                      {rec.status === 'pending' && (
                         <>
                          <button
                            onClick={() => approve(rec.id)}
                            disabled={processing === rec.id}
                            className="flex items-center gap-2 text-[13px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 px-4 py-2 rounded-xl transition-all disabled:opacity-50"
                          >
                            <CheckCircle className="w-4 h-4" />
                            Approve
                          </button>
                          <button
                            onClick={() => setRejectModal({ id: rec.id })}
                            className="flex items-center gap-2 text-[13px] font-medium bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 px-4 py-2 rounded-xl transition-all"
                          >
                            <XCircle className="w-4 h-4" />
                            Reject
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Reject Modal */}
      {rejectModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-50 p-4">
          <div className="bg-premium-card border border-premium-border rounded-2xl p-8 w-full max-w-lg space-y-6 shadow-2xl">
            <div>
              <h2 className="text-[20px] font-medium text-white tracking-wide">Reject Recommendation</h2>
              <p className="text-premium-subtext text-[14px] font-light mt-1">Provide a reason to help the AI model improve future pricing suggestions.</p>
            </div>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={4}
              placeholder="e.g. Competitor data is outdated, our margin target is higher this month..."
              className="w-full bg-premium-surface border border-premium-border rounded-xl px-4 py-4 text-white placeholder-premium-subtext/50 text-[14px] font-light focus:outline-none focus:border-premium-subtext transition-colors resize-none shadow-inner-premium"
            />
            <div className="flex gap-3 pt-2">
              <button onClick={() => { setRejectModal(null); setRejectReason(''); }} className="flex-1 bg-premium-surface border border-premium-border py-3 rounded-xl text-[14px] font-medium text-white hover:bg-premium-border/50 transition-colors">Cancel</button>
              <button onClick={reject} className="flex-1 bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 py-3 rounded-xl text-[14px] font-medium transition-colors">Confirm Reject</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
