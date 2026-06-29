'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { recommendationsApi } from '@/lib/api';
import { formatCurrency, formatPct, getConfidenceBg, getStatusColor, cn, formatDate } from '@/lib/utils';
import {
  Brain, TrendingDown, TrendingUp, ArrowLeft, CheckCircle,
  XCircle, Edit3, Database, Activity, Package, BarChart2, ShieldCheck
} from 'lucide-react';
import toast from 'react-hot-toast';

const AGENT_ICONS: Record<string, any> = {
  'Market Intelligence Agent': Activity,
  'Demand Forecasting Agent': BarChart2,
  'Inventory & Cost Agent': Package,
  'Pricing Strategy Agent': Brain,
  'Execution & Compliance Agent': ShieldCheck,
};

export default function RecommendationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [rec, setRec] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [modifyPrice, setModifyPrice] = useState('');
  const [showModify, setShowModify] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [showReject, setShowReject] = useState(false);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await recommendationsApi.get(id);
        setRec(res.data);
        setModifyPrice(res.data.recommended_price.toFixed(2));
      } catch { toast.error('Recommendation not found'); router.push('/recommendations'); }
      finally { setLoading(false); }
    })();
  }, [id]);

  const approve = async () => {
    setProcessing(true);
    try {
      await recommendationsApi.approve(id);
      toast.success('Approved and executed!');
      router.push('/recommendations');
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed'); } finally { setProcessing(false); }
  };

  const reject = async () => {
    if (rejectReason.length < 5) { toast.error('Reason too short'); return; }
    setProcessing(true);
    try {
      await recommendationsApi.reject(id, rejectReason);
      toast.success('Rejected');
      router.push('/recommendations');
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed'); } finally { setProcessing(false); }
  };

  const modify = async () => {
    const price = parseFloat(modifyPrice);
    if (isNaN(price) || price <= 0) { toast.error('Invalid price'); return; }
    setProcessing(true);
    try {
      await recommendationsApi.modify(id, price);
      toast.success(`Price set to ${formatCurrency(price)}`);
      router.push('/recommendations');
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed'); } finally { setProcessing(false); }
  };

  if (loading) return (
    <div className="space-y-4">
      {Array.from({ length: 4 }).map((_, i) => <div key={i} className="glass rounded-xl h-32 animate-pulse" />)}
    </div>
  );
  if (!rec) return null;

  const agentOutputs: any[] = rec.agent_outputs || [];
  const dataSources: any[] = rec.data_sources || [];

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Back */}
      <button onClick={() => router.back()} className="flex items-center gap-2 text-slate-400 hover:text-slate-200 text-sm transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Recommendations
      </button>

      {/* Hero Card */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-xl font-bold text-slate-100">{rec.product?.name}</h1>
              <span className="font-mono text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">{rec.product?.sku}</span>
              <span className={cn('text-xs px-2 py-1 rounded-lg font-semibold', getStatusColor(rec.status))}>
                {rec.status.replace('_', ' ')}
              </span>
            </div>
            <p className="text-slate-400 text-sm">{rec.product?.category?.name}</p>
          </div>
          <div className={cn('text-center px-5 py-3 rounded-xl', getConfidenceBg(rec.confidence_score))}>
            <div className="text-3xl font-black">{Math.round(rec.confidence_score)}</div>
            <div className="text-xs opacity-70 mt-0.5">Confidence</div>
          </div>
        </div>

        {/* Price Summary */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          {[
            { label: 'Current Price', value: formatCurrency(rec.current_price), sub: 'Live price' },
            {
              label: 'AI Recommendation', value: formatCurrency(rec.recommended_price),
              sub: formatPct(rec.price_change_pct), bold: true,
              subColor: rec.price_change_pct < 0 ? 'text-red-400' : 'text-emerald-400'
            },
            { label: 'Created', value: formatDate(rec.created_at), sub: 'By AI pipeline' },
          ].map((item) => (
            <div key={item.label} className="bg-slate-800/40 rounded-xl p-4">
              <div className="text-xs text-slate-500 mb-1">{item.label}</div>
              <div className={cn('text-lg font-bold', item.bold ? 'text-slate-100' : 'text-slate-200')}>{item.value}</div>
              <div className={cn('text-xs mt-0.5', item.subColor || 'text-slate-500')}>{item.sub}</div>
            </div>
          ))}
        </div>

        {/* Confidence Bar */}
        <div className="mt-4 flex items-center gap-3">
          <span className="text-xs text-slate-500 w-20">Confidence</span>
          <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full confidence-bar" style={{ width: `${rec.confidence_score}%` }} />
          </div>
          <span className="text-xs text-slate-400 w-12 text-right">{rec.confidence_score.toFixed(1)}%</span>
        </div>
      </div>

      {/* Final Rationale */}
      <div className="glass rounded-xl p-5">
        <h2 className="font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <Brain className="w-4 h-4 text-brand-400" /> AI Rationale
        </h2>
        <p className="text-slate-300 text-sm leading-relaxed">
          {rec.reasoning?.rationale || 'No rationale available.'}
        </p>
        {rec.reasoning?.risk_factors?.length > 0 && (
          <div className="mt-3">
            <div className="text-xs text-slate-500 mb-2">Risk Factors</div>
            <div className="flex flex-wrap gap-2">
              {rec.reasoning.risk_factors.map((r: string, i: number) => (
                <span key={i} className="text-xs bg-red-500/10 text-red-300 border border-red-500/20 px-2 py-1 rounded-lg">{r}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Agent Outputs Accordion */}
      {agentOutputs.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold text-slate-200 flex items-center gap-2">
            <Activity className="w-4 h-4 text-brand-400" /> Agent Contributions
          </h2>
          {agentOutputs.map((agent: any, i: number) => {
            const Icon = AGENT_ICONS[agent.agent_name] || Brain;
            return (
              <details key={i} className="glass rounded-xl group">
                <summary className="flex items-center gap-3 p-4 cursor-pointer list-none hover:bg-slate-800/30 rounded-xl transition-colors">
                  <div className="w-8 h-8 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-4 h-4 text-brand-400" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-slate-200 text-sm">{agent.agent_name}</div>
                    <div className="text-xs text-slate-500 line-clamp-1">{agent.summary}</div>
                  </div>
                  {agent.confidence_contribution && (
                    <span className={cn('text-xs font-semibold px-2 py-1 rounded-lg', getConfidenceBg(agent.confidence_contribution * 4))}>
                      +{agent.confidence_contribution?.toFixed(1)}pts
                    </span>
                  )}
                </summary>
                <div className="px-4 pb-4 border-t border-slate-800/50 mt-1">
                  <div className="pt-3 text-sm text-slate-300 leading-relaxed">{agent.summary}</div>
                  {agent.data_points && Object.keys(agent.data_points).length > 0 && (
                    <div className="mt-3 bg-slate-900/50 rounded-lg p-3">
                      <div className="text-xs text-slate-500 mb-2">Raw Data</div>
                      <pre className="text-xs text-slate-400 overflow-auto max-h-40">
                        {JSON.stringify(agent.data_points, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            );
          })}
        </div>
      )}

      {/* Data Sources */}
      {dataSources.length > 0 && (
        <div className="glass rounded-xl p-5">
          <h2 className="font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <Database className="w-4 h-4 text-brand-400" /> Data Sources
          </h2>
          <div className="space-y-2">
            {dataSources.map((src: any, i: number) => (
              <div key={i} className="flex items-center justify-between text-sm py-2 border-b border-slate-800/40 last:border-0">
                <span className="text-slate-300">{src.source}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded">{src.type}</span>
                  <div className="w-20 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-brand-500" style={{ width: `${(src.weight || 0.5) * 100}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Panel */}
      {rec.status === 'pending' && (
        <div className="glass rounded-xl p-5 border border-amber-500/20">
          <h2 className="font-semibold text-slate-200 mb-4">Analyst Decision</h2>
          <div className="flex flex-wrap gap-3">
            <button id="detail-approve-btn" onClick={approve} disabled={processing}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50 transition-all">
              <CheckCircle className="w-4 h-4" /> Approve {formatCurrency(rec.recommended_price)}
            </button>
            <button id="modify-toggle-btn" onClick={() => setShowModify(!showModify)}
              className="flex items-center gap-2 glass text-slate-200 px-5 py-2.5 rounded-xl text-sm font-semibold hover:border-brand-500/50 transition-all">
              <Edit3 className="w-4 h-4" /> Modify Price
            </button>
            <button id="reject-toggle-btn" onClick={() => setShowReject(!showReject)}
              className="flex items-center gap-2 bg-red-600/20 text-red-300 border border-red-500/30 hover:bg-red-600/30 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all">
              <XCircle className="w-4 h-4" /> Reject
            </button>
          </div>

          {showModify && (
            <div className="mt-4 flex items-center gap-3">
              <span className="text-sm text-slate-400">New Price: $</span>
              <input
                id="modify-price-input"
                type="number"
                step="0.01"
                min="0.01"
                value={modifyPrice}
                onChange={(e) => setModifyPrice(e.target.value)}
                className="w-28 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:border-brand-500"
              />
              <button id="confirm-modify-btn" onClick={modify} disabled={processing}
                className="bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50">
                Execute
              </button>
            </div>
          )}

          {showReject && (
            <div className="mt-4 space-y-2">
              <textarea
                id="detail-reject-reason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={2}
                placeholder="Reason for rejection (min 5 chars)..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:border-red-500 resize-none"
              />
              <button id="confirm-detail-reject-btn" onClick={reject} disabled={processing}
                className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50">
                Confirm Reject
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
