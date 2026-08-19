// =============================================================
// 段功能：M4 后台布局 + 门控（需登录）
// 说明：若 localStorage 无 access_token，重定向到 /admin/login。
//   左侧菜单导航（仪表盘/车型/内容/线索/经销商/系统），右上角退出登录。
// =============================================================

import { useEffect } from "react";
import { Outlet, useNavigate, Link } from "react-router-dom";

const MENUS = [
  { to: "/admin/dashboard", label: "仪表盘" },
  { to: "/admin/models", label: "车型管理" },
  { to: "/admin/content", label: "内容管理" },
  { to: "/admin/leads", label: "线索管理" },
  { to: "/admin/dealers", label: "经销商" },
  { to: "/admin/system", label: "系统设置" },
];

export default function AdminLayout() {
  const navigate = useNavigate();

  // 门控：无 token 重定向登录
  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      navigate("/admin/login", { replace: true });
    }
  }, [navigate]);

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/admin/login");
  };

  return (
    <div className="admin-shell">
      <aside className="admin-side">
        <div className="admin-brand">REGALIA 后台</div>
        <nav className="admin-nav">
          {MENUS.map((m) => (
            <Link key={m.to} to={m.to}>{m.label}</Link>
          ))}
        </nav>
      </aside>
      <div className="admin-main">
        <header className="admin-top">
          <span />
          <div className="admin-top__right">
            <Link to="/" className="btn-ghost">前台</Link>
            <button className="btn-ghost" onClick={logout}>退出</button>
          </div>
        </header>
        <main className="admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
