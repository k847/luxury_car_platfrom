// =============================================================
// 段功能：i18n 初始化（M1 基建）
// 说明：集成 i18next + react-i18next，注册中英双语资源。
//       默认语言 zh，提供 toggleLang 供导航栏切换。
//       与后端 *_i18n 表的双语策略一致（前端的文案 key ↔ 后端的 lang 字段）。
// =============================================================

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import zh from "./locales/zh";
import en from "./locales/en";

// 初始化 i18next
i18n.use(initReactI18next).init({
  resources: {
    zh: { translation: zh },
    en: { translation: en },
  },
  lng: "zh", // 默认中文
  fallbackLng: "en", // 缺译文时回退英文
  interpolation: { escapeValue: false }, // React 已做 XSS 转义，关闭 i18next 转义
});

/**
 * 语言切换辅助：在 zh / en 之间来回切。
 * @param current 当前语言代码
 */
export function toggleLang(current: string): void {
  const next = current.startsWith("zh") ? "en" : "zh";
  i18n.changeLanguage(next);
}

export default i18n;
