// =============================================================
// 段功能：前台根布局（M1 脚手架）
// 说明：提供站点外壳：顶部导航（含中英文切换）+ 内容区（路由出口）+ 页脚。
//       页面具体内容在 M2（首页/列表/详情）与 M3（配置器/计算器）逐步实现。
// =============================================================

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { AppRoutes } from "./router";
import { toggleLang } from "./i18n";

export default function App() {
  // useTranslation 提供 t（翻译函数）与 i18n 实例
  const { t, i18n } = useTranslation();
  // M5 手机端汉堡菜单展开态
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="app-shell">
      {/* 顶部导航 */}
      <header className="app-header">
        <button
          className="hamburger"
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="menu"
          aria-expanded={menuOpen}
        >
          <span />
          <span />
          <span />
        </button>
        <div className="brand">REGALIA MOTORS · 冠驭名车</div>
        <nav className={`app-nav ${menuOpen ? "open" : ""}`}>
          <Link to="/" onClick={() => setMenuOpen(false)}>{t("nav.home")}</Link>
          <Link to="/models" onClick={() => setMenuOpen(false)}>{t("nav.models")}</Link>
          <Link to="/news" onClick={() => setMenuOpen(false)}>{t("nav.news")}</Link>
        </nav>
        {/* 中英文切换按钮 */}
        <button
          className="lang-switch"
          onClick={() => toggleLang(i18n.language)}
          aria-label="切换语言"
        >
          {i18n.language.startsWith("zh") ? "EN" : "中"}
        </button>
      </header>

      {/* 路由出口：根据 URL 渲染对应页面（当前为占位） */}
      <main className="app-main">
        <AppRoutes />
      </main>

      <footer className="app-footer">© 2026 REGALIA MOTORS</footer>
    </div>
  );
}
