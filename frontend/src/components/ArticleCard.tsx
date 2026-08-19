// =============================================================
// 段功能：资讯卡片组件（M2 首页/资讯列表）
// 说明：展示封面 + 分类 + 标题 + 摘要；点击进入资讯详情。
// =============================================================

import { Link } from "react-router-dom";
import type { ArticleListItem } from "../api/public";

export default function ArticleCard({ article }: { article: ArticleListItem }) {
  return (
    <Link className="article-card" to={`/news/${article.id}`}>
      <div className="article-card__media">
        {article.cover_url ? (
          <img src={article.cover_url} alt={article.title || ""} />
        ) : (
          <div className="article-card__ph" />
        )}
      </div>
      <div className="article-card__body">
        <div className="article-card__cat">{article.category}</div>
        <div className="article-card__title">{article.title}</div>
        <div className="article-card__summary">{article.summary}</div>
      </div>
    </Link>
  );
}
