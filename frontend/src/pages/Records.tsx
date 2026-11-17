import { useEffect, useRef, useState } from "react";
import { api } from "../api";

type Field = { key: string; label: string; type?: string };

function Records({ title, path, fields, nameOf }: { title: string; path: string; fields: Field[]; nameOf: (r: any) => string }) {
  const [rows, setRows] = useState<any[]>([]);
  const [form, setForm] = useState<Record<string, string>>({});
  const [q, setQ] = useState("");
  const [msg, setMsg] = useState("");
  const file = useRef<HTMLInputElement>(null);
  const load = () => api(`/${path}`).then(setRows);
  useEffect(() => { load(); }, [path]);

  const add = async (e: React.FormEvent) => { e.preventDefault(); await api(`/${path}`, { method: "POST", json: form }); setForm({}); load(); };
  const del = async (id: number) => { if (confirm("Delete?")) { await api(`/${path}/${id}`, { method: "DELETE" }).catch((e) => setMsg(e.message)); load(); } };
  const upload = async (f: File) => {
    const fd = new FormData(); fd.append("file", f);
    const r = await api(`/import/${path}`, { method: "POST", body: fd });
    setMsg(`Imported ${r.created} rows` + (r.errors.length ? `, ${r.errors.length} errors (first: row ${r.errors[0].row} ${r.errors[0].error})` : ""));
    load();
  };
  const shown = rows.filter((r) => JSON.stringify(r).toLowerCase().includes(q.toLowerCase()));

  return (
    <>
      <h1>{title}</h1>
      <form className="row" onSubmit={add}>
        {fields.map((f) => <input key={f.key} placeholder={f.label} type={f.type} required={f === fields[0]}
          value={form[f.key] ?? ""} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />)}
        <button className="primary">Add</button>
      </form>
      <div className="row">
        <input placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} />
        <a href={`/api/export/${path}.csv`}><button type="button">Export CSV</button></a>
        <button type="button" onClick={() => file.current?.click()}>Import CSV</button>
        <input ref={file} type="file" accept=".csv" hidden onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
        <span className="muted">{msg}</span>
      </div>
      <table>
        <thead><tr><th>Name</th>{fields.slice(1).map((f) => <th key={f.key}>{f.label}</th>)}<th /></tr></thead>
        <tbody>{shown.map((r) => (
          <tr key={r.id}><td>{nameOf(r)}</td>{fields.slice(1).map((f) => <td key={f.key}>{r[f.key]}</td>)}
            <td><button className="link" onClick={() => del(r.id)}>Delete</button></td></tr>
        ))}</tbody>
      </table>
    </>
  );
}

export const Contacts = () => (
  <Records title="Contacts" path="contacts" nameOf={(r) => `${r.first_name} ${r.last_name}`}
    fields={[{ key: "first_name", label: "First name" }, { key: "last_name", label: "Last name" },
      { key: "email", label: "Email", type: "email" }, { key: "phone", label: "Phone" }, { key: "title", label: "Title" }]} />
);
export const Companies = () => (
  <Records title="Companies" path="companies" nameOf={(r) => r.name}
    fields={[{ key: "name", label: "Name" }, { key: "website", label: "Website" }, { key: "industry", label: "Industry" }]} />
);
