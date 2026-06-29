import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value);
}

export function formatPct(value: number, decimals = 1): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

export function getConfidenceColor(score: number): string {
  if (score >= 80) return 'text-emerald-400';
  if (score >= 60) return 'text-amber-400';
  return 'text-red-400';
}

export function getConfidenceBg(score: number): string {
  if (score >= 80) return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
  if (score >= 60) return 'bg-amber-500/20 text-amber-300 border border-amber-500/30';
  return 'bg-red-500/20 text-red-300 border border-red-500/30';
}

export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    pending: 'bg-amber-500/20 text-amber-300 border border-amber-500/30',
    approved: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
    rejected: 'bg-red-500/20 text-red-300 border border-red-500/30',
    auto_executed: 'bg-brand-500/20 text-brand-300 border border-brand-500/30',
    modified: 'bg-purple-500/20 text-purple-300 border border-purple-500/30',
  };
  return map[status] || 'bg-slate-700 text-slate-300';
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}
