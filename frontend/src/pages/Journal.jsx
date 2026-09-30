import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api from "../lib/api";
import { PageHeader, Card, Empty } from "../components/Primitives";
import { fmtINR } from "../lib/format";

const BLANK = { symbol: "", setup: "Swing", direction: "bullish", entry_price: "", exit_price: "", quantity: 1, outcome: "open", notes: "" };

export default function Journal() {
  const [data, setData] = useState({ metrics: {}, entries: [] });
  const [form, setForm] = useState(BLANK);

  const load = useCallback(() => {
    api.get("/journal").then((r) => setData(r.data)).catch(() => {});
  }, []);
  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/journal", {
        ...form,
        entry_price: Number(form.entry_price),
        exit_price: form.exit_price === "" ? null : Number(form.exit_price),
        quantity: Number(form.quantity),
      });
      toast.success("Journal entry saved");
      setForm(BLANK);
      load();
    } catch (err) { toast.error(err.response?.data?.detail || "Save failed"); }
  };

  const m = data.metrics;
  const inputCls = "w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-blue-500";

  return (
    <div>
      <PageHeader title="Trade Journal" subtitle="Log trades, review your edge" />

      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          ["Total Trades", m.total ?? 0], ["Win Rate", `${m.win_rate ?? 0}%`],
          ["Simulated P&L", fmtINR(m.total_pnl ?? 0)], ["Closed", m.closed ?? 0],
        ].map(([l, v]) => (
          <Card key={l}>
            <div className="text-[10px] uppercase tracking-wider text-slate-500">{l}</div>
            <div className="mt-1 font-num text-xl font-bold">{v}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <h2 className="mb-3 font-display text-lg font-bold">Add Entry</h2>
          <form onSubmit={submit} className="space-y-3" data-testid="journal-form">
            <input required placeholder="Symbol" value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value.toUpperCase() })} className={inputCls} data-testid="journal-symbol-input" />
            <div className="grid grid-cols-2 gap-3">
              <select value={form.setup} onChange={(e) => setForm({ ...form, setup: e.target.value })} className={inputCls}>
                {["Swing", "Breakout", "Reversal", "Positional"].map((s) => <option key={s}>{s}</option>)}
              </select>
              <select value={form.direction} onChange={(e) => setForm({ ...form, direction: e.target.value })} className={inputCls}>
                <option value="bullish">Bullish</option><option value="bearish">Bearish</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input required type="number" step="0.01" placeholder="Entry ₹" value={form.entry_price} onChange={(e) => setForm({ ...form, entry_price: e.target.value })} className={inputCls} data-testid="journal-entry-input" />
              <input type="number" step="0.01" placeholder="Exit ₹" value={form.exit_price} onChange={(e) => setForm({ ...form, exit_price: e.target.value })} className={inputCls} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input type="number" min="1" placeholder="Qty" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} className={inputCls} />
              <select value={form.outcome} onChange={(e) => setForm({ ...form, outcome: e.target.value })} className={inputCls}>
                <option value="open">Open</option><option value="win">Win</option><option value="loss">Loss</option>
              </select>
            </div>
            <textarea placeholder="Notes / mindset" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inputCls} rows={2} />
            <button type="submit" className="w-full rounded-lg bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-500" data-testid="journal-submit-button">Save Entry</button>
          </form>
        </Card>

        <div className="lg:col-span-2">
          {data.entries.length === 0 ? (
            <Empty message="No journal entries yet." testId="journal-empty" />
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-900/80 text-[10px] uppercase tracking-wider text-slate-500">
                  <tr><th className="px-4 py-3">Symbol</th><th className="px-4 py-3">Setup</th><th className="px-4 py-3 text-right">Entry</th><th className="px-4 py-3 text-right">Exit</th><th className="px-4 py-3 text-right">Qty</th><th className="px-4 py-3">Outcome</th></tr>
                </thead>
                <tbody>
                  {data.entries.map((e) => (
                    <tr key={e.id} className="border-t border-slate-800" data-testid={`journal-row-${e.symbol}`}>
                      <td className="px-4 py-3 font-display font-bold">{e.symbol}</td>
                      <td className="px-4 py-3 text-slate-400">{e.setup}</td>
                      <td className="px-4 py-3 text-right font-num">{fmtINR(e.entry_price)}</td>
                      <td className="px-4 py-3 text-right font-num">{e.exit_price == null ? "—" : fmtINR(e.exit_price)}</td>
                      <td className="px-4 py-3 text-right font-num">{e.quantity}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-md px-2 py-0.5 text-[10px] font-semibold ${e.outcome === "win" ? "bg-emerald-500/10 text-emerald-400" : e.outcome === "loss" ? "bg-rose-500/10 text-rose-400" : "bg-slate-500/10 text-slate-400"}`}>{e.outcome}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
