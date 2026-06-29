'use client';
import { useEffect, useState } from 'react';
import { auditApi } from '@/lib/api';
import { formatCurrency, formatPct, cn, formatDate } from '@/lib/utils';
import { History, TrendingDown, TrendingUp, CheckCircle, XCircle, Zap } from 'lucide-react';

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await auditApi.list({ page });
        setLogs(res.data.items);
        setTotal(res.data.total);
      } finally { setLoading(false); }
    })();
  }, [page]);

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      <div>
        <h1 className="text-3xl font-light text-white flex items-center gap-4 tracking-wide">
          <History className="w-7 h-7 text-premium-accent" /> Audit Trail
        </h1>
        <p className="text-premium-subtext text-[15px] font-light mt-2 tracking-wide">
          {total} price change events · Full accountability log
        </p>
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-16 bg-premium-surface border border-premium-border/50 rounded-xl animate-pulse" />)}
          </div>
        ) : logs.length === 0 ? (
          <div className="p-20 text-center flex flex-col items-center justify-center">
            <History className="w-12 h-12 mx-auto mb-4 text-premium-border" />
            <div className="text-white font-medium text-[16px] tracking-wide">No audit events yet</div>
            <p className="text-premium-subtext text-[14px] font-light mt-2 tracking-wide">AI pricing actions will appear here once executed.</p>
          </div>
        ) : (
          <div className="divide-y divide-premium-border/50">
            {logs.map((log: any) => (
              <div key={log.id} className="p-5 hover:bg-premium-surface/30 transition-colors slide-in">
                <div className="flex items-center gap-5">
                  {/* Status Icon */}
                  <div className={cn(
                    'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 border shadow-inner-premium',
                    log.execution_status === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                    log.execution_status === 'failed' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                    'bg-amber-500/10 border-amber-500/20 text-amber-400'
                  )}>
                    {log.execution_status === 'success' ? <CheckCircle className="w-4 h-4" /> :
                     log.execution_status === 'failed' ? <XCircle className="w-4 h-4" /> :
                     <History className="w-4 h-4" />}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="font-medium text-white text-[15px] tracking-wide">{log.product?.name}</span>
                      <span className="font-mono text-[11px] text-premium-subtext bg-premium-surface border border-premium-border px-2 py-0.5 rounded-md">{log.product?.sku}</span>
                    </div>
                    <div className="flex items-center gap-4 text-[13px] font-light text-premium-subtext mt-2">
                      <span>{formatCurrency(log.previous_price)} → <span className="text-white font-medium ml-1">{formatCurrency(log.new_price)}</span></span>
                      <span className={cn('font-medium flex items-center gap-1',
                        log.change_pct < 0 ? 'text-red-400' : 'text-emerald-400'
                      )}>
                        {log.change_pct < 0 ? <TrendingDown className="w-3.5 h-3.5" /> : <TrendingUp className="w-3.5 h-3.5" />}
                        {formatPct(log.change_pct)}
                      </span>
                      <div className="w-1 h-1 rounded-full bg-premium-border" />
                      <span>
                        {log.executed_by === 'auto' ? (
                          <span className="flex items-center gap-1.5"><Zap className="w-3.5 h-3.5 text-premium-accent" />Auto-executed</span>
                        ) : `Approved by analyst`}
                      </span>
                      {log.confidence_score && (
                        <>
                          <div className="w-1 h-1 rounded-full bg-premium-border" />
                          <span className="text-premium-subtext">AI Conf: {log.confidence_score.toFixed(1)}%</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="text-[12px] font-light text-premium-subtext flex-shrink-0 tracking-wide">{formatDate(log.created_at)}</div>
                </div>
                {log.error_message && (
                  <div className="mt-3 ml-[60px] text-[13px] font-light text-red-400 bg-red-500/10 border border-red-500/20 px-4 py-2 rounded-xl">
                    {log.error_message}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {total > 20 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-premium-border bg-premium-surface">
            <span className="text-[13px] font-light text-premium-subtext">{total} events</span>
            <div className="flex items-center gap-3">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="px-4 py-2 bg-premium-card border border-premium-border hover:bg-white/5 rounded-lg text-[13px] font-medium disabled:opacity-40 text-white transition-colors shadow-inner-premium">Prev</button>
              <span className="px-3 text-[13px] font-light text-premium-subtext">Page {page}</span>
              <button disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)} className="px-4 py-2 bg-premium-card border border-premium-border hover:bg-white/5 rounded-lg text-[13px] font-medium disabled:opacity-40 text-white transition-colors shadow-inner-premium">Next</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
