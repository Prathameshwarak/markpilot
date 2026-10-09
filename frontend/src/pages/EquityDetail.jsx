import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import api from "../lib/api";
import usePolling from "../hooks/usePolling";
import { PageHeader, Card } from "../components/Primitives";
import { ScoreGauge } from "../components/Score";
import { ScoreBreakdown } from "../components/Score";
import { fmtINR } from "../lib/format";

export default function EquityDetail() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  const load = useCallback(() => {
    api.get(`/equities/${symbol}/research`).then((r) => setData(r.data)).catch(() => {});
  }, [symbol]);
  useEffect(() => { load(); }, [load]);
  usePolling(load, 30000);

  const monitor = async () => {
    try {
      await api.post(`/trade-ideas/idea-${symbol}/monitor`);
      toast.success(`Added ${symbol} to My Monitoring`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not start monitoring");
    }
  };

  if (!data) return <div className="py-20 text-center text-sm text-slate-500">Loading research…</div>;

  const ind = data.indicators;
  const f = data.fundamentals;
  const fundRows = [
    ["Revenue Growth", f.revenue_growth, "%"], ["Profit Growth", f.profit_growth, "%"],
    ["EPS Growth", f.eps_growth, "%"], ["ROE", f.roe, "%"], ["ROCE", f.roce, "%"],
    ["Debt/Equity", f.debt_equity, ""], ["P/E", f.pe, ""], ["P/B", f.pb, ""],
  ];

  return (
    <div>
      <button onClick={() => navigate(-1)} className="mb-4 flex items-center gap-1 text-sm text-slate-400 hover:text-slate-100" data-testid="detail-back-button">
        <ArrowLeft size={16} /> Back
      </button>
      <PageHeader
        title={`${data.symbol}`}
        subtitle={`${data.company} · ${data.sector}`}
        right={
          <button onClick={monitor} data-testid={`detail-monitor-button-${symbol}`} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500">
            Monitor This Idea
          </button>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <h2 className="mb-3 font-display text-lg font-bold">Price (last 60 sessions)</h2>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={data.chart}>
                <defs>
                  <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="i" hide />
                <YAxis domain={["auto", "auto"]} tick={{ fill: "#64748B", fontSize: 11 }} width={50} />
                <Tooltip contentStyle={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 8, color: "#F8FAFC" }} />
                <Area type="monotone" dataKey="close" stroke="#3B82F6" strokeWidth={2} fill="url(#g)" />
              </AreaChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <h2 className="mb-3 font-display text-lg font-bold">Technical Signals</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                ["RSI 14", ind.rsi], ["EMA 20", ind.ema20], ["EMA 50", ind.ema50], ["ATR 14", ind.atr],
                ["Vol Ratio", ind.volume_ratio], ["Momentum %", ind.momentum], ["Support", ind.support], ["Resistance", ind.resistance],
              ].map(([l, v]) => (
                <div key={l} className="rounded-lg bg-slate-900/60 px-3 py-2">
                  <div className="text-[10px] uppercase tracking-wider text-slate-500">{l}</div>
                  <div className="font-num text-sm font-semibold text-slate-200">{v ?? "—"}</div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <h2 className="mb-3 font-display text-lg font-bold">Fundamentals <span className="text-[10px] font-normal uppercase tracking-wider text-amber-500">MOCK DATA</span></h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {fundRows.map(([l, v, u]) => (
                <div key={l} className="rounded-lg bg-slate-900/60 px-3 py-2">
                  <div className="text-[10px] uppercase tracking-wider text-slate-500">{l}</div>
                  <div className="font-num text-sm font-semibold text-slate-200">{v == null ? "Data unavailable" : `${v}${u}`}</div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <h2 className="mb-3 font-display text-lg font-bold">Recent News &amp; Sentiment</h2>
            <div className="space-y-2">
              {data.news.map((n, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg bg-slate-900/60 px-3 py-2">
                  <div>
                    <div className="text-sm text-slate-200">{n.headline}</div>
                    <div className="text-[11px] text-slate-500">{n.source} · {new Date(n.timestamp).toLocaleString()}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="flex flex-col items-center">
            <h2 className="mb-3 font-display text-lg font-bold">Opportunity Score</h2>
            <ScoreGauge score={data.opportunity.total} size={120} />
            <div className="mt-5 w-full">
              <ScoreBreakdown opportunity={data.opportunity} />
            </div>
          </Card>
          <Card>
            <h2 className="mb-3 font-display text-lg font-bold">Trade Levels</h2>
            {[
              ["Entry", data.levels.entry, "text-slate-100"],
              ["Stop Loss", data.levels.stop_loss, "text-rose-400"],
              ["Target 1", data.levels.target1, "text-emerald-400"],
              ["Target 2", data.levels.target2, "text-emerald-400"],
              ["Risk / Reward", `1:${data.levels.risk_reward}`, "text-cyan-400"],
            ].map(([l, v, c]) => (
              <div key={l} className="flex items-center justify-between border-b border-slate-800 py-2 last:border-0">
                <span className="text-xs text-slate-400">{l}</span>
                <span className={`font-num text-sm font-semibold ${c}`}>{typeof v === "number" ? fmtINR(v) : v}</span>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
