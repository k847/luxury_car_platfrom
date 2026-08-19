// =============================================================
// 段功能：Axios 请求封装（M1 基建）
// 说明：统一封装 API 调用，处理：
//   1. baseURL 取自 VITE_API（默认 http://localhost:8000）
//   2. 请求拦截器：自动附加 Bearer token（从 localStorage 读取）
//   3. 响应拦截器：对 401 统一清除本地登录态并跳登录
//   4. 统一返回后端 {code,message,data} 信封中的 data，便于业务直接使用
// =============================================================

import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from "axios";

// 创建 axios 实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API || "http://localhost:8000",
  timeout: 15000,
});

// 请求拦截器：附带 token
request.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

// 响应拦截器：解包信封 + 统一处理错误
request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 后端统一信封 {code,message,data}；这里直接返回 data 部分
    const body = response.data;
    if (body && typeof body === "object" && "code" in body) {
      if (body.code !== 0) {
        // 业务错误：抛出 message，交由调用方处理
        return Promise.reject(new Error(body.message || "业务错误"));
      }
      return body.data;
    }
    return body;
  },
  (error) => {
    // HTTP 层错误
    if (error.response?.status === 401) {
      // 登录失效：清理本地态（真实项目可跳登录页）
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
    return Promise.reject(error);
  }
);

export default request;
