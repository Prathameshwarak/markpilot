import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, Bell, Zap, TrendingUp } from "lucide-react";
import api from "../lib/api";
import { PageHeader, Card, Empty } from "../components/Primitives";
import { ScoreGauge, ChangePill } from "../components/Score";
import { fmtPct, regimeStyle, statusStyle } from "../lib/format";

export default function Dashboard() {
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [tops, setTops] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    api.get("/market/overview").then((r) => setOverview(r.data)).catch(() => {});
    api.get("/trade-ideas").then((r) => setTops(r.data.ideas.slice(0, 3))).catch(() => {});
    api.get("/monitoring").then((r) => setSessions(r.data.sessions)).catch(() => {});
    api.get("/alerts").then((r) => setAlerts(r.data.alerts.slice(0, 6))).catch(() => {});
  }, []);

  const regime = overview?.regime?.regime || "NEUTRAL";
  const active = sessions.filter((s) => !["CLOSED", "STOP_LOSS_HIT", "T2_HIT"].includes(s.status));

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Indian equity research overview"
        right={
          overview && (
            <span
              data-testid="dashboard-data-badge"
              className={`rounded-md border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ${
                overview.data_source === "kotak"
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                  : "border-amber-500/30 bg-amber-500/10 text-amber-400"
              }`}
            >
              {overview.data_source === "kotak" ? "Live Market Data" : "Demo Market Data"}
            </span>
          )
        }
      />

      {/* Market status row */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card data-testid="market-status-card">
          <div className="text-[10px] uppercase tracking-wider text-slate-500">Market Status</div>
          <div className="mt-1 flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            <span className="font-display text-xl font-bold">{overview?.market_status || "—"}</span>
          </div>
        </Card>
        <Card>
          <div className="text-[10px] uppercase tracking-wider text-slate-500">NIFTY 50</div>
          <div className="mt-1 font-num text-xl font-bold">
            {overview ? overview.nifty.value.toLocaleString("en-IN") : "—"}
          </div>
        </Card>
        <Card>
          <div className="text-[10px] uppercase tracking-wider text-slate-500">NIFTY Change</div>
          <div className="mt-1 font-num text-xl font-bold">
            {overview ? <ChangePill value={overview.nifty.change_pct} /> : "—"}
          </div>
        </Card>
        <Card>
          <div className="text-[10px] uppercase tracking-wider text-slate-500">Market Regime</div>
          <div className={`mt-1 inline-flex rounded-md border px-2 py-1 font-num text-sm font-semibold ${regimeStyle(regime)}`}>
            {regime}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Top opportunities */}
        <div className="lg:col-span-2">
          <div className="mb-3 flex items-center gap-2">
            <TrendingUp size={16} className="text-blue-400" />
            <h2 className="font-display text-lg font-bold">Top Equity Opportunities</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {tops.map((idea) => (
              <Card
                key={idea.id}
                className="cursor-pointer transition-colors hover:border-slate-700"
                data-testid={`dashboard-top-${idea.symbol}`}
                onClick={() => navigate(`/equity/${idea.symbol}`)}
              >
                <div className="flex items-center justify-between">
                  <span className="font-display font-bold">{idea.symbol}</span>
                  <span className={`text-[10px] font-semibold ${idea.direction === "bullish" ? "text-emerald-400" : "text-rose-400"}`}>
                    {idea.direction_label}
                  </span>
                </div>
                <div className="my-3 flex justify-center">
                  <ScoreGauge score={idea.score} size={80} />
                </div>
                <div className="text-center text-[11px] text-slate-500">R:R 1:{idea.risk_reward}</div>
              </Card>
            ))}
          </div>

          {/* Sector heatmap */}
          <div className="mb-3 mt-6 flex items-center gap-2">
            <Zap size={16} className="text-amber-400" />
            <h2 className="font-display text-lg font-bold">Sector Snapshot</h2>
          </div>
          <Card>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {overview &&
                Object.entries(overview.sector_performance).map(([sec, chg]) => (
                  <div key={sec} className="flex items-center justify-between rounded-lg bg-slate-900/60 px-3 py-2">
                    <span className="text-xs text-slate-400">{sec}</span>
                    <ChangePill value={chg} />
                  </div>
                ))}
            </div>
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <Activity size={16} className="text-cyan-400" />
              <h2 className="font-display text-lg font-bold">Active Monitoring</h2>
            </div>
            {active.length === 0 ? (
              <Empty message="No active monitored ideas yet." testId="dashboard-monitoring-empty" />
            ) : (
              <div className="space-y-2">
                {active.slice(0, 5).map((s) => (
                  <Card key={s.id} className="flex items-center justify-between py-3" data-testid={`dashboard-session-${s.symbol}`}>
                    <div>
                      <div className="font-display text-sm font-bold">{s.symbol}</div>
                      <div className="text-[11px] text-slate-500">Entry {s.entry}</div>
                    </div>
                    <span className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold ${statusStyle(s.status)}`}>
                      {s.status}
                    </span>
                  </Card>
                ))}
              </div>
            )}
          </div>

          <div>
            <div className="mb-3 flex items-center gap-2">
              <Bell size={16} className="text-rose-400" />
              <h2 className="font-display text-lg font-bold">Recent Alerts</h2>
            </div>
            {alerts.length === 0 ? (
              <Empty message="No alerts yet." testId="dashboard-alerts-empty" />
            ) : (
              <div className="space-y-2">
                {alerts.map((a) => (
                  <Card key={a.id} className="py-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{a.type}</span>
                      <span className="text-[10px] text-slate-600">{new Date(a.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="mt-1 text-xs text-slate-300">{a.message}</div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
