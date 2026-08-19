// =============================================================
// 段功能：资讯详情页（M2，对应 §7.9）
// 说明：展示标题/元信息/封面/正文（富文本）。正文本来自可信 CMS，直接渲染；
//       若未来接入外部来源，需在此加 DOMPurify 等消毒处理以防 XSS。
// =============================================================

import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getArticle, type ArticleDetail } from "../api/public";

export default function ArticleDetailPage() {
  const { id } = useParams();
  const { t } = useTranslation();
  const [detail, setDetail] = useState<ArticleDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setNotFound(false);
    getArticle(id!)
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
        {t("articles.notFound")}
        <br />
        <Link to="/news">{t("articles.back")}</Link>
      </div>
    );

  return (
    <article className="article-detail">
      <Link className="btn-ghost" to="/news">
        ‹ {t("articles.back")}
      </Link>
      <h1 className="article-detail__title">{detail.title}</h1>
      <div className="article-detail__meta">
        {detail.author}
        {detail.published_at ? ` · ${detail.published_at}` : ""}
        {detail.source ? ` · ${detail.source}` : ""}
      </div>
      {detail.cover_url && <img className="article-detail__cover" src={detail.cover_url} alt="" />}
      {/* 正文为富文本，来自可信 CMS，直接渲染 */}
      <div className="article-detail__body" dangerouslySetInnerHTML={{ __html: detail.body || "" }} />
    </article>
  );
}
