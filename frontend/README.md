# 前台（React 18 + Vite + TypeScript）· M1 脚手架

> 技术栈：React 18 + Vite 5 + TypeScript + react-router-dom 6 + axios + react-i18next。

## 已完成（M1）
- 工程脚手架：`package.json` / `vite.config.ts` / `tsconfig*.json` / `index.html`
- 多语言基建：`src/i18n`（中英双语资源 + `toggleLang` 切换）
- 路由基建：`src/router`（集中路由表 + 占位页面，待 M2/M3 填充真实页）
- 请求封装：`src/api/request.ts`（Axios 实例 + token 拦截 + 统一信封解包 + 401 处理）
- 设计令牌：`src/theme/tokens.ts`（墨黑 #0E0E10 + 香槟金 #C2A36B）
- 全局样式：`src/styles/global.css`（CSS 变量镜像令牌 + 深色奢华风格重置）

## 本地运行
```bash
# 1. 安装依赖
npm install

# 2. 配置环境变量
cp .env.example .env

# 3. 启动开发服务器
npm run dev
```
访问 http://localhost:5173 查看占位页与语言切换效果。

## 对接后端
- 开发期 `vite.config.ts` 已配置 `/api` → `http://localhost:8000` 代理；
  也可直接设置 `.env` 的 `VITE_API` 指向后端地址。
- 登录态 token 存于 `localStorage`（access_token / refresh_token），由 `request.ts` 自动附带。

## 说明
- 页面内容（首页/Hero、车型列表/详情、资讯、配置器、计算器）在 M2/M3 实现，M1 仅打通工程与基建。
