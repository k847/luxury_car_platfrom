// =============================================================
// 段功能：M4 后台系统设置
// 说明：审计日志列表 + SEO 配置查看/保存。RBAC 角色/权限为只读展示。
// =============================================================

import { useEffect, useState } from "react";
import { getAuditLogs, getPermissions, getRoles, getSeo, updateSeo } from "../../api/admin";

export default function AdminSystem() {
  const [logs, setLogs] = useState<Array<Record<string, unknown>>>([]);
  const [permissions, setPermissions] = useState<Array<{ code: string; module: string }>>([]);
  const [roles, setRoles] = useState<Array<Record<string, unknown>>>([]);
  const [seo, setSeo] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState("");

  useEffect(() => {
    getAuditLogs().then((r) => setLogs(r.list));
    getPermissions().then(setPermissions);
    getRoles().then(setRoles);
    getSeo().then(setSeo);
  }, []);

  const saveSeo = () => {
    updateSeo(seo).then(() => { setSaved("已保存"); setTimeout(() => setSaved(""), 2000); });
  };

  return (
    <div className="admin-page">
      <div className="admin-page-head"><h2>系统设置</h2></div>

      <div className="dash-cols">
        {/* SEO */}
        <section className="panel">
          <h3>SEO 配置</h3>
          {["title", "keywords", "description", "og_image"].map((k) => (
            <label key={k} className="seo-label">{k} <input value={seo[k] || ""} onChange={(e) => setSeo({ ...seo, [k]: e.target.value })} /></label>
          ))}
          <button className="btn-gold sm" onClick={saveSeo}>保存 SEO</button>
          {saved && <span className="muted">{saved}</span>}
        </section>

        {/* 角色 / 权限 */}
        <section className="panel">
          <h3>角色与权限</h3>
          <p className="muted">角色：{roles.map((r) => (r as { name?: string }).name).join("、") || "无"}</p>
          <p className="muted">权限点（{permissions.length}）：</p>
          <div className="perm-chips">{permissions.map((p) => <span key={p.code} className="chip">{p.code}</span>)}</div>
        </section>
      </div>

      {/* 审计日志 */}
      <section className="panel">
        <h3>审计日志</h3>
        <table className="admin-table">
          <thead><tr><th>ID</th><th>操作人</th><th>动作</th><th>模块</th><th>IP</th></tr></thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id as number}><td>{l.id as number}</td><td>{String(l.admin_user_id ?? "—")}</td><td>{l.action as string}</td><td>{String(l.module ?? "—")}</td><td>{String(l.ip ?? "—")}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
