import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// FastAPI `detail` kan string of 422-lijst zijn; altijd een leesbare string teruggeven
export function apiError(r, fallback = 'Er ging iets mis') {
  const d = r?.detail ?? r?.message ?? r?.error;
  if (!d) return fallback;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map(e => `${(e.loc || []).slice(1).join('.')}: ${e.msg}`).join(' · ') || fallback;
  return fallback;
}
