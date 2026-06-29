'use client';
import { useEffect, useState } from 'react';
import { productsApi, recommendationsApi } from '@/lib/api';
import { formatCurrency, formatPct, getStatusColor, cn } from '@/lib/utils';
import { Box, Search, Filter, Plus, ChevronRight, Zap, RefreshCcw } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const fetchProducts = async (currentPage = page, currentSearch = search) => {
    setLoading(true);
    try {
      const res = await productsApi.list({ page: currentPage, search: currentSearch, page_size: 20 });
      setProducts(res.data.items);
      setTotal(res.data.total);
    } catch {
      toast.error('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    
    const delayDebounceFn = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await productsApi.list({ page, search, page_size: 20 });
        if (active) {
          setProducts(res.data.items);
          setTotal(res.data.total);
          setLoading(false);
        }
      } catch {
        if (active) {
          toast.error('Failed to load products');
          setLoading(false);
        }
      }
    }, 300);

    return () => {
      active = false;
      clearTimeout(delayDebounceFn);
    };
  }, [search, page]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1); // Reset page on search
  };

  const generateRecs = async () => {
    if (products.length === 0) return;
    setGenerating(true);
    const toastId = toast.loading('Initializing Multi-Agent AI Analysis...');
    try {
      // Analyze only the first 2 visible products to prevent Groq rate limits
      const productIds = products.slice(0, 2).map(p => p.id);
      await recommendationsApi.generate(productIds);
      toast.success('AI recommendations generated successfully!', { id: toastId });
      fetchProducts(); // refresh status
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || err.message || 'AI Analysis failed';
      toast.error(`Error: ${errMsg}`, { id: toastId });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-3xl font-light text-white flex items-center gap-4 tracking-wide">
            <Box className="w-7 h-7 text-premium-accent" /> Product Catalog
          </h1>
          <p className="text-premium-subtext text-[15px] font-light mt-2 tracking-wide">
            {total} SKUs · View margins, inventory, and AI recommendation status.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-premium-subtext" />
            <input 
              type="text" 
              placeholder="Search SKUs or names..."
              value={search}
              onChange={handleSearch}
              className="pl-11 pr-4 py-3 bg-premium-card border border-premium-border rounded-xl text-[14px] font-light text-white shadow-inner-premium focus:outline-none focus:border-premium-subtext transition-all w-[300px] placeholder:text-premium-border"
            />
          </div>
          <button 
            onClick={generateRecs}
            disabled={generating || products.length === 0}
            className="flex items-center gap-2 bg-white hover:bg-gray-200 text-black px-6 py-3 rounded-xl font-medium text-[14px] transition-all disabled:opacity-50"
          >
            {generating ? <RefreshCcw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {generating ? 'Analyzing...' : 'Run AI Analysis'}
          </button>
        </div>
      </div>

      <div className="card overflow-hidden">
        {loading && products.length === 0 ? (
          <div className="p-8 space-y-4">
            {Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-12 bg-premium-surface border border-premium-border/50 rounded-xl animate-pulse" />)}
          </div>
        ) : products.length === 0 ? (
          <div className="p-20 text-center flex flex-col items-center justify-center">
            <Box className="w-12 h-12 mx-auto mb-4 text-premium-border" />
            <div className="text-white font-medium text-[16px] tracking-wide">No products found</div>
            <p className="text-premium-subtext text-[14px] font-light mt-2 tracking-wide">Adjust your search or add new SKUs to the catalog.</p>
          </div>
        ) : (
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-premium-border/50 bg-premium-surface">
                  <th className="px-6 py-4 text-[12px] font-medium text-premium-subtext uppercase tracking-widest">Product</th>
                  <th className="px-6 py-4 text-[12px] font-medium text-premium-subtext uppercase tracking-widest text-right">Price</th>
                  <th className="px-6 py-4 text-[12px] font-medium text-premium-subtext uppercase tracking-widest text-right">Cost (COGS)</th>
                  <th className="px-6 py-4 text-[12px] font-medium text-premium-subtext uppercase tracking-widest text-right">Margin</th>
                  <th className="px-6 py-4 text-[12px] font-medium text-premium-subtext uppercase tracking-widest text-right">Inventory</th>
                  <th className="px-6 py-4 text-[12px] font-medium text-premium-subtext uppercase tracking-widest text-center">AI Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-premium-border/50">
                {products.map((p) => {
                  const margin = ((p.current_price - p.cogs) / p.current_price) * 100;
                  const isLowStock = p.stock_qty <= p.reorder_point;
                  const status = p.recommendation_status || 'none';
                  
                  return (
                    <tr key={p.id} className="hover:bg-premium-surface/30 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-premium-surface border border-premium-border flex items-center justify-center flex-shrink-0 text-[10px] text-premium-subtext uppercase font-bold shadow-inner-premium">
                            {p.name.substring(0, 2)}
                          </div>
                          <div>
                            <div className="font-medium text-white text-[14px] tracking-wide group-hover:text-premium-accent transition-colors">{p.name}</div>
                            <div className="font-mono text-[11px] text-premium-subtext mt-0.5">{p.sku}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right font-medium text-[14px] text-white">
                        {formatCurrency(p.current_price)}
                      </td>
                      <td className="px-6 py-4 text-right font-light text-[14px] text-premium-subtext">
                        {formatCurrency(p.cogs)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={cn("text-[13px] font-medium px-2 py-1 rounded-md border",
                          margin < 15 ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        )}>
                          {formatPct(margin)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex flex-col items-end">
                          <span className={cn("text-[14px] font-medium", isLowStock ? 'text-amber-400' : 'text-white')}>
                            {p.stock_qty}
                          </span>
                          {isLowStock && <span className="text-[10px] text-amber-500/80 uppercase tracking-wider font-medium mt-0.5">Low Stock</span>}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={cn('text-[10px] px-2.5 py-1 rounded-md font-medium uppercase tracking-widest border border-white/5 inline-block min-w-[90px]', 
                          status === 'pending' ? 'bg-amber-500/10 text-amber-400' :
                          status === 'approved' || status === 'auto_executed' ? 'bg-emerald-500/10 text-emerald-400' :
                          status === 'rejected' ? 'bg-red-500/10 text-red-400' : 'bg-slate-500/10 text-slate-400'
                        )}>
                          {status.replace('_', ' ')}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {total > 20 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-premium-border bg-premium-surface">
            <span className="text-[13px] font-light text-premium-subtext">{total} products</span>
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
