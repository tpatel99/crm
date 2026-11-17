import { useEffect, useState } from "react";
import { api, money } from "../api";
import type { Me } from "../App";
import DealDrawer from "./DealDrawer";

export type Deal = { id: number; title: string; value: number; stage: string; expected_close: string | null;
  company_id: number | null; contact_id: number | null; owner_id: number | null };
export type Company = { id: number; name: string };

export default function Board({ me }: { me: Me }) {
  const [stages, setStages] = useState<string[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [over, setOver] = useState<string | null>(null);
  const [open, setOpen] = useState<Deal | null>(null);
  const [form, setForm] = useState({ title: "", value: "", company_id: "" });
  const [error, setError] = useState("");

  const load = () => Promise.all([api("/stages"), api("/deals"), api("/companies")])
    .then(([s, d, c]) => { setStages(s); setDeals(d); setCompanies(c); })
    .catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const move = async (id: number, stage: string) => {
    const prev = deals;
    setDeals(deals.map((d) => (d.id === id ? { ...d, stage } : d))); // optimistic
    try { await api(`/deals/${id}/stage`, { method: "PATCH", json: { stage } }); }
    catch (e: any) { setDeals(prev); setError(e.message); }
  };

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    await api("/deals", { method: "POST", json: {
      title: form.title, value: Number(form.value) || 0,
      company_id: form.company_id ? Number(form.company_id) : null } });
    setForm({ title: "", value: "", company_id: "" });
    load();
  };

  return (
    <>
      <h1>Pipeline</h1>
      {error && <p className="err">{error}</p>}
      <form className="row" onSubmit={add}>
        <input required placeholder="New deal title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <input type="number" placeholder="Value" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} />
        <select value={form.company_id} onChange={(e) => setForm({ ...form, company_id: e.target.value })}>
          <option value="">No company</option>
          {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button className="primary">Add deal</button>
      </form>
      <div className="board">
        {stages.map((st) => {
          const items = deals.filter((d) => d.stage === st);
          return (
            <div key={st} className={"col" + (over === st ? " over" : "")}
              onDragOver={(e) => { e.preventDefault(); setOver(st); }}
              onDragLeave={() => setOver(null)}
              onDrop={(e) => { setOver(null); move(Number(e.dataTransfer.getData("id")), st); }}>
              <h3><span>{st} ({items.length})</span><span>{money(items.reduce((a, d) => a + Number(d.value), 0))}</span></h3>
              {items.map((d) => (
                <div key={d.id} className="deal" draggable
                  onDragStart={(e) => e.dataTransfer.setData("id", String(d.id))} onClick={() => setOpen(d)}>
                  <b>{d.title}</b>
                  <span className="muted">{companies.find((c) => c.id === d.company_id)?.name ?? "—"} · {money(Number(d.value))}</span>
                </div>
              ))}
            </div>
          );
        })}
      </div>
      {open && <DealDrawer deal={open} onClose={() => setOpen(null)} onChanged={load} me={me} />}
    </>
  );
}
