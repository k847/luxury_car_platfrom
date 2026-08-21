// =============================================================
// 段功能：车型卡片组件（M2 列表/首页推荐；M6 升级 hover 上浮+图片懒加载）
// 说明：展示封面 + 车型名 + 品牌/车系 + 指导价；点击进入车型详情。
//       封面使用 LazyImage（懒加载 + 滚动显现），hover 上浮与图片缩放。
// =============================================================

import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { ModelListItem } from "../api/public";
import { formatPrice } from "../utils/format";
import LazyImage from "./LazyImage";

export default function ModelCard({
  model,
  selected = false,
  onCompare,
}: {
  model: ModelListItem;
  selected?: boolean;
  onCompare?: (id: number) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="model-card-wrap">
      <Link className="model-card" to={`/models/${model.id}`}>
        <div className="model-card__media">
          {model.cover_image ? (
            <LazyImage src={model.cover_image} alt={model.model_name || ""} reveal />
          ) : (
            <div className="model-card__ph">REGALIA</div>
          )}
        </div>
        <div className="model-card__body">
          <div className="model-card__name">{model.model_name}</div>
          <div className="model-card__meta">
            {model.brand_name} · {model.series_name}
          </div>
          <div className="model-card__price">
            {t("models.guidePrice")}{" "}
            {model.guide_price != null ? <strong>{formatPrice(model.guide_price)}</strong> : "—"}
          </div>
        </div>
      </Link>
      {onCompare && (
        <button
          className={`compare-toggle ${selected ? "on" : ""}`}
          onClick={() => onCompare(model.id)}
        >
          {t("compare.title")}
          {selected ? " ✓" : ""}
        </button>
      )}
    </div>
  );
}
