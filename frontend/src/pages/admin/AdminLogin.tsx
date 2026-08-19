// =============================================================
// 段功能：M4 后台登录页
// 说明：登录成功后把 access_token/refresh_token 存 localStorage 并跳转后台首页。
//   M1 的 /auth/login 返回裸结构，直接用 adminLogin 拿到 access_token。
// =============================================================

import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { adminLogin } from "../../api/admin";

export default function AdminLogin() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    adminLogin(username, password)
      .then((r: { access_token: string; refresh_token: string }) => {
        localStorage.setItem("access_token", r.access_token);
        localStorage.setItem("refresh_token", r.refresh_token);
        navigate("/admin/dashboard");
      })
      .catch(() => setErr("用户名或密码错误"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="admin-login">
      <div className="admin-login__card">
        <h1>REGALIA · 后台管理</h1>
        <form onSubmit={submit}>
          <label>
            用户名
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          </label>
          <label>
            密码
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {err && <div className="admin-error">{err}</div>}
          <button className="btn-gold" type="submit" disabled={loading}>
            {loading ? "登录中…" : "登录"}
          </button>
        </form>
        <Link to="/" className="btn-ghost">返回前台</Link>
      </div>
    </div>
  );
}
