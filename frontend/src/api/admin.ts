// =============================================================
// 段功能：M4 后台管理 API 封装（对应后端 /api/v1/admin/*）
// 说明：每个函数对应一个后台接口；request 拦截器已解包 {code,message,data} 信封。
//   登录接口特殊（M1 返回裸 LoginResponse），单独处理。
// =============================================================

import request from "./request";

// ---------- 鉴权（M1） ----------
export interface LoginResult {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: { id: number; username: string; real_name: string | null; role_id: number; is_active: number };
}

/** 登录：M1 返回裸结构（无信封），直接返回 access_token 等 */
export const adminLogin = (username: string, password: string) =>
  request.post<LoginResult>("/api/v1/auth/login", { username, password }) as unknown as Promise<LoginResult>;

// ---------- 品牌 ----------
export interface AdminBrand {
  id: number;
  brand_code: string;
  logo: string | null;
  country: string | null;
  sort: number;
  is_active: number;
  name_zh: string | null;
  name_en: string | null;
}
export interface BrandPayload {
  brand_code: string;
  country?: string | null;
  logo?: string | null;
  sort?: number;
  is_active?: number;
  name_zh: string;
  name_en: string;
}
export const getBrands = () => request.get("/api/v1/admin/brands") as unknown as Promise<AdminBrand[]>;
export const createBrand = (p: BrandPayload) => request.post("/api/v1/admin/brands", p) as unknown as Promise<{ id: number }>;
export const updateBrand = (id: number, p: BrandPayload) => request.put(`/api/v1/admin/brands/${id}`, p) as unknown as Promise<{ id: number }>;
export const deleteBrand = (id: number) => request.delete(`/api/v1/admin/brands/${id}`) as unknown as Promise<null>;

// ---------- 车系 ----------
export interface AdminSeries {
  id: number;
  brand_id: number;
  series_code: string;
  segment: string | null;
  sort: number;
  is_active: number;
  name_zh: string | null;
  name_en: string | null;
}
export const getSeries = (brandId?: number) =>
  request.get("/api/v1/admin/series", brandId ? { params: { brand_id: brandId } } : undefined) as unknown as Promise<AdminSeries[]>;
export const createSeries = (p: Record<string, unknown>) => request.post("/api/v1/admin/series", p) as unknown as Promise<{ id: number }>;
export const deleteSeries = (id: number) => request.delete(`/api/v1/admin/series/${id}`) as unknown as Promise<null>;

// ---------- 车型 ----------
export interface AdminModel {
  id: number;
  series_id: number;
  model_code: string;
  fuel_type: string | null;
  guide_price: number | null;
  is_recommended: number;
  status: string;
  is_active: number;
  name_zh: string | null;
  name_en: string | null;
}
export interface ModelPayload {
  series_id: number;
  model_code: string;
  fuel_type?: string | null;
  guide_price?: number | null;
  is_recommended?: number;
  status?: string;
  is_active?: number;
  name_zh: string;
  name_en: string;
}
export const getModels = (q: { brand?: string; page?: number; page_size?: number } = {}) =>
  request.get("/api/v1/admin/models", { params: q }) as unknown as Promise<{ list: AdminModel[]; total: number; page: number; page_size: number }>;
export const createModel = (p: ModelPayload) => request.post("/api/v1/admin/models", p) as unknown as Promise<{ id: number }>;
export const updateModel = (id: number, p: ModelPayload) => request.put(`/api/v1/admin/models/${id}`, p) as unknown as Promise<{ id: number }>;
export const deleteModel = (id: number) => request.delete(`/api/v1/admin/models/${id}`) as unknown as Promise<null>;

// ---------- 资讯 / Banner ----------
export interface AdminArticle {
  id: number;
  category: string;
  status: string;
  cover_url: string | null;
  author: string | null;
  source: string | null;
  is_top: number;
  is_recommended: number;
  title_zh: string | null;
  summary_zh: string | null;
  title_en: string | null;
}
export const getArticles = (q: { category?: string; page?: number; page_size?: number } = {}) =>
  request.get("/api/v1/admin/articles", { params: q }) as unknown as Promise<{ list: AdminArticle[]; total: number; page: number; page_size: number }>;
