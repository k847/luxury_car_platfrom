// =============================================================
// 段功能：首页 Hero / Banner 轮播组件（M2）
// 说明：接收后台 Banner 列表，自动轮播展示；无 Banner 时降级为纯文字 Hero。
//       点击进入 link（默认 /models）。暗黑奢华风格：墨黑底 + 香槟金按钮。
// =============================================================

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Banner } from "../api/public";

export default function Banner({ banners }: { banners: Banner[] }) {
  const { t } = useTranslation();
  const [idx, setIdx] = useState(0);

  // 多张 Banner 时间隔 5 秒自动切换；单张或不切换时不启定时器
  useEffect(() => {
    if (banners.length <= 1) return;
    const timer = setInterval(() => setIdx((i) => (i + 1) % banners.length), 5000);
    return () => clearInterval(timer);
  }, [banners.length]);

  // 无数据时：纯文字 Hero，避免空白
  if (banners.length === 0) {
    return (
      <section className="hero hero--empty">
        <h1 className="hero__title">{t("home.heroTitle")}</h1>
        <p className="hero__sub">{t("home.heroSubtitle")}</p>
        <a className="btn-gold" href="/models">
          {t("home.explore")}
        </a>
      </section>
    );
  }

  const current = banners[idx];
  return (
    <section className="hero" style={{ backgroundImage: `url(${current.image})` }}>
      {/* 暗色遮罩，保证文字可读 */}
      <div className="hero__mask" />
      <div className="hero__content">
        <h1 className="hero__title">{t("home.heroTitle")}</h1>
        <p className="hero__sub">{t("home.heroSubtitle")}</p>
        <a className="btn-gold" href={current.link || "/models"}>
          {t("home.explore")}
        </a>
      </div>
      {/* 轮播指示点 */}
      <div className="hero__dots">
        {banners.map((_, i) => (
          <span
            key={i}
            className={i === idx ? "dot dot--on" : "dot"}
            onClick={() => setIdx(i)}
            role="button"
            aria-label={`banner ${i + 1}`}
          />
        ))}
      </div>
    </section>
  );
}
