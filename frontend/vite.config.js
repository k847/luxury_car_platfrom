// =============================================================
// 段功能：Vite 构建配置（M1 脚手架）
// 说明：启用 React 插件；开发服务器端口 5173；
//       配置 /api 代理到后端 8000，避免开发期跨域（也可走 CORS）。
// =============================================================
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            // 把前台对 /api 的请求代理到后端，开发期无需处理跨域
            "/api": {
                target: "http://localhost:8000",
                changeOrigin: true,
            },
        },
    },
});
