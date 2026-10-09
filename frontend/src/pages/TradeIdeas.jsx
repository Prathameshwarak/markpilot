import { useEffect, useState, useCallback } from "react";
import api from "../lib/api";
import usePolling from "../hooks/usePolling";
import { PageHeader } from "../components/Primitives";
import { TradeIdeaCard } from "../components/TradeIdeaCard";

export default function TradeIdeas() {
  const [ideas, setIdeas] = useState([]);

  const load = useCallback(() => {
    api.get("/trade-ideas").then((r) => setIdeas(r.data.ideas)).catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);
  usePolling(load, 30000);

  return (
    <div>
      <PageHeader title="Trade Ideas" subtitle="Transparent, research-based opportunities — you make the final decision" />
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3" data-testid="ideas-grid">
        {ideas.map((idea) => (
          <TradeIdeaCard key={idea.id} idea={idea} onMonitored={load} />
        ))}
      </div>
    </div>
  );
}
