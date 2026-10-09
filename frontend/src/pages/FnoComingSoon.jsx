import { Zap, Lock } from "lucide-react";
import { PageHeader, Card } from "../components/Primitives";

export default function FnoComingSoon() {
  return (
    <div>
      <PageHeader title="F&O — Futures & Options" subtitle="A dedicated module planned for a future milestone" />
      <Card className="flex flex-col items-center py-16 text-center" data-testid="fno-coming-soon">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-500/10">
          <Zap className="h-8 w-8 text-amber-400" />
        </div>
        <h2 className="font-display text-2xl font-extrabold">Coming Soon</h2>
        <p className="mt-2 max-w-md text-sm text-slate-400">
          Options chains, PCR, Max Pain, Greeks and strategy builders will arrive as a separate module.
          MarketPilot V1 focuses exclusively on equity research and monitoring.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {["Option Chain", "PCR", "Max Pain", "Greeks", "Strategy Builder"].map((f) => (
            <span key={f} className="flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-500">
              <Lock size={12} /> {f}
            </span>
          ))}
        </div>
      </Card>
    </div>
  );
}
