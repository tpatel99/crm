import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { api, AuthError } from "./api";
import Board from "./pages/Board";
import Reports from "./pages/Reports";
import Tasks from "./pages/Tasks";
import { Companies, Contacts } from "./pages/Records";
import Admin from "./pages/Admin";

export type Me = { id: number; email: string; name: string; is_admin: boolean; auth_disabled?: boolean };

export default function App() {
  const [me, setMe] = useState<Me | null | undefined>(undefined);
  useEffect(() => {
    api<Me>("/auth/me").then(setMe).catch((e) => { if (e instanceof AuthError) setMe(null); });
  }, []);

  if (me === undefined) return null;
  if (me === null)
    return (
      <div className="login card">
        <h1>CRM</h1>
        <a href="/api/auth/login"><button className="primary">Sign in with Okta</button></a>
      </div>
    );

  const logout = async () => { await api("/auth/logout", { method: "POST" }); setMe(null); };
  return (
    <>
      <nav>
        <NavLink to="/">Pipeline</NavLink>
        <NavLink to="/contacts">Contacts</NavLink>
        <NavLink to="/companies">Companies</NavLink>
        <NavLink to="/tasks">Tasks</NavLink>
        <NavLink to="/reports">Reports</NavLink>
        {me.is_admin && <NavLink to="/admin">Admin</NavLink>}
        <span className="sp" />
        <span className="muted">{me.email}</span>
        {me.auth_disabled ? <span className="muted">(auth off)</span> : <button className="link" onClick={logout}>Sign out</button>}
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Board me={me} />} />
          <Route path="/contacts" element={<Contacts />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/admin" element={me.is_admin ? <Admin me={me} /> : <Navigate to="/" />} />
        </Routes>
      </main>
    </>
  );
}
