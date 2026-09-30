import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import api from "../lib/api";
import { PageHeader, Card } from "../components/Primitives";
import { ChangePill } from "../components/Score";
import { regimeStyle as regStyle } from "../lib/format";

export default function MarketOverview() {
  const [o, setO] = useState(null);
  useEffect(() => { api.get("/market/overview").then((r) => setO(r.data)).catch(() => {}); }, []);
  if (!o) return <div className="py-20 text-center text-sm text-slate-500">Loading market…</div>;

  const sectorData = Object.entries(o.sector_performance).map(([name, chg]) => ({ name, chg }));
  const total = o.breadth.total || 1;

  return (
    <div>
      <PageHeader title="Market Overview" subtitle="NIFTY, breadth and sector performance — V1 mock data" />

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card>
          <div className="text-[10px] uppercase tracking-wider text-slate-500">NIFTY 50</div>
          <div className="mt-1 font-num text-xl font-bold">{o.nifty.value.toLocaleString("en-IN")}</div>
          <ChangePill value={o.nifty.change_pct} />
        </Card>
        <Card>
          <div className="text-[10px] uppercase tracking-wider text-slate-500">Regime</div>
          <div className={`mt-1 inline-flex rounded-md border px-2 py-1 font-num text-sm font-semibold ${regStyle(o.regime.regime)}`}>{o.regime.regime}</div>
        </Card>
        <Card>
          <div className="text-[10px] uppercase tracking-wider text-slate-500">Advances</div>
          <div className="mt-1 font-num text-xl font-bold text-emerald-400">{o.breadth.advances}</div>
        </Card>
        <Card>
          <div className="text-[10px] uppercase tracking-wider text-slate-500">Declines</div>
          <div className="mt-1 font-num text-xl font-bold text-rose-400">{o.breadth.declines}</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="mb-3 font-display text-lg font-bold">Sector Performance</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={sectorData} layout="vertical" margin={{ left: 20 }}>
              <XAxis type="number" tick={{ fill: "#64748B", fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fill: "#94A3B8", fontSize: 11 }} width={90} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #1E293B", borderRadius: 8 }} cursor={{ fill: "#1E293B55" }} />
              <Bar dataKey="chg" radius={[0, 4, 4, 0]}>
                {sectorData.map((d, i) => <Cell key={i} fill={d.chg >= 0 ? "#10B981" : "#EF4444"} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <div className="space-y-6">
          <Card>
            <h2 className="mb-3 font-display text-lg font-bold">Market Breadth</h2>
            <div className="h-3 w-full overflow-hidden rounded-full bg-slate-800">
              <div className="h-full bg-emerald-500" style={{ width: `${(o.breadth.advances / total) * 100}%` }} />
            </div>
            <div className="mt-2 flex justify-between text-xs text-slate-400">
              <span>{Math.round((o.breadth.advances / total) * 100)}% Bulls</span>
              <span>{Math.round((o.breadth.declines / total) * 100)}% Bears</span>
            </div>
          </Card>
          <Card>
            <h2 className="mb-3 font-display text-lg font-bold">Top Gainers</h2>
            {o.top_gainers.map((g) => (
              <div key={g.symbol} className="flex items-center justify-between border-b border-slate-800 py-2 last:border-0">
                <span className="font-display text-sm font-bold">{g.symbol}</span>
                <ChangePill value={g.change_pct} />
              </div>
            ))}
          </Card>
          <Card>
            <h2 className="mb-3 font-display text-lg font-bold">Top Losers</h2>
            {o.top_losers.map((g) => (
              <div key={g.symbol} className="flex items-center justify-between border-b border-slate-800 py-2 last:border-0">
                <span className="font-display text-sm font-bold">{g.symbol}</span>
                <ChangePill value={g.change_pct} />
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
