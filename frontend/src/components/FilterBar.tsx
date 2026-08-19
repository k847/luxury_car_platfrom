// =============================================================
// 段功能：车型列表筛选栏组件（M2）
// 说明：提供级别(segment)/能源(fuel)/排序(sort)下拉；变更时回调 onChange。
//       空选项表示“全部”。品牌筛选在首页品牌墙已通过 URL 参数带入。
// =============================================================

import { useTranslation } from "react-i18next";

const SEGMENTS = ["sedan", "suv", "coupe", "mpv", "sport"];
const FUELS = ["gasoline", "hybrid", "ev", "phev"];
const SORTS = ["default", "price", "launch", "heat"];

export default function FilterBar({
  value,
  onChange,
}: {
  value: { segment?: string; fuel_type?: string; sort?: string };
  onChange: (patch: Record<string, string>) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="filter-bar">
      <label>
        {t("models.segment")}
        <select
          value={value.segment || ""}
          onChange={(e) => onChange({ segment: e.target.value })}
        >
          <option value="">{t("models.all")}</option>
          {SEGMENTS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>

      <label>
        {t("models.fuel")}
        <select
          value={value.fuel_type || ""}
          onChange={(e) => onChange({ fuel_type: e.target.value })}
        >
          <option value="">{t("models.all")}</option>
          {FUELS.map((f) => (
            <option key={f} value={f}>
              {f}
            </option>
          ))}
        </select>
      </label>

      <label>
        {t("models.sort")}
        <select
          value={value.sort || "default"}
          onChange={(e) => onChange({ sort: e.target.value })}
        >
          {SORTS.map((s) => (
            <option key={s} value={s}>
              {t(`models.sort${s[0].toUpperCase() + s.slice(1)}`)}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
