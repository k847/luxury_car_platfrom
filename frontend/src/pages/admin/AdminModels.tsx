// =============================================================
// 段功能：M4 后台车型管理
// 说明：品牌 / 车系 / 车型 三个层级的列表 + 新增 + 删除（软删）。
//   品牌/车系/车型均带中英文名称；新增通过弹层表单提交到 admin API。
// =============================================================

import { useEffect, useState } from "react";
import {
  getBrands, createBrand, deleteBrand,
  getSeries, createSeries, deleteSeries,
  getModels, createModel, deleteModel, updateModel,
  type AdminBrand, type AdminSeries, type AdminModel,
} from "../../api/admin";

export default function AdminModels() {
  const [brands, setBrands] = useState<AdminBrand[]>([]);
  const [series, setSeries] = useState<AdminSeries[]>([]);
  const [models, setModels] = useState<AdminModel[]>([]);
  const [selectedBrand, setSelectedBrand] = useState<number | null>(null);
  const [show, setShow] = useState<"brand" | "series" | "model" | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [err, setErr] = useState("");

  const refresh = (brandId?: number) => {
    getBrands().then((b) => { setBrands(b); if (!brandId && b.length) setSelectedBrand(b[0].id); });
    getModels().then((r) => setModels(r.list));
    if (brandId) getSeries(brandId).then(setSeries);
  };
  useEffect(() => { refresh(); }, []);
  useEffect(() => {
    if (selectedBrand) getSeries(selectedBrand).then(setSeries);
    else setSeries([]);
  }, [selectedBrand]);

  const submit = () => {
    setErr("");
    try {
      if (show === "brand") {
        createBrand({ brand_code: form.code, name_zh: form.zh, name_en: form.en, country: form.country || null, sort: Number(form.sort || 0) }).then(() => { setShow(null); setForm({}); refresh(); });
      } else if (show === "series") {
        if (!selectedBrand) return;
        createSeries({ brand_id: selectedBrand, series_code: form.code, segment: form.segment || null, name_zh: form.zh, name_en: form.en, sort: Number(form.sort || 0) }).then(() => { setShow(null); setForm({}); refresh(selectedBrand); });
      } else if (show === "model") {
        if (!selectedBrand) return;
        const seriesObj = series.find((s) => s.brand_id === selectedBrand);
        if (!seriesObj) { setErr("请先为该品牌创建车系"); return; }
        createModel({ series_id: seriesObj.id, model_code: form.code, name_zh: form.zh, name_en: form.en, fuel_type: form.fuel || null, guide_price: form.price ? Number(form.price) : null, status: form.status || "active" }).then(() => { setShow(null); setForm({}); refresh(); });
      }
    } catch (e) {
      setErr((e as Error).message);
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-head"><h2>车型管理</h2></div>

      {/* 品牌 */}
      <section className="panel">
        <h3>品牌 <button className="btn-gold sm" onClick={() => setShow("brand")}>+ 新增品牌</button></h3>
        <table className="admin-table">
          <thead><tr><th>编码</th><th>中文</th><th>英文</th><th>国别</th><th>排序</th><th>操作</th></tr></thead>
          <tbody>
            {brands.map((b) => (
              <tr key={b.id}>
                <td>{b.brand_code}</td><td>{b.name_zh}</td><td>{b.name_en}</td><td>{b.country}</td><td>{b.sort}</td>
                <td><button className="btn-ghost sm" onClick={() => { setSelectedBrand(b.id); setShow("series"); }}>+车系</button> <button className="btn-danger sm" onClick={() => deleteBrand(b.id).then(() => refresh())}>删除</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* 车系（按选中品牌） */}
      <section className="panel">
        <h3>车系（品牌：{brands.find((b) => b.id === selectedBrand)?.name_zh || "未选"}）</h3>
        <table className="admin-table">
          <thead><tr><th>编码</th><th>中文</th><th>英文</th><th>级别</th><th>操作</th></tr></thead>
          <tbody>
            {series.map((s) => (
              <tr key={s.id}><td>{s.series_code}</td><td>{s.name_zh}</td><td>{s.name_en}</td><td>{s.segment}</td><td><button className="btn-danger sm" onClick={() => { if (selectedBrand) deleteSeries(s.id).then(() => getSeries(selectedBrand).then(setSeries)); }}>删除</button></td></tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* 车型 */}
      <section className="panel">
        <h3>车型 <button className="btn-gold sm" onClick={() => setShow("model")}>+ 新增车型</button></h3>
        <table className="admin-table">
          <thead><tr><th>编码</th><th>中文</th><th>英文</th><th>能源</th><th>指导价</th><th>状态</th><th>推荐</th><th>操作</th></tr></thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.id}>
                <td>{m.model_code}</td><td>{m.name_zh}</td><td>{m.name_en}</td><td>{m.fuel_type}</td><td>{m.guide_price != null ? `¥${m.guide_price.toLocaleString()}` : "—"}</td><td>{m.status}</td><td>{m.is_recommended ? "是" : "否"}</td>
                <td>
                  <button className="btn-ghost sm" onClick={() => updateModel(m.id, { series_id: m.series_id, model_code: m.model_code, name_zh: m.name_zh || "", name_en: m.name_en || "", is_recommended: m.is_recommended ? 0 : 1 }).then(() => refresh())}>{m.is_recommended ? "取消推荐" : "推荐"}</button>
                  <button className="btn-danger sm" onClick={() => deleteModel(m.id).then(() => refresh())}>删除</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* 新增弹层 */}
      {show && (
        <div className="admin-modal">
          <div className="modal-card">
            <h3>新增{show === "brand" ? "品牌" : show === "series" ? "车系" : "车型"}</h3>
            <label>编码 <input value={form.code || ""} onChange={(e) => setForm({ ...form, code: e.target.value })} /></label>
            <label>中文名 <input value={form.zh || ""} onChange={(e) => setForm({ ...form, zh: e.target.value })} /></label>
            <label>英文名 <input value={form.en || ""} onChange={(e) => setForm({ ...form, en: e.target.value })} /></label>
            {show === "brand" && <label>国别 <input value={form.country || ""} onChange={(e) => setForm({ ...form, country: e.target.value })} /></label>}
            {show === "series" && <label>级别 <input value={form.segment || ""} onChange={(e) => setForm({ ...form, segment: e.target.value })} /></label>}
            {show === "model" && (
              <>
                <label>能源 <input value={form.fuel || ""} onChange={(e) => setForm({ ...form, fuel: e.target.value })} /></label>
                <label>指导价 <input type="number" value={form.price || ""} onChange={(e) => setForm({ ...form, price: e.target.value })} /></label>
              </>
            )}
            {err && <div className="admin-error">{err}</div>}
            <div className="modal-actions">
              <button className="btn-gold" onClick={submit}>保存</button>
              <button className="btn-ghost" onClick={() => { setShow(null); setErr(""); }}>取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
