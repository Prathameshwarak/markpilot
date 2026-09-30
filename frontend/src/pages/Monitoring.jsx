import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { RefreshCw, X } from "lucide-react";
import api from "../lib/api";
import { PageHeader, Card, Empty } from "../components/Primitives";
import { statusStyle, fmtINR } from "../lib/format";

function ProximityBar({ session }) {
  const { entry, current_stop, target1, direction } = session;
  const lo = Math.min(current_stop, target1);
  const hi = Math.max(current_stop, target1);
  const pos = Math.max(0, Math.min(100, ((entry - lo) / (hi - lo)) * 100));
  return (
    <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
      <div className="h-full rounded-full bg-gradient-to-r from-rose-500 via-amber-400 to-emerald-500" style={{ width: `${pos}%` }} />
    </div>
  );
}

export default function Monitoring() {
  const [sessions, setSessions] = useState([]);
  const [filter, setFilter] = useState("all");
  const [expanded, setExpanded] = useState(null);

  const load = useCallback(() => {
    api.get("/monitoring").then((r) => setSessions(r.data.sessions)).catch(() => {});
  }, []);
  useEffect(() => { load(); }, [load]);

  const refresh = async (id) => {
    try {
      const { data } = await api.post(`/monitoring/${id}/refresh`);
      if (data.new_events.length) toast.success(`${data.new_events.length} new event(s)`);
      else toast("No change at current price");
      load();
    } catch { toast.error("Refresh failed"); }
  };

  const close = async (id) => {
    try { await api.post(`/monitoring/${id}/close`); toast.success("Monitoring closed"); load(); }
    catch { toast.error("Close failed"); }
  };

  const filtered = sessions.filter((s) => (filter === "all" ? true : s.status === filter));
  const STATUSES = ["all", "MONITORING", "T1_HIT", "T2_HIT", "STOP_LOSS_HIT", "CLOSED"];

  return (
    <div>
      <PageHeader title="My Monitoring" subtitle="Manually selected ideas — MarketPilot never places orders" />
      <div className="mb-5 flex flex-wrap gap-2">
        {STATUSES.map((s) => (
          <button
            key={s} onClick={() => setFilter(s)} data-testid={`monitoring-filter-${s}`}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium ${filter === s ? "border-blue-500 bg-blue-600/15 text-blue-400" : "border-slate-800 text-slate-400 hover:bg-slate-800"}`}
          >
            {s === "all" ? "All" : s}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <Empty message="No monitored ideas. Go to Trade Ideas and click 'Monitor This Idea'." testId="monitoring-empty" />
      ) : (
        <div className="space-y-3">
          {filtered.map((s) => (
            <Card key={s.id} data-testid={`monitoring-session-${s.symbol}`}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-display text-lg font-bold">{s.symbol}</span>
                    <span className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold ${statusStyle(s.status)}`}>{s.status}</span>
                    <span className={`text-[11px] ${s.direction === "bullish" ? "text-emerald-400" : "text-rose-400"}`}>{s.direction}</span>
                  </div>
                  <div className="mt-0.5 text-xs text-slate-500">{s.company}</div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => refresh(s.id)} data-testid={`refresh-session-${s.symbol}`} className="flex items-center gap-1 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800">
                    <RefreshCw size={13} /> Re-evaluate
                  </button>
                  {!["CLOSED", "STOP_LOSS_HIT", "T2_HIT"].includes(s.status) && (
                    <button onClick={() => close(s.id)} data-testid={`close-session-${s.symbol}`} className="flex items-center gap-1 rounded-lg border border-rose-500/30 px-3 py-1.5 text-xs text-rose-400 hover:bg-rose-500/10">
                      <X size={13} /> Close
                    </button>
                  )}
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
                {[
                  ["Entry", s.entry, "text-slate-100"], ["Orig Stop", s.original_stop, "text-slate-400"],
                  ["Current Stop", s.current_stop, "text-rose-400"], ["Target 1", s.target1, "text-emerald-400"],
                  ["Target 2", s.target2, "text-emerald-400"],
                ].map(([l, v, c]) => (
                  <div key={l} className="rounded-lg bg-slate-900/60 px-3 py-2">
                    <div className="text-[10px] uppercase tracking-wider text-slate-500">{l}</div>
                    <div className={`font-num text-sm font-semibold ${c}`}>{fmtINR(v)}</div>
                  </div>
                ))}
              </div>
              <ProximityBar session={s} />

              <button onClick={() => setExpanded(expanded === s.id ? null : s.id)} className="mt-3 text-xs text-blue-400" data-testid={`toggle-events-${s.symbol}`}>
                {expanded === s.id ? "Hide" : "Show"} events ({s.events?.length || 0})
              </button>
              {expanded === s.id && (
                <div className="mt-2 space-y-1.5">
                  {s.events.map((e, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg bg-slate-900/60 px-3 py-1.5 text-xs">
                      <span className="text-slate-300">{e.message}</span>
                      <span className="text-[10px] text-slate-600">{new Date(e.timestamp).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
