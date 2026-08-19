// =============================================================
// 段功能：车型列表页（M2，对应 §7.2）
// 说明：支持 URL 参数 brand（来自首页品牌墙）与筛选栏；分页通过 URL page 参数驱动。
//       切换筛选时回到第 1 页，避免停留在越界页。
// =============================================================

import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import FilterBar from "../components/FilterBar";
import ModelCard from "../components/ModelCard";
import Pagination from "../components/Pagination";
import { getModels, type ModelListData } from "../api/public";

const MAX_COMPARE = 5;

export default function ModelListPage() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const brand = params.get("brand") || undefined;
  const page = Number(params.get("page") || "1");

  const [data, setData] = useState<ModelListData>({ list: [], total: 0, page: 1, page_size: 12 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<{ segment?: string; fuel_type?: string; sort?: string }>({});

  // M3 对比：已勾选的车型 id 集合（存内存，翻页/筛选不保留）
  const [compare, setCompare] = useState<number[]>([]);

  // 监听 brand / page / filters 变化，重新拉取列表
  useEffect(() => {
    let active = true;
    setLoading(true);
    getModels({ brand, page, page_size: 12, ...filters }).then((d) => {
      if (active) {
        setData(d);
        setLoading(false);
      }
    });
    return () => {
      active = false;
    };
  }, [brand, page, filters]);

  // 筛选变更：合并补丁、清除空值、回到第 1 页
  const onFilter = (patch: Record<string, string>) => {
    const next = { ...filters, ...patch };
    (Object.keys(next) as (keyof typeof next)[]).forEach((k) => {
      if (!next[k]) delete next[k];
    });
    setFilters(next);
    const p = new URLSearchParams(params);
    p.delete("page");
    setParams(p, { replace: true });
  };

  // 翻页：写入 URL page 参数
  const onPage = (p: number) => {
    const np = new URLSearchParams(params);
    np.set("page", String(p));
    setParams(np);
  };

  // 对比勾选：加入/移除，最多 5 个
  const onCompare = (id: number) => {
    setCompare((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, id];
    });
  };

  return (
    <div className="list-page">
      <h1 className="page-title">{t("models.title")}</h1>
      <FilterBar value={filters} onChange={onFilter} />
      <div className="list-meta">{t("models.results", { count: data.total })}</div>

      {loading ? (
        <div className="loading">{t("common.loading")}</div>
      ) : data.list.length === 0 ? (
        <div className="empty">{t("models.noResult")}</div>
      ) : (
        <div className="model-grid">
          {data.list.map((m) => (
            <ModelCard
              key={m.id}
              model={m}
              selected={compare.includes(m.id)}
              onCompare={onCompare}
            />
          ))}
        </div>
      )}

      <Pagination page={data.page} pageSize={data.page_size} total={data.total} onChange={onPage} />

      {/* 底部对比栏：展示已选数量并提供查看/清空 */}
      {compare.length > 0 && (
        <div className="compare-bar">
          <span>
            {t("compare.title")} · {compare.length}/{MAX_COMPARE}
          </span>
          <Link className="btn-gold" to={`/compare?ids=${compare.join(",")}`}>
            {t("compare.title")} →
          </Link>
          <button className="btn-ghost" onClick={() => setCompare([])}>
            {t("compare.clear")}
          </button>
        </div>
      )}
    </div>
  );
}
