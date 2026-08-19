// =============================================================
// 段功能：车型详情页（M2，对应 §7.3）
// 说明：展示封面/图库/车身尺寸/配置版本/颜色/在售经销商/金融入口。
//       数据缺失或下架时显示 notFound 并引导返回列表。
// =============================================================

import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getModel, type ModelDetail } from "../api/public";
import { formatPrice } from "../utils/format";

export default function ModelDetailPage() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<ModelDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setNotFound(false);
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
    return () => {
      active = false;
    };
  }, [id]);

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
  return (
    <div className="detail-page">
      <button className="btn-ghost" onClick={() => navigate(-1)}>
        ‹ {t("modelDetail.back")}
      </button>

      <div className="detail-hero">
        {detail.cover_image ? (
          <img src={detail.cover_image} alt={detail.model_name || ""} />
        ) : (
          <div className="detail-hero__ph">REGALIA</div>
        )}
      </div>

      <h1 className="detail-title">{detail.model_name}</h1>
      <div className="detail-price">
        {t("models.guidePrice")}{" "}
        <strong>{detail.guide_price != null ? formatPrice(detail.guide_price) : "—"}</strong>
      </div>

      {/* 图库 */}
      {detail.gallery.length > 0 && (
        <section className="section">
          <h3 className="section__title">{t("modelDetail.gallery")}</h3>
          <div className="gallery">
            {detail.gallery.map((g, i) => (
              <img key={i} className="gallery__img" src={g} alt="" />
            ))}
          </div>
        </section>
      )}

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

      {/* 选车与咨询：配置器 / 试驾 / 询价 / 对比 入口（M3 接入） */}
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
        {/* 金融入口（M3 已接入，跳配置器页内金融计算器） */}
        {detail.finance_available && (
          <p className="summary-hint">
            {t("modelDetail.finance")}：{t("configurator.title")} · {t("finance.monthly")}
          </p>
        )}
      </section>
    </div>
  );
}
