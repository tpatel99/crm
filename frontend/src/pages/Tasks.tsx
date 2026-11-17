import { useEffect, useState } from "react";
import { api } from "../api";

type Task = { id: number; title: string; due_date: string | null; done: boolean; deal_id: number | null; contact_id: number | null; assignee_id: number | null };

export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [form, setForm] = useState({ title: "", due_date: "" });
  const load = () => api("/tasks").then(setTasks);
  useEffect(() => { load(); }, []);
  const today = new Date().toISOString().slice(0, 10);

  const add = async (e: React.FormEvent) => { e.preventDefault();
    await api("/tasks", { method: "POST", json: { title: form.title, due_date: form.due_date || null } });
    setForm({ title: "", due_date: "" }); load(); };
  const toggle = async (t: Task) => { await api(`/tasks/${t.id}`, { method: "PUT", json: { ...t, done: !t.done } }); load(); };
  const del = async (id: number) => { await api(`/tasks/${id}`, { method: "DELETE" }); load(); };

  return (
    <>
      <h1>Tasks</h1>
      <form className="row" onSubmit={add}>
        <input required placeholder="New task" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
        <button className="primary">Add</button>
      </form>
      <table><tbody>{tasks.map((t) => (
        <tr key={t.id}>
          <td style={{ width: 30 }}><input type="checkbox" checked={t.done} onChange={() => toggle(t)} /></td>
          <td style={{ textDecoration: t.done ? "line-through" : "none" }}>{t.title}</td>
          <td className={!t.done && t.due_date && t.due_date < today ? "overdue" : "muted"}>{t.due_date ?? ""}</td>
          <td><button className="link" onClick={() => del(t.id)}>Delete</button></td>
        </tr>))}</tbody></table>
    </>
  );
}
