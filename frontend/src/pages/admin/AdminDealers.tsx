// =============================================================
// 段功能：M4 后台经销商管理
// 说明：经销商列表 + 新增 + 删除（软删）。字段含经纬度/电话/营业时间。
// =============================================================

import { useEffect, useState } from "react";
import { getBrands, type AdminBrand } from "../../api/admin";
import request from "../../api/request";

interface Dealer { id: number; brand_id: number; name: string; city: string | null; address: string | null; phone: string | null; is_active: number }

export default function AdminDealers() {
  const [dealers, setDealers] = useState<Dealer[]>([]);
  const [brands, setBrands] = useState<AdminBrand[]>([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [err, setErr] = useState("");

  const refresh = () => request.get("/api/v1/admin/dealers").then((r) => setDealers((r as { data: Dealer[] }).data || []));
  useEffect(() => { refresh(); getBrands().then(setBrands); }, []);

  const submit = () => {
    setErr("");
    request.post("/api/v1/admin/dealers", {
      brand_id: Number(form.brand_id || brands[0]?.id || 0),
      name: form.name, city: form.city || null, address: form.address || null,
      phone: form.phone || null, lng: form.lng ? Number(form.lng) : null, lat: form.lat ? Number(form.lat) : null,
    }).then(() => { setShow(false); setForm({}); refresh(); }).catch((e: Error) => setErr(e.message));
  };

  return (
    <div className="admin-page">
      <div className="admin-page-head"><h2>经销商管理</h2><button className="btn-gold sm" onClick={() => setShow(true)}>+ 新增经销商</button></div>
      <section className="panel">
        <table className="admin-table">
          <thead><tr><th>ID</th><th>名称</th><th>品牌</th><th>城市</th><th>地址</th><th>电话</th><th>操作</th></tr></thead>
          <tbody>
            {dealers.map((d) => (
              <tr key={d.id}>
                <td>{d.id}</td><td>{d.name}</td>
                <td>{brands.find((b) => b.id === d.brand_id)?.name_zh || d.brand_id}</td>
                <td>{d.city || "—"}</td><td>{d.address || "—"}</td><td>{d.phone || "—"}</td>
                <td><button className="btn-danger sm" onClick={() => request.delete(`/api/v1/admin/dealers/${d.id}`).then(refresh)}>删除</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {show && (
        <div className="admin-modal">
          <div className="modal-card">
            <h3>新增经销商</h3>
            <label>名称 <input value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label>品牌 <select value={form.brand_id || brands[0]?.id || ""} onChange={(e) => setForm({ ...form, brand_id: e.target.value })}>{brands.map((b) => <option key={b.id} value={b.id}>{b.name_zh}</option>)}</select></label>
            <label>城市 <input value={form.city || ""} onChange={(e) => setForm({ ...form, city: e.target.value })} /></label>
            <label>地址 <input value={form.address || ""} onChange={(e) => setForm({ ...form, address: e.target.value })} /></label>
            <label>电话 <input value={form.phone || ""} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
            {err && <div className="admin-error">{err}</div>}
            <div className="modal-actions"><button className="btn-gold" onClick={submit}>保存</button><button className="btn-ghost" onClick={() => { setShow(false); setErr(""); }}>取消</button></div>
          </div>
        </div>
      )}
    </div>
  );
}
