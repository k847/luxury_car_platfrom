// =============================================================
// 段功能：车型对比页（M3，对应 §7.6）
// 说明：接收 URL ?ids=101,102,103，调用 /models/compare 返回对比项；
//       逐行展示名称/价格/能源/级别/车身尺寸/动力/配置版本数，缺失项显示"—"。
// =============================================================

import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getCompare, type CompareItem } from "../api/public";
import { formatPrice } from "../utils/format";

export default function ComparePage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const rawIds = (params.get("ids") || "").split(",").map((s) => Number(s.trim())).filter((n) => !isNaN(n));
  const [items, setItems] = useState<CompareItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (rawIds.length === 0) {
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    getCompare(rawIds).then((d) => {
      if (active) {
        setItems(d);
        setLoading(false);
      }
    });
    return () => {
      active = false;
    };
  }, [rawIds.join(",")]);

  if (loading) return <div className="loading">{t("common.loading")}</div>;

  if (rawIds.length < 2) {
    return (
      <div className="compare-page">
        <h1 className="page-title">{t("compare.title")}</h1>
        <div className="empty">
          {t("compare.empty")}
          <br />
          <Link to="/models">{t("compare.addHint")}</Link>
        </div>
      </div>
    );
  }

  // 行定义：标签 + 取值函数
  const rows: Array<{ label: string; get: (c: CompareItem) => string }> = [
    { label: t("configurator.title"), get: (c) => c.model_name || "—" },
    { label: t("compare.guidePrice"), get: (c) => (c.guide_price != null ? formatPrice(c.guide_price) : "—") },
    { label: t("compare.fuel"), get: (c) => c.fuel_type || "—" },
    { label: t("compare.segment"), get: (c) => c.segment || "—" },
    {
      label: t("compare.body"),
      get: (c) =>
        c.body
          ? `${c.body.length ?? "—"}×${c.body.width ?? "—"}×${c.body.height ?? "—"} (${c.body.wheelbase ?? "—"})`
          : "—",
    },
    { label: t("compare.power"), get: (c) => c.power || "—" },
    { label: t("compare.trims"), get: (c) => String(c.trims_count) },
  ];

  return (
    <div className="compare-page">
      <h1 className="page-title">{t("compare.title")}</h1>
      <table className="compare-table">
        <thead>
          <tr>
            <th />
            {items.map((c) => (
              <th key={c.id}>
                <Link to={`/models/${c.id}`}>{c.model_name || `#${c.id}`}</Link>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <th className="row-label">{r.label}</th>
              {items.map((c) => (
                <td key={c.id}>{r.get(c)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
