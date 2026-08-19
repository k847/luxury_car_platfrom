// =============================================================
// 段功能：首页（M2）
// 说明：组合 Hero/Banner 轮播 + 品牌墙 + 推荐车型 + 最新资讯。
//       首屏并行请求 4 个公开接口，加载完成前显示 loading。
// =============================================================

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import BannerCarousel from "../components/Banner";
import BrandWall from "../components/BrandWall";
import ModelCard from "../components/ModelCard";
import ArticleCard from "../components/ArticleCard";
import {
  getBanners,
  getBrands,
  getModels,
  getArticles,
  type Banner,
  type Brand,
  type ModelListItem,
  type ArticleListItem,
} from "../api/public";

export default function HomePage() {
  const { t } = useTranslation();
  const [banners, setBanners] = useState<Banner[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [models, setModels] = useState<ModelListItem[]>([]);
  const [articles, setArticles] = useState<ArticleListItem[]>([]);
  const [loading, setLoading] = useState(true);

  // 并行拉取首页数据；组件卸载时通过 active 标志避免 setState
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [b, br, m, a] = await Promise.all([
          getBanners("home_hero"),
          getBrands(),
          getModels({ page: 1, page_size: 8 }),
          getArticles({ page: 1, page_size: 3 }),
        ]);
        if (!active) return;
        setBanners(b);
        setBrands(br);
        setModels(m.list);
        setArticles(a.list);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="home">
      <BannerCarousel banners={banners} />

      <BrandWall brands={brands} />

      <section className="section">
        <div className="section__head">
          <h2 className="section__title">{t("home.recommended")}</h2>
          <Link className="section__more" to="/models">
            {t("home.viewAll")}
          </Link>
        </div>
        {loading ? (
          <div className="loading">{t("common.loading")}</div>
        ) : (
          <div className="model-grid">
            {models.map((m) => (
              <ModelCard key={m.id} model={m} />
            ))}
          </div>
        )}
      </section>

      <section className="section">
        <div className="section__head">
          <h2 className="section__title">{t("home.latestNews")}</h2>
          <Link className="section__more" to="/news">
            {t("home.viewAll")}
          </Link>
        </div>
        {loading ? (
          <div className="loading">{t("common.loading")}</div>
        ) : (
          <div className="article-grid">
            {articles.map((a) => (
              <ArticleCard key={a.id} article={a} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
