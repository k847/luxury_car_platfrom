// =============================================================
// 段功能：M2 公开端 API 封装（对应后端 /api/v1/brands /models /articles /banners）
// 说明：每个函数对应一个公开接口，返回类型严格对齐《开发技术文档》§7.1/7.2/7.3/7.9。
//   request 拦截器已解包 {code,message,data} 信封，这里直接得到 data 部分。
//   语言参数 lang 取自当前 i18n 语言，确保前端语言与后端返回文案一致。
// =============================================================

import request from "./request";
import i18n from "../i18n";

// ---------- 响应数据类型（对齐后端 schemas_public.py） ----------
export interface Brand {
  id: number;
  brand_code: string | null;
  logo: string | null;
  country: string | null;
  name_zh: string | null;
  name_en: string | null;
  sort: number | null;
}

export interface ModelListItem {
  id: number;
  brand_name: string | null;
  series_name: string | null;
  model_name: string | null;
  cover_image: string | null;
  guide_price: number | null;
  fuel_type: string | null;
  segment: string | null;
  is_recommended: number | null;
}

export interface ModelListData {
  list: ModelListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface TrimBrief {
  trim_name: string | null;
  price: number | null;
  power: string | null;
  transmission: string | null;
  drive: string | null;
}

export interface ColorOption {
  name: string | null;
  swatch: string | null;
  price_delta: number | null;
}

export interface DealerBrief {
  id: number;
  name: string | null;
  city: string | null;
}

export interface ModelBody {
  length: number | null;
  width: number | null;
  height: number | null;
  wheelbase: number | null;
  trunk: number | null;
}

export interface ModelDetail {
  id: number;
  model_name: string | null;
  guide_price: number | null;
  body: ModelBody | null;
  cover_image: string | null;
  gallery: string[];
  trims: TrimBrief[];
  colors: ColorOption[];
  dealers: DealerBrief[];
  finance_available: boolean;
}

export interface ArticleListItem {
  id: number;
  category: string | null;
  cover_url: string | null;
  title: string | null;
  summary: string | null;
  published_at: string | null;
  is_top: number | null;
  is_recommended: number | null;
  author: string | null;
  source: string | null;
}

export interface ArticleListData {
  list: ArticleListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface ArticleDetail {
  id: number;
  category: string | null;
  cover_url: string | null;
  title: string | null;
  summary: string | null;
  body: string | null;
  published_at: string | null;
  author: string | null;
  source: string | null;
}

export interface Banner {
  id: number;
  position: string | null;
  image: string | null;
  link: string | null;
  sort: number | null;
}

// ---------- 查询参数类型 ----------
export interface ModelQuery {
  brand?: string;
  segment?: string;
  fuel_type?: string;
  price_min?: number;
  price_max?: number;
  country?: string;
  sort?: string;
  page?: number;
  page_size?: number;
}

export interface ArticleQuery {
  category?: string;
  page?: number;
  page_size?: number;
}

/** 取当前 i18n 语言，供接口 lang 参数使用（zh/en 回退） */
function currentLang(): string {
  return i18n.language.startsWith("zh") ? "zh" : "en";
}

/**
 * 统一 GET 封装：request 拦截器已返回 data，这里用类型断言让 TS 拿到正确的数据类型。
 */
function apiGet<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  return request.get(url, { params }) as unknown as Promise<T>;
}

// ---------- 接口函数 ----------
export const getBrands = () => apiGet<Brand[]>("/api/v1/brands", { lang: currentLang() });

export const getModels = (q: ModelQuery) =>
  apiGet<ModelListData>("/api/v1/models", { ...q, lang: currentLang() });

export const getModel = (id: number | string) =>
  apiGet<ModelDetail>(`/api/v1/models/${id}`, { lang: currentLang() });

export const getArticles = (q: ArticleQuery) =>
  apiGet<ArticleListData>("/api/v1/articles", { ...q, lang: currentLang() });

export const getArticle = (id: number | string) =>
  apiGet<ArticleDetail>(`/api/v1/articles/${id}`, { lang: currentLang() });

export const getBanners = (position?: string) =>
  apiGet<Banner[]>("/api/v1/banners", position ? { position } : undefined);

// ---------- M3 选车深化类型（对齐后端 schemas_public.py §7.4–7.7） ----------
export interface OptionBrief {
  id: number;
  name: string | null;
  swatch: string | null;
  price_delta: number | null;
  stock_status: string | null;
  lead_time: number | null;
  is_default: number | null;
}

export interface OptionGroupOut {
  group_code: string;
  name: string | null;
  is_required: number | null;
  max_select: number | null;
  options: OptionBrief[];
}

export interface ConfiguratorData {
  base_price: number | null;
  groups: OptionGroupOut[];
}

export interface QuoteSelection {
  color?: number | null;
  wheel?: number | null;
  interior?: number | null;
  packages?: number[];
}

export interface QuoteRequest {
  model_id: number;
  selections: QuoteSelection;
}

export interface QuoteDelta {
  group: string;
  option: string;
  price_delta: number;
}

export interface QuoteResult {
  base_price: number;
  deltas: QuoteDelta[];
  total: number;
  stock_status: string;
  max_lead_time: number;
}

export interface CompareItem {
  id: number;
  model_name: string | null;
  guide_price: number | null;
  fuel_type: string | null;
  segment: string | null;
  body: ModelBody | null;
  power: string | null;
  trims_count: number;
}

export interface FinanceParam {
  term_months: number;
  annual_rate: number;
  product_name: string | null;
}

export interface TestDriveLeadRequest {
  name: string;
  phone: string;
  city?: string | null;
  brand_id?: number | null;
  model_id?: number | null;
  preferred_dealer_id?: number | null;
  preferred_time?: string | null;
  remark?: string | null;
  config_summary?: unknown;
}

export interface InquiryLeadRequest {
  name: string;
  phone: string;
  intent: string;
  city?: string | null;
  brand_id?: number | null;
  model_id?: number | null;
  remark?: string | null;
}

export interface LeadResponse {
  lead_id: number;
  message: string;
}

/**
 * 统一 POST 封装：request 拦截器已解包信封，这里直接得到 data。
 */
function apiPost<T>(url: string, data?: unknown): Promise<T> {
  return request.post(url, data) as unknown as Promise<T>;
}

// ---------- M3 接口函数 ----------
export const getConfigurator = (id: number | string) =>
  apiGet<ConfiguratorData>(`/api/v1/models/${id}/configurator`, { lang: currentLang() });

export const getQuote = (req: QuoteRequest) =>
  apiPost<QuoteResult>("/api/v1/configurator/quote", req);

export const getCompare = (ids: number[]) =>
  apiGet<CompareItem[]>(`/api/v1/models/compare`, { ids: ids.join(","), lang: currentLang() });

export const getFinanceParams = () =>
  apiGet<FinanceParam[]>("/api/v1/finance/params");

export const postTestDrive = (req: TestDriveLeadRequest) =>
  apiPost<LeadResponse>("/api/v1/leads/test-drive", req);

export const postInquiry = (req: InquiryLeadRequest) =>
  apiPost<LeadResponse>("/api/v1/leads/inquiry", req);
