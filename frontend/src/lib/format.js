export const fmtINR = (n) =>
  n == null ? "—" : `₹${Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const fmtPct = (n) => (n == null ? "—" : `${n > 0 ? "+" : ""}${Number(n).toFixed(2)}%`);

export const fmtNum = (n) =>
  n == null ? "—" : Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });

export const scoreTier = (s) => {
  if (s >= 80) return { label: "EXCELLENT", color: "text-emerald-400" };
  if (s >= 65) return { label: "STRONG", color: "text-emerald-300" };
  if (s >= 50) return { label: "MODERATE", color: "text-amber-400" };
  return { label: "WEAK", color: "text-slate-400" };
};

export const regimeStyle = (r) => {
  const map = {
    BULLISH: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    NEUTRAL: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    BEARISH: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  };
  return map[r] || map.NEUTRAL;
};

export const statusStyle = (s) => {
  const map = {
    MONITORING: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    T1_HIT: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    T2_HIT: "bg-emerald-500/20 text-emerald-300 border-emerald-500/50",
    STOP_LOSS_HIT: "bg-rose-500/15 text-rose-300 border-rose-500/40",
    INVALIDATED: "bg-slate-500/10 text-slate-400 border-slate-500/30",
    CLOSED: "bg-slate-500/10 text-slate-400 border-slate-500/30",
  };
  return map[s] || map.MONITORING;
};
