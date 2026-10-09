import { fmtPct } from "../lib/format";

export function ScoreBreakdown({ opportunity, compact = false }) {
  if (!opportunity) return null;
  const items = [
    { key: "technical", label: "Technical" },
    { key: "fundamental", label: "Fundamental" },
    { key: "sentiment", label: "Sentiment" },
    { key: "sector", label: "Sector" },
    { key: "risk_reward", label: "Risk / Reward" },
  ];
  return (
    <div className="space-y-2.5" data-testid="score-breakdown">
      {items.map((it) => {
        const c = opportunity.breakdown[it.key];
        const pct = (c.score / c.max) * 100;
        return (
          <div key={it.key}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="text-slate-400">{it.label}</span>
              <span className="font-num font-semibold text-slate-200">
                {c.score}/{c.max}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function ScoreGauge({ score, size = 96 }) {
  const r = 42;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#10B981" : score >= 65 ? "#22D3EE" : score >= 50 ? "#F59E0B" : "#64748B";
  return (
    <div className="relative" style={{ width: size, height: size }} data-testid="opportunity-score-badge">
      <svg width={size} height={size} viewBox="0 0 100 100" className="-rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#1E293B" strokeWidth="8" />
        <circle
          cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-num text-2xl font-bold" style={{ color }}>{score}</span>
        <span className="text-[10px] uppercase tracking-wider text-slate-500">/ 100</span>
      </div>
    </div>
  );
}

export function ChangePill({ value }) {
  const up = value >= 0;
  return (
    <span className={`font-num text-sm font-semibold ${up ? "text-emerald-400" : "text-rose-400"}`}>
      {fmtPct(value)}
    </span>
  );
}
