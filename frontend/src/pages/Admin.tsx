import { useEffect, useState } from "react";
import { api } from "../api";
import type { Me } from "../App";

export default function Admin({ me }: { me: Me }) {
  const [users, setUsers] = useState<any[]>([]);
  const [err, setErr] = useState("");
  const load = () => api("/users").then(setUsers);
  useEffect(() => { load(); }, []);
  const patch = async (id: number, body: object) => { setErr(""); await api(`/users/${id}`, { method: "PATCH", json: body }).catch((e) => setErr(e.message)); load(); };
  return (
    <>
      <h1>Users</h1>
      <p className="muted">Users appear here after their first Okta sign-in. Control who can sign in via Okta app assignments.</p>
      {err && <p className="err">{err}</p>}
      <table><thead><tr><th>Email</th><th>Name</th><th>Admin</th><th>Active</th></tr></thead>
        <tbody>{users.map((u) => (
          <tr key={u.id}><td>{u.email}</td><td>{u.name}</td>
            <td><input type="checkbox" checked={u.is_admin} disabled={u.id === me.id} onChange={(e) => patch(u.id, { is_admin: e.target.checked })} /></td>
            <td><input type="checkbox" checked={u.is_active} disabled={u.id === me.id} onChange={(e) => patch(u.id, { is_active: e.target.checked })} /></td></tr>))}
        </tbody></table>
    </>
  );
}
