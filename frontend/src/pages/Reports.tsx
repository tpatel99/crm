import { useEffect, useState } from "react";
import { api, money } from "../api";

export default function Reports() {
  const [r, setR] = useState<any>(null);
  useEffect(() => { api("/reports/summary").then(setR); }, []);
  if (!r) return null;
  const max = Math.max(1, ...Object.values<any>(r.by_stage).map((s) => s.value));
  return (
    <>
      <h1>Reports</h1>
      <div className="grid" style={{ marginBottom: 16 }}>
        <div className="card"><div className="muted">Open pipeline</div><div className="stat">{money(r.open_value)}</div></div>
        <div className="card"><div className="muted">Weighted forecast</div><div className="stat">{money(r.weighted_forecast)}</div></div>
        <div className="card"><div className="muted">Won</div><div className="stat">{money(r.won_value)}</div></div>
        <div className="card"><div className="muted">Win rate</div><div className="stat">{r.win_rate == null ? "—" : Math.round(r.win_rate * 100) + "%"}</div></div>
      </div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Value by stage</h3>
        {Object.entries<any>(r.by_stage).map(([st, v]) => (
          <div key={st} className="row" style={{ marginBottom: 6 }}>
            <span style={{ width: 100 }}>{st}</span>
            <div style={{ flex: 1, background: "var(--bg)", borderRadius: 4 }}>
              <div style={{ width: `${(v.value / max) * 100}%`, minWidth: 2, height: 16, background: "var(--accent)", borderRadius: 4 }} />
            </div>
            <span style={{ width: 130, textAlign: "right" }}>{money(v.value)} · {v.count}</span>
          </div>))}
      </div>
    </>
  );
}
