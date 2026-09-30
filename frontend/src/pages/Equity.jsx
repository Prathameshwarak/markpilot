import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../lib/api";
import { PageHeader, Card } from "../components/Primitives";
import { ChangePill } from "../components/Score";
import { fmtINR, fmtNum, scoreTier } from "../lib/format";

export default function Equity() {
  const navigate = useNavigate();
  const [equities, setEquities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sector, setSector] = useState("all");
  const [dir, setDir] = useState("all");
  const [minScore, setMinScore] = useState(0);

  useEffect(() => {
    api.get("/equities").then((r) => setEquities(r.data.equities)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const sectors = useMemo(() => ["all", ...new Set(equities.map((e) => e.sector))], [equities]);

  const filtered = equities
    .filter((e) => (sector === "all" ? true : e.sector === sector))
    .filter((e) => (dir === "all" ? true : e.direction === dir))
    .filter((e) => e.scores.overall >= minScore)
    .sort((a, b) => b.scores.overall - a.scores.overall);

  return (
    <div>
      <PageHeader
        title="Equity Research"
        subtitle={`${equities.length} liquid large-cap Indian equities — scanner`}
        right={
          equities[0] && (
            <span
              data-testid="equity-data-badge"
              className={`rounded-md border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ${
                equities[0].data_source === "kotak"
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                  : "border-amber-500/30 bg-amber-500/10 text-amber-400"
              }`}
            >
              {equities[0].data_source === "kotak" ? (equities[0].is_live ? "Live" : "Stale") : "Demo Data"}
            </span>
          )
        }
      />

      {/* Filters */}
      <Card className="mb-5">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-wider text-slate-500">Sector</label>
            <select
              value={sector} onChange={(e) => setSector(e.target.value)} data-testid="filter-sector-select"
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              {sectors.map((s) => <option key={s} value={s}>{s === "all" ? "All Sectors" : s}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-wider text-slate-500">Bias</label>
            <select
              value={dir} onChange={(e) => setDir(e.target.value)} data-testid="filter-direction-select"
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              <option value="all">All</option>
              <option value="bullish">Bullish</option>
              <option value="bearish">Bearish</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-wider text-slate-500">Min Score: {minScore}</label>
            <input
              type="range" min="0" max="100" value={minScore} onChange={(e) => setMinScore(Number(e.target.value))}
              data-testid="filter-score-range" className="w-40 accent-blue-500"
            />
          </div>
        </div>
      </Card>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm" data-testid="equity-table">
          <thead className="sticky top-0 bg-slate-900/80 backdrop-blur-md">
            <tr className="text-[10px] uppercase tracking-wider text-slate-500">
              <th className="px-4 py-3">Symbol</th>
              <th className="px-4 py-3">Sector</th>
              <th className="px-4 py-3 text-right">Price</th>
              <th className="px-4 py-3 text-right">Chg</th>
              <th className="px-4 py-3 text-right">RSI</th>
              <th className="px-4 py-3 text-right">Tech</th>
              <th className="px-4 py-3 text-right">Fund</th>
              <th className="px-4 py-3 text-right">Sent</th>
              <th className="px-4 py-3 text-right">Sect</th>
              <th className="px-4 py-3 text-right">Score</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={10} className="px-4 py-12 text-center text-sm text-slate-500" data-testid="equity-loading">Loading equities…</td></tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr><td colSpan={10} className="px-4 py-12 text-center text-sm text-slate-500">No equities match the filters.</td></tr>
            )}
            {filtered.map((e) => {
              const tier = scoreTier(e.scores.overall);
              return (
                <tr
                  key={e.symbol}
                  onClick={() => navigate(`/equity/${e.symbol}`)}
                  data-testid={`equity-row-${e.symbol}`}
                  className="cursor-pointer border-t border-slate-800 transition-colors hover:bg-slate-800/50"
                >
                  <td className="px-4 py-3">
                    <div className="font-display font-bold">{e.symbol}</div>
                    <div className="text-[11px] text-slate-500">{e.company}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{e.sector}</td>
                  <td className="px-4 py-3 text-right font-num">{fmtINR(e.price)}</td>
                  <td className="px-4 py-3 text-right"><ChangePill value={e.change_pct} /></td>
                  <td className="px-4 py-3 text-right font-num text-slate-300">{e.indicators.rsi ?? "—"}</td>
                  <td className="px-4 py-3 text-right font-num text-slate-300">{e.scores.technical}</td>
                  <td className="px-4 py-3 text-right font-num text-slate-300">{e.scores.fundamental}</td>
                  <td className="px-4 py-3 text-right font-num text-slate-300">{e.scores.sentiment}</td>
                  <td className="px-4 py-3 text-right font-num text-slate-300">{e.scores.sector}</td>
                  <td className={`px-4 py-3 text-right font-num font-bold ${tier.color}`}>{e.scores.overall}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
