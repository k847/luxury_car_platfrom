// =============================================================
// 段功能：品牌墙组件（M2 首页）
// 说明：展示全部品牌（Logo + 名称），点击跳转到该品牌的车型列表。
//       名称按当前语言取 name_zh / name_en。
// =============================================================

import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { Brand } from "../api/public";

export default function BrandWall({ brands }: { brands: Brand[] }) {
  const { t, i18n } = useTranslation();

  // 按当前语言取品牌名，回退到另一语种或编码
  const nameOf = (b: Brand): string =>
    (i18n.language.startsWith("zh") ? b.name_zh : b.name_en) ||
    b.name_zh ||
    b.name_en ||
    b.brand_code ||
    "";

  return (
    <section className="section">
      <h2 className="section__title">{t("home.brands")}</h2>
      <div className="brand-wall">
        {brands.map((b) => (
          <Link key={b.id} className="brand-card" to={`/models?brand=${b.brand_code}`}>
            {b.logo ? (
              <img className="brand-card__logo" src={b.logo} alt={nameOf(b)} />
            ) : null}
            <span className="brand-card__name">{nameOf(b)}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
