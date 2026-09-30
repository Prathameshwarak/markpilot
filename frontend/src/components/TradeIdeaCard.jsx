import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Check, TriangleAlert, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { fmtINR } from "../lib/format";
import { ScoreGauge } from "./Score";
import api from "../lib/api";

export function TradeIdeaCard({ idea, onMonitored }) {
  const navigate = useNavigate();
  const bullish = idea.direction === "bullish";

  const monitor = async () => {
    try {
      await api.post(`/trade-ideas/${idea.id}/monitor`);
      toast.success(`Added ${idea.symbol} to My Monitoring`);
      onMonitored?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not start monitoring");
    }
  };

  return (
    <div
      className="mp-fade-up flex flex-col rounded-xl border border-slate-800 bg-[#111827] p-5 transition-colors hover:border-slate-700"
      data-testid={`trade-idea-card-${idea.symbol}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-display text-lg font-bold">{idea.symbol}</h3>
            <span
              className={`flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-semibold ${
                bullish
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                  : "border-rose-500/30 bg-rose-500/10 text-rose-400"
              }`}
            >
              {bullish ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
              {idea.direction_label} {idea.idea_type}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">{idea.company}</p>
        </div>
        <ScoreGauge score={idea.score} size={72} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { l: "Entry", v: idea.entry, c: "text-slate-100" },
          { l: "Stop Loss", v: idea.stop_loss, c: "text-rose-400" },
          { l: "Target 1", v: idea.target1, c: "text-emerald-400" },
          { l: "Target 2", v: idea.target2, c: "text-emerald-400" },
        ].map((x) => (
          <div key={x.l} className="rounded-lg bg-slate-900/60 px-3 py-2">
            <div className="text-[10px] uppercase tracking-wider text-slate-500">{x.l}</div>
            <div className={`font-num text-sm font-semibold ${x.c}`}>{fmtINR(x.v)}</div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex items-center justify-between rounded-lg border border-slate-800 px-3 py-2">
        <span className="text-xs text-slate-400">Risk / Reward</span>
        <span className="font-num text-sm font-bold text-cyan-400">1:{idea.risk_reward}</span>
        <span className="text-[11px] text-slate-500">{idea.rr_flag}</span>
      </div>

      <div className="mt-4">
        <div className="mb-1.5 text-xs font-semibold text-slate-300">Why this idea?</div>
        <ul className="space-y-1">
          {idea.why.map((r, i) => (
            <li key={i} className="flex items-center gap-2 text-xs text-slate-400">
              <Check size={13} className="text-emerald-400" /> {r}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-3">
        <div className="mb-1.5 text-xs font-semibold text-slate-300">Risks</div>
        <ul className="space-y-1">
          {idea.risks.map((r, i) => (
            <li key={i} className="flex items-center gap-2 text-xs text-slate-400">
              <TriangleAlert size={13} className="text-amber-400" /> {r}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          onClick={() => navigate(`/equity/${idea.symbol}`)}
          data-testid={`view-analysis-button-${idea.symbol}`}
          className="flex-1 rounded-lg border border-slate-700 py-2 text-xs font-semibold text-slate-300 transition-colors hover:bg-slate-800"
        >
          View Full Analysis
        </button>
        <button
          onClick={monitor}
          data-testid={`monitor-idea-button-${idea.symbol}`}
          className="flex-1 rounded-lg bg-emerald-600 py-2 text-xs font-semibold text-white transition-colors hover:bg-emerald-500"
        >
          Monitor This Idea
        </button>
      </div>
      <p className="mt-3 text-[10px] leading-relaxed text-slate-600">{idea.disclaimer}</p>
    </div>
  );
}