export const createArticle = (p: Record<string, unknown>) => request.post("/api/v1/admin/articles", p) as unknown as Promise<{ id: number }>;
export const deleteArticle = (id: number) => request.delete(`/api/v1/admin/articles/${id}`) as unknown as Promise<null>;

export interface AdminBanner {
  id: number;
  position: string;
  image: string;
  link: string | null;
  sort: number;
  is_active: number;
}
export const getBanners = () => request.get("/api/v1/admin/banners") as unknown as Promise<AdminBanner[]>;
export const createBanner = (p: Record<string, unknown>) => request.post("/api/v1/admin/banners", p) as unknown as Promise<{ id: number }>;
export const deleteBanner = (id: number) => request.delete(`/api/v1/admin/banners/${id}`) as unknown as Promise<null>;

// ---------- 线索 ----------
export interface AdminLead {
  id: number;
  name: string;
  phone: string;
  city: string | null;
  model_id: number | null;
  status: string;
  owner_id: number | null;
  created_at: string | null;
  intent?: string | null;
  remark?: string | null;
}
export const getTestDriveLeads = (q: { status?: string; page?: number } = {}) =>
  request.get("/api/v1/admin/leads/test-drive", { params: q }) as unknown as Promise<{ list: AdminLead[]; total: number; page: number; page_size: number }>;
export const getInquiryLeads = (q: { status?: string; page?: number } = {}) =>
  request.get("/api/v1/admin/leads/inquiry", { params: q }) as unknown as Promise<{ list: AdminLead[]; total: number; page: number; page_size: number }>;
export const assignLead = (type: "test-drive" | "inquiry", id: number, ownerId: number | null) =>
  request.post(`/api/v1/admin/leads/${type}/${id}/assign`, { owner_id: ownerId }) as unknown as Promise<{ id: number }>;
export const advanceLead = (type: "test-drive" | "inquiry", id: number, toStatus: string) =>
  request.post(`/api/v1/admin/leads/${type}/${id}/advance`, { to_status: toStatus }) as unknown as Promise<{ id: number; status: string }>;

// ---------- 看板 ----------
export interface DashboardData {
  kpis: { leads_total: number; test_drive: number; inquiry: number; deal_rate: number };
  trend: Array<{ date: string; leads: number }>;
  by_brand: Array<{ brand: string; count: number }>;
  by_city: Array<{ city: string; count: number }>;
  funnel: Array<{ stage: string; count: number }>;
}
export const getDashboard = (range = 30) =>
  request.get("/api/v1/admin/dashboard", { params: { range } }) as unknown as Promise<DashboardData>;

// ---------- 审计 / 权限 / 系统 ----------
export const getAuditLogs = (q: { page?: number } = {}) =>
  request.get("/api/v1/admin/audit-logs", { params: q }) as unknown as Promise<{ list: Array<Record<string, unknown>>; total: number }>;
export const getPermissions = () => request.get("/api/v1/admin/permissions") as unknown as Promise<Array<{ id: number; code: string; name: string; module: string }>>;
export const getRoles = () => request.get("/api/v1/admin/roles") as unknown as Promise<Array<Record<string, unknown>>>;
export const getSystemConfig = () => request.get("/api/v1/admin/system-config") as unknown as Promise<Record<string, string>>;
export const updateSystemConfig = (values: Record<string, string>) => request.put("/api/v1/admin/system-config", { values }) as unknown as Promise<null>;
export const getSeo = () => request.get("/api/v1/admin/seo") as unknown as Promise<Record<string, string>>;
export const updateSeo = (p: Record<string, string>) => request.put("/api/v1/admin/seo", p) as unknown as Promise<null>;
