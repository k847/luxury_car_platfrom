// =============================================================
// 段功能：前端应用入口（M1 脚手架）
// 说明：按顺序完成：
//   1. 引入 i18n 初始化（必须在渲染前，使文案立即生效）
//   2. 引入全局样式
//   3. 用 BrowserRouter 提供路由能力，渲染根组件 App
// =============================================================

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./i18n"; // 初始化多语言
import "./styles/global.css"; // 全局样式（含 Design Tokens 变量）

// 挂载到 #root
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
