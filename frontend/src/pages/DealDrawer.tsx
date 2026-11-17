import { useEffect, useState } from "react";
import { api } from "../api";
import type { Me } from "../App";
import type { Deal } from "./Board";

type Act = { id: number; kind: string; body: string; created_at: string };

export default function DealDrawer({ deal, onClose, onChanged }: { deal: Deal; onClose: () => void; onChanged: () => void; me: Me }) {
  const [d, setD] = useState(deal);
  const [acts, setActs] = useState<Act[]>([]);
  const [note, setNote] = useState({ kind: "note", body: "" });
  const loadActs = () => api(`/activities?deal_id=${deal.id}`).then(setActs);
  useEffect(() => { loadActs(); }, [deal.id]);

  const save = async () => { await api(`/deals/${d.id}`, { method: "PUT", json: {
    title: d.title, value: Number(d.value), stage: d.stage, expected_close: d.expected_close || null,
    company_id: d.company_id, contact_id: d.contact_id, owner_id: d.owner_id } }); onChanged(); onClose(); };
  const del = async () => { if (confirm("Delete this deal?")) { await api(`/deals/${d.id}`, { method: "DELETE" }); onChanged(); onClose(); } };
  const log = async (e: React.FormEvent) => {
    e.preventDefault();
    await api("/activities", { method: "POST", json: { ...note, deal_id: d.id } });
    setNote({ ...note, body: "" }); loadActs();
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "#0006" }} onClick={onClose}>
      <aside className="card" style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: 420, overflow: "auto", borderRadius: 0 }}
        onClick={(e) => e.stopPropagation()}>
        <div className="row"><h1 style={{ flex: 1, margin: 0 }}>Deal</h1><button onClick={onClose}>✕</button></div>
        <div className="stack" style={{ display: "grid", gap: 8 }}>
          <input value={d.title} onChange={(e) => setD({ ...d, title: e.target.value })} />
          <input type="number" value={d.value} onChange={(e) => setD({ ...d, value: Number(e.target.value) })} />
          <input type="date" value={d.expected_close ?? ""} onChange={(e) => setD({ ...d, expected_close: e.target.value })} />
          <div className="row">
            <button className="primary" onClick={save}>Save</button>
            <button onClick={del}>Delete</button>
          </div>
        </div>
        <h3>Activity</h3>
        <form className="row" onSubmit={log}>
          <select value={note.kind} onChange={(e) => setNote({ ...note, kind: e.target.value })}>
            {["note", "call", "email", "meeting"].map((k) => <option key={k}>{k}</option>)}
          </select>
          <input required style={{ flex: 1 }} placeholder="What happened?" value={note.body} onChange={(e) => setNote({ ...note, body: e.target.value })} />
          <button className="primary">Log</button>
        </form>
        {acts.map((a) => (
          <p key={a.id}><b>{a.kind}</b> · <span className="muted">{new Date(a.created_at + "Z").toLocaleString()}</span><br />{a.body}</p>
        ))}
      </aside>
    </div>
  );
}
