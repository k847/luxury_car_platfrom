// =============================================================
// 段功能：车型详情页（M2，对应 §7.3；M6 升级：大图集切换 + 收藏 + 相似推荐）
// 说明：大图集（主图+缩略图切换）、车身尺寸/配置版本/颜色/经销商、
//       收藏（localStorage）、相似车型横向推荐、配置/留资入口。
// =============================================================

import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getModel, getModels, type ModelDetail, type ModelListItem } from "../api/public";
import { formatPrice } from "../utils/format";
import LazyImage from "../components/LazyImage";
import ModelCard from "../components/ModelCard";

const FAV_KEY = "fav_models";

function loadFavs(): number[] {
  try {
    return JSON.parse(localStorage.getItem(FAV_KEY) || "[]") as number[];
  } catch {
    return [];
  }
}

export default function ModelDetailPage() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<ModelDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [galleryIdx, setGalleryIdx] = useState(0);
  const [fav, setFav] = useState(false);
  const [related, setRelated] = useState<ModelListItem[]>([]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setNotFound(false);
    setGalleryIdx(0);
    setFav(loadFavs().includes(Number(id)));
    getModel(id!)
      .then((d) => {
        if (active) {
          setDetail(d);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) {
          setNotFound(true);
          setLoading(false);
        }
      });
    // 相似推荐：同页拉取推荐车型，排除当前
    getModels({ page: 1, page_size: 6 })
      .then((r) => {
        if (active) setRelated(r.list.filter((m) => m.id !== Number(id)).slice(0, 4));
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [id]);

  const toggleFav = () => {
    const next = !fav;
    setFav(next);
    const list = loadFavs();
    const cur = Number(id);
    const idx = list.indexOf(cur);
    if (next && idx < 0) list.push(cur);
    if (!next && idx >= 0) list.splice(idx, 1);
    localStorage.setItem(FAV_KEY, JSON.stringify(list));
  };

  if (loading) return <div className="loading">{t("common.loading")}</div>;
  if (notFound || !detail)
    return (
      <div className="empty">
        {t("modelDetail.notFound")}
        <br />
        <Link to="/models">{t("modelDetail.back")}</Link>
      </div>
    );

  const b = detail.body;
  const imgs = [detail.cover_image, ...detail.gallery].filter((x): x is string => !!x);
  const current = imgs[Math.min(galleryIdx, imgs.length - 1)];

  return (
    <div className="detail-page">
      <button className="btn-ghost" onClick={() => navigate(-1)}>
        ‹ {t("modelDetail.back")}
      </button>

      {/* 大图集：主图 + 缩略图切换 */}
      <div className="gallery-main">
        {current ? (
          <LazyImage src={current} alt={detail.model_name || ""} />
        ) : (
          <div className="detail-hero__ph">REGALIA</div>
        )}
      </div>
      {imgs.length > 1 && (
        <div className="gallery-thumbs">
          {imgs.map((g, i) => (
            <button
              key={i}
              className={`gallery-thumb ${i === galleryIdx ? "on" : ""}`}
              onClick={() => setGalleryIdx(i)}
            >
              <img src={g} alt="" />
            </button>
          ))}
        </div>
      )}

      <div className="detail-head">
        <div>
          <h1 className="detail-title">{detail.model_name}</h1>
          <div className="detail-price">
            {t("models.guidePrice")}{" "}
            <strong>{detail.guide_price != null ? formatPrice(detail.guide_price) : "—"}</strong>
          </div>
        </div>
        <button className={`btn-fav ${fav ? "on" : ""}`} onClick={toggleFav} aria-label="收藏">
          {fav ? "★" : "☆"}
        </button>
      </div>

      {/* 车身尺寸 */}
      <section className="section">
        <h3 className="section__title">{t("modelDetail.body")}</h3>
        <div className="spec-grid">
          <div><span>{t("modelDetail.length")}</span><b>{b?.length ?? "—"}</b></div>
          <div><span>{t("modelDetail.width")}</span><b>{b?.width ?? "—"}</b></div>
          <div><span>{t("modelDetail.height")}</span><b>{b?.height ?? "—"}</b></div>
          <div><span>{t("modelDetail.wheelbase")}</span><b>{b?.wheelbase ?? "—"}</b></div>
          <div><span>{t("modelDetail.trunk")}</span><b>{b?.trunk ?? "—"}</b></div>
        </div>
      </section>

      {/* 配置版本 */}
      {detail.trims.length > 0 && (
        <section className="section">
          <h3 className="section__title">{t("modelDetail.trims")}</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>{t("modelDetail.trims")}</th>
                <th>{t("models.guidePrice")}</th>
                <th>power</th>
                <th>drive</th>
              </tr>
            </thead>
            <tbody>
              {detail.trims.map((tr, i) => (
                <tr key={i}>
                  <td>{tr.trim_name}</td>
                  <td>{tr.price != null ? formatPrice(tr.price) : "—"}</td>
                  <td>{tr.power || "—"}</td>
                  <td>{tr.drive || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* 颜色 */}
      {detail.colors.length > 0 && (
        <section className="section">
          <h3 className="section__title">{t("modelDetail.colors")}</h3>
          <div className="color-list">
            {detail.colors.map((c, i) => (
              <div key={i} className="color-item">
                <span className="color-dot" style={{ background: c.swatch || "#999" }} />
                {c.name}
                {c.price_delta ? ` (+${formatPrice(c.price_delta)})` : ""}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 在售经销商 */}
      {detail.dealers.length > 0 && (
        <section className="section">
          <h3 className="section__title">{t("modelDetail.dealers")}</h3>
          <div className="dealer-list">
            {detail.dealers.map((d) => (
              <div key={d.id} className="dealer-item">
                {d.name}
                {d.city ? ` · ${d.city}` : ""}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 选车与咨询：配置器 / 试驾 / 询价 入口 */}
      <section className="section finance-cta">
        <h3 className="section__title">{t("modelDetail.actions")}</h3>
        <div className="detail-actions">
          <Link to={`/models/${detail.id}/configurator`} className="btn-gold">
            {t("modelDetail.configure")}
          </Link>
          <Link to={`/lead/test-drive?model=${detail.id}`} className="btn-ghost">
            {t("lead.testDriveTitle")}
          </Link>
          <Link to={`/lead/inquiry?model=${detail.id}`} className="btn-ghost">
            {t("lead.inquiryTitle")}
          </Link>
        </div>
      </section>

      {/* 相似推荐（智能推荐） */}
      {related.length > 0 && (
        <section className="section">
          <div className="section__head">
            <h3 className="section__title">{t("home.recommended")}</h3>
            <Link className="section__more" to="/models">
              {t("home.viewAll")}
            </Link>
          </div>
          <div className="scroll-row">
            {related.map((m) => (
              <ModelCard key={m.id} model={m} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
