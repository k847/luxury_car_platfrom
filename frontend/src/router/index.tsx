// =============================================================
// 段功能：前台路由配置（M2 接入真实页面）
// 说明：把 M1 的占位路由替换为真实页面组件：
//   首页 / 车型列表 / 车型详情 / 资讯列表 / 资讯详情。
//   路径常量集中管理，与导航栏、卡片跳转保持一致。
// =============================================================

import { Routes, Route } from "react-router-dom";
import HomePage from "../pages/HomePage";
import ModelListPage from "../pages/ModelListPage";
import ModelDetailPage from "../pages/ModelDetailPage";
import ArticleListPage from "../pages/ArticleListPage";
import ArticleDetailPage from "../pages/ArticleDetailPage";
import ConfiguratorPage from "../pages/ConfiguratorPage";
import ComparePage from "../pages/ComparePage";
import TestDrivePage from "../pages/TestDrivePage";
import InquiryPage from "../pages/InquiryPage";
import AdminLogin from "../pages/admin/AdminLogin";
import AdminLayout from "../pages/admin/AdminLayout";
import AdminDashboard from "../pages/admin/AdminDashboard";
import AdminModels from "../pages/admin/AdminModels";
import AdminContent from "../pages/admin/AdminContent";
import AdminLeads from "../pages/admin/AdminLeads";
import AdminDealers from "../pages/admin/AdminDealers";
import AdminSystem from "../pages/admin/AdminSystem";

// 路由表：路径常量集中管理，避免各处硬编码
export const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/models" element={<ModelListPage />} />
    <Route path="/models/:id" element={<ModelDetailPage />} />
    {/* M3 配置器（5 步 + 实时算价 + 金融计算器） */}
    <Route path="/models/:id/configurator" element={<ConfiguratorPage />} />
    {/* M3 车型对比 */}
    <Route path="/compare" element={<ComparePage />} />
    {/* M3 留资：试驾 / 询价 */}
    <Route path="/lead/test-drive" element={<TestDrivePage />} />
    <Route path="/lead/inquiry" element={<InquiryPage />} />
    <Route path="/news" element={<ArticleListPage />} />
    <Route path="/news/:id" element={<ArticleDetailPage />} />

    {/* M4 后台（门控布局） */}
    <Route path="/admin/login" element={<AdminLogin />} />
    <Route path="/admin" element={<AdminLayout />}>
      <Route path="dashboard" element={<AdminDashboard />} />
      <Route path="models" element={<AdminModels />} />
      <Route path="content" element={<AdminContent />} />
      <Route path="leads" element={<AdminLeads />} />
      <Route path="dealers" element={<AdminDealers />} />
      <Route path="system" element={<AdminSystem />} />
    </Route>

    {/* 未匹配路由回首页 */}
    <Route path="*" element={<HomePage />} />
  </Routes>
);
