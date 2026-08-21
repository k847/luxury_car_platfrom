// =============================================================
// 段功能：M6 升级 - 首页全屏轮播 Hero（保时捷式沉浸浏览）
// 说明：全屏(100vh)大图背景 + 渐变遮罩 + 大字标题；多图自动轮播(opacity 切换)，
//       支持左右箭头与指示点手动切换；无 Banner 时降级为纯文字 Hero。
//       动画仅动 opacity（GPU 友好），reduced-motion 下全局禁用。
// =============================================================

import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { Banner } from "../api/public";

export default function Banner({ banners }: { banners: Banner[] }) {
  const { t } = useTranslation();
  const [idx, setIdx] = useState(0);
  const timerRef = useRef<number | null>(null);

  // 自动轮播：5 秒切换；手动操作在 go() 内重置定时器
  useEffect(() => {
    if (banners.length <= 1) return;
    timerRef.current = window.setInterval(() => setIdx((i) => (i + 1) % banners.length), 5000);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [banners.length]);

  const go = (i: number) => {
    setIdx((i + banners.length) % banners.length);
    // 重置定时器，避免手动切换后立刻自动跳转
    if (timerRef.current) window.clearInterval(timerRef.current);
    if (banners.length > 1) {
      timerRef.current = window.setInterval(() => setIdx((v) => (v + 1) % banners.length), 5000);
    }
  };

  // 无数据时：纯文字 Hero
  if (banners.length === 0) {
    return (
      <section className="hero hero--empty">
        <div className="hero__mask" />
        <div className="hero__content">
          <h1 className="hero__title">{t("home.heroTitle")}</h1>
          <p className="hero__sub">{t("home.heroSubtitle")}</p>
          <Link className="btn-gold" to="/models">
            {t("home.explore")}
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="hero">
      {/* 轮播图层：仅切换 opacity */}
      {banners.map((b, i) => (
        <div
          key={b.id || i}
          className={`hero-slide ${i === idx ? "active" : ""}`}
          style={{ backgroundImage: `url(${b.image})` }}
        />
      ))}
      <div className="hero__mask" />

      {/* 主视觉文案 */}
      <div className="hero__content">
        <h1 className="hero__title">{t("home.heroTitle")}</h1>
        <p className="hero__sub">{t("home.heroSubtitle")}</p>
        <Link className="btn-gold" to={banners[idx]?.link || "/models"}>
          {t("home.explore")}
        </Link>
      </div>

      {/* 左右箭头（桌面端） */}
      {banners.length > 1 && (
        <>
          <button className="hero__arrow left" onClick={() => go(idx - 1)} aria-label="prev">
            ‹
          </button>
          <button className="hero__arrow right" onClick={() => go(idx + 1)} aria-label="next">
            ›
          </button>
        </>
      )}

      {/* 指示点 */}
      <div className="hero__dots">
        {banners.map((b, i) => (
          <span
            key={b.id || i}
            className={i === idx ? "dot dot--on" : "dot"}
            onClick={() => go(i)}
            role="button"
            aria-label={`banner ${i + 1}`}
          />
        ))}
      </div>
    </section>
  );
}
