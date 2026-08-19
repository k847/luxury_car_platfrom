// =============================================================
// 段功能：M4 后台内容管理（资讯 + Banner）
// 说明：资讯列表（双语标题/发布状态）+ 新增；Banner 列表 + 新增 + 删除。
// =============================================================

import { useEffect, useState } from "react";
import { getArticles, createArticle, deleteArticle, getBanners, createBanner, deleteBanner, type AdminArticle, type AdminBanner } from "../../api/admin";

export default function AdminContent() {
  const [articles, setArticles] = useState<AdminArticle[]>([]);
  const [banners, setBanners] = useState<AdminBanner[]>([]);
  const [tab, setTab] = useState<"articles" | "banners">("articles");
  const [form, setForm] = useState<Record<string, string>>({});
  const [show, setShow] = useState(false);
  const [err, setErr] = useState("");

  const refresh = () => {
    getArticles().then((r) => setArticles(r.list));
    getBanners().then(setBanners);
  };
  useEffect(() => { refresh(); }, []);

  const submitArticle = () => {
    setErr("");
    createArticle({ category: form.category || "company_news", status: form.status || "draft", title_zh: form.zh, summary_zh: form.summary || null, title_en: form.en || null, cover_url: form.cover || null, author: form.author || null })
      .then(() => { setShow(false); setForm({}); refresh(); })
      .catch((e: Error) => setErr(e.message));
  };
  const submitBanner = () => {
    setErr("");
    createBanner({ position: form.position || "home_hero", image: form.image, link: form.link || null, sort: Number(form.sort || 0) })
      .then(() => { setShow(false); setForm({}); refresh(); })
      .catch((e: Error) => setErr(e.message));
  };

  return (
    <div className="admin-page">
      <div className="admin-page-head">
        <h2>内容管理</h2>
        <div className="seg">
          <button className={tab === "articles" ? "on" : ""} onClick={() => setTab("articles")}>资讯</button>
          <button className={tab === "banners" ? "on" : ""} onClick={() => setTab("banners")}>Banner</button>
        </div>
      </div>

      {tab === "articles" ? (
        <section className="panel">
          <h3>资讯 <button className="btn-gold sm" onClick={() => setShow(true)}>+ 新增资讯</button></h3>
          <table className="admin-table">
            <thead><tr><th>标题</th><th>分类</th><th>状态</th><th>置顶</th><th>操作</th></tr></thead>
            <tbody>
              {articles.map((a) => (
                <tr key={a.id}><td>{a.title_zh}</td><td>{a.category}</td><td>{a.status}</td><td>{a.is_top ? "是" : "否"}</td><td><button className="btn-danger sm" onClick={() => deleteArticle(a.id).then(refresh)}>删除</button></td></tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : (
        <section className="panel">
          <h3>Banner <button className="btn-gold sm" onClick={() => setShow(true)}>+ 新增 Banner</button></h3>
          <table className="admin-table">
            <thead><tr><th>位置</th><th>图片</th><th>链接</th><th>排序</th><th>操作</th></tr></thead>
            <tbody>
              {banners.map((b) => (
                <tr key={b.id}><td>{b.position}</td><td>{b.image}</td><td>{b.link || "—"}</td><td>{b.sort}</td><td><button className="btn-danger sm" onClick={() => deleteBanner(b.id).then(refresh)}>删除</button></td></tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {show && (
        <div className="admin-modal">
          <div className="modal-card">
            <h3>新增{tab === "articles" ? "资讯" : "Banner"}</h3>
            {tab === "articles" ? (
              <>
                <label>中文标题 <input value={form.zh || ""} onChange={(e) => setForm({ ...form, zh: e.target.value })} /></label>
                <label>英文标题 <input value={form.en || ""} onChange={(e) => setForm({ ...form, en: e.target.value })} /></label>
                <label>摘要 <input value={form.summary || ""} onChange={(e) => setForm({ ...form, summary: e.target.value })} /></label>
                <label>封面URL <input value={form.cover || ""} onChange={(e) => setForm({ ...form, cover: e.target.value })} /></label>
                <label>状态 <select value={form.status || "draft"} onChange={(e) => setForm({ ...form, status: e.target.value })}><option value="draft">草稿</option><option value="published">已发布</option></select></label>
              </>
            ) : (
              <>
                <label>位置 <input value={form.position || "home_hero"} onChange={(e) => setForm({ ...form, position: e.target.value })} /></label>
                <label>图片URL <input value={form.image || ""} onChange={(e) => setForm({ ...form, image: e.target.value })} /></label>
                <label>链接 <input value={form.link || ""} onChange={(e) => setForm({ ...form, link: e.target.value })} /></label>
                <label>排序 <input type="number" value={form.sort || "0"} onChange={(e) => setForm({ ...form, sort: e.target.value })} /></label>
              </>
            )}
            {err && <div className="admin-error">{err}</div>}
            <div className="modal-actions">
              <button className="btn-gold" onClick={tab === "articles" ? submitArticle : submitBanner}>保存</button>
              <button className="btn-ghost" onClick={() => { setShow(false); setErr(""); }}>取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
