// =============================================================
// 段功能：资讯列表页（M2，对应 §7.9）
// 说明：展示已发布资讯卡片网格；空态提示暂无资讯。
// =============================================================

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import ArticleCard from "../components/ArticleCard";
import { getArticles, type ArticleListData } from "../api/public";

export default function ArticleListPage() {
  const { t } = useTranslation();
  const [data, setData] = useState<ArticleListData>({ list: [], total: 0, page: 1, page_size: 12 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getArticles({ page: 1, page_size: 20 }).then((d) => {
      if (active) {
        setData(d);
        setLoading(false);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="list-page">
      <h1 className="page-title">{t("articles.title")}</h1>
      {loading ? (
        <div className="loading">{t("common.loading")}</div>
      ) : data.list.length === 0 ? (
        <div className="empty">{t("articles.noResult")}</div>
      ) : (
        <div className="article-grid">
          {data.list.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      )}
    </div>
  );
}
