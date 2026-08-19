/// <reference types="vite/client" />
// 段功能：Vite 客户端类型声明 + 自定义环境变量类型（M1 脚手架）
// 说明：为 import.meta.env.VITE_* 提供类型提示，避免 TS 报错。
interface ImportMetaEnv {
  readonly VITE_API: string;      // 后端 API 基址
  readonly VITE_MAP_KEY: string;  // 地图 SDK Key（M5/D5 用）
  readonly CDN_BASE: string;      // 图片 CDN 基址
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
