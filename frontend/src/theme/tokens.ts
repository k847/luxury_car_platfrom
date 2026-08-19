// =============================================================
// 段功能：Design Tokens 设计变量（M1 基建）
// 说明：集中定义品牌设计令牌，作为组件样式与全局 CSS 变量的单一来源。
//       品牌色：墨黑 #0E0E10（主背景）+ 香槟金 #C2A36B（强调/主色）。
//       组件库（M2+）应引用这些 token，而非硬编码颜色，保证主题一致。
// =============================================================

export const tokens = {
  // 颜色
  color: {
    ink: "#0E0E10", // 墨黑：主背景 / 主文字反白底
    inkSoft: "#1A1A1E", // 次级背景（卡片）
    gold: "#C2A36B", // 香槟金：主强调色 / 按钮 / 分割线
    goldSoft: "#D8C39A", // 香槟金浅色（hover / 禁用）
    text: "#F5F5F7", // 主文字（深底浅字）
    textMuted: "#9A9AA0", // 次要文字
    border: "rgba(194,163,107,0.25)", // 金色低透明度边框
    danger: "#C0392B", // 错误/危险
    success: "#2E8B57", // 成功
  },
  // 间距（4 的倍数体系）
  space: {
    xs: "4px",
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "40px",
  },
  // 圆角
  radius: {
    sm: "4px",
    md: "8px",
    lg: "16px",
  },
  // 字体
  font: {
    base: "14px",
    lg: "18px",
    xl: "28px",
    family: "'PingFang SC','Microsoft YaHei',system-ui,sans-serif",
  },
} as const;

export default tokens;
