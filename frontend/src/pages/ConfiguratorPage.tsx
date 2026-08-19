// =============================================================
// 段功能：在线配置器页（M3，对应 §7.4/§7.5 + UI-UX §6.4）
// 说明：5 步累积选型（车型→颜色→轮毂→内饰→选装包），useState 累积 selections；
//       每次变更实时调用 /configurator/quote 算价；内嵌金融计算器（按月供估算）；
//       完成配置携带 config_summary 跳转到 /lead/test-drive 留资。
// =============================================================

import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  getConfigurator,
  getQuote,
  getFinanceParams,
  type ConfiguratorData,
  type OptionGroupOut,
  type QuoteSelection,
  type QuoteResult,
  type FinanceParam,
} from "../api/public";
import { formatPrice } from "../utils/format";

// 单选项分组（max_select=1）对应的 selections 键
const SINGLE_KEYS: Record<string, "color" | "wheel" | "interior"> = {
  color: "color",
  wheel: "wheel",
  interior: "interior",
};

export default function ConfiguratorPage() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const modelId = Number(id);

  const [data, setData] = useState<ConfiguratorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [step, setStep] = useState(0); // 0=概览，1..n=各分组步骤
  const [selections, setSelections] = useState<QuoteSelection>({ packages: [] });
  const [quote, setQuote] = useState<QuoteResult | null>(null);

  const [financeParams, setFinanceParams] = useState<FinanceParam[]>([]);
  const [term, setTerm] = useState<number>(12);
  const [down, setDown] = useState<number>(30); // 首付比例 %
  const [finance, setFinance] = useState<{ monthly: number; interest: number } | null>(null);

  // 加载配置器数据 + 金融参数
  useEffect(() => {
    let active = true;
    setLoading(true);
    setNotFound(false);
    Promise.all([getConfigurator(modelId), getFinanceParams()])
      .then(([cfg, fps]) => {
        if (!active) return;
        if (!cfg || !cfg.groups || cfg.groups.length === 0) {
          setNotFound(true);
        } else {
          setData(cfg);
          if (fps && fps.length > 0) {
            setFinanceParams(fps);
            setTerm(fps[0].term_months);
          }
        }
        setLoading(false);
      })
      .catch(() => {
        if (active) {
          setNotFound(true);
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [modelId]);

  const groups = data?.groups || [];
  // 步骤：概览 + 每个分组
  const steps: Array<{ code: string; group?: OptionGroupOut }> = [
    { code: "start" },
    ...groups.map((g) => ({ code: g.group_code, group: g })),
  ];

  // 判断是否已选（单选项看 selections[键]，多选看 packages）
  const isSelected = (g: OptionGroupOut, optId: number): boolean => {
    if (g.group_code === "package") return (selections.packages || []).includes(optId);
    const key = SINGLE_KEYS[g.group_code];
    return key ? selections[key] === optId : false;
  };

  // 选择/取消选择
  const onPick = (g: OptionGroupOut, optId: number) => {
    if (g.group_code === "package") {
      const cur = selections.packages || [];
      const next = cur.includes(optId) ? cur.filter((x) => x !== optId) : [...cur, optId];
      setSelections({ ...selections, packages: next });
      return;
    }
    const key = SINGLE_KEYS[g.group_code];
    if (!key) return;
    // 单选项：再次点击同项则取消，否则替换
    setSelections({ ...selections, [key]: selections[key] === optId ? null : optId });
  };

  // 必选项是否全部满足 → 才可实时算价
  const requiredOk = useMemo(() => {
    return groups
      .filter((g) => g.is_required)
      .every((g) => (g.group_code === "package" ? (selections.packages || []).length > 0 : !!SINGLE_KEYS[g.group_code] && selections[SINGLE_KEYS[g.group_code]] != null));
  }, [groups, selections]);

  // 实时算价：必选项满足时调用 /configurator/quote
  useEffect(() => {
    if (!requiredOk) {
      setQuote(null);
      return;
    }
    let active = true;
    getQuote({ model_id: modelId, selections })
      .then((q) => active && setQuote(q))
      .catch(() => active && setQuote(null));
    return () => {
      active = false;
    };
  }, [requiredOk, selections, modelId]);

  // 金融计算：等额本息
  useEffect(() => {
    if (!quote || financeParams.length === 0) {
      setFinance(null);
      return;
    }
    const fp = financeParams.find((f) => f.term_months === term) || financeParams[0];
    const principal = quote.total * (1 - down / 100);
    const r = fp.annual_rate / 12;
    const n = fp.term_months;
    let monthly = 0;
    if (r === 0) {
      monthly = principal / n;
    } else {
      monthly = (principal * r) / (1 - Math.pow(1 + r, -n));
    }
    const interest = monthly * n - principal;
    setFinance({ monthly, interest });
  }, [quote, term, down, financeParams]);

  // 构建配置摘要（携带选中项名称）后跳转留资
  const goLead = () => {
    if (!quote) return;
    const chosen: string[] = [];
    groups.forEach((g) => g.options.forEach((o) => {
      if (isSelected(g, o.id)) chosen.push(o.name || "");
    }));
    const summary: Record<string, unknown> = {
      total: quote.total,
      stock_status: quote.stock_status,
      options: chosen,
    };
    navigate("/lead/test-drive", { state: { model_id: modelId, config_summary: summary } });
  };

  if (loading) return <div className="loading">{t("common.loading")}</div>;
  if (notFound || !data)
    return (
      <div className="empty">
        {t("modelDetail.notFound")}
        <br />
        <Link to="/models">{t("modelDetail.back")}</Link>
      </div>
    );

  const current = steps[Math.min(step, steps.length - 1)];
  const isLast = step >= steps.length - 1;

  return (
    <div className="config-page">
      <Link to={`/models/${modelId}`} className="btn-ghost">
        ‹ {t("modelDetail.back")}
      </Link>
      <h1 className="page-title">{t("configurator.title")}</h1>

      {/* 步骤指示 */}
      <div className="steps">
        {steps.map((s, i) => (
          <button
            key={s.code}
            className={`step ${i === step ? "active" : ""} ${i < step ? "done" : ""}`}
            onClick={() => setStep(i)}
          >
            {i + 1}. {s.code === "start" ? t("configurator.start") : s.group?.name || s.code}
          </button>
        ))}
      </div>

      <div className="config-body">
        {/* 左：步骤内容 */}
        <section className="config-main">
          {current.code === "start" ? (
            <div className="config-start">
              <p>{t("configurator.basePrice")}：<strong>{formatPrice(data.base_price || 0)}</strong></p>
              <button className="btn-gold" onClick={() => setStep(1)}>
                {t("configurator.start")}
              </button>
            </div>
          ) : (
            <div className="config-group">
              <h3 className="section__title">{current.group?.name}</h3>
              <div className="opt-grid">
                {current.group?.options.map((o) => (
                  <button
                    key={o.id}
                    className={`opt ${isSelected(current.group!, o.id) ? "sel" : ""}`}
                    onClick={() => onPick(current.group!, o.id)}
                  >
                    {o.swatch && <span className="opt__swatch" style={{ background: o.swatch }} />}
                    <span className="opt__name">{o.name}</span>
                    {o.price_delta ? <span className="opt__delta">+{formatPrice(o.price_delta)}</span> : null}
                    {o.is_default ? <span className="opt__tag">{t("configurator.defaultTag")}</span> : null}
                    {o.stock_status === "preorder" ? <span className="opt__tag pre">{t("configurator.stockPreorder")}</span> : null}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 步骤导航 */}
          <div className="config-nav">
            <button className="btn-ghost" disabled={step === 0} onClick={() => setStep(step - 1)}>
              ‹ {t("configurator.prev")}
            </button>
            {!isLast ? (
              <button className="btn-gold" onClick={() => setStep(step + 1)}>
                {t("configurator.next")} ›
              </button>
            ) : (
              <button className="btn-gold" disabled={!quote} onClick={goLead}>
                {t("configurator.toLead")}
              </button>
            )}
          </div>
        </section>

        {/* 右：实时摘要 + 金融计算器 */}
        <aside className="config-summary">
          <div className="summary-card">
            <div className="summary-row">
              <span>{t("configurator.basePrice")}</span>
              <b>{formatPrice(quote?.base_price || data.base_price || 0)}</b>
            </div>
            <div className="summary-row total">
              <span>{t("configurator.total")}</span>
              <b>{quote ? formatPrice(quote.total) : "—"}</b>
            </div>
            {quote && (
              <>
                <div className="summary-row">
                  <span>{t("configurator.stock")}</span>
                  <b>
                    {quote.stock_status === "in_stock"
                      ? t("configurator.stockInStock")
                      : quote.stock_status === "preorder"
                      ? t("configurator.stockPreorder")
                      : t("configurator.stockEol")}
                  </b>
                </div>
                <div className="summary-row">
                  <span>{t("configurator.leadTime")}</span>
                  <b>{quote.max_lead_time > 0 ? `${quote.max_lead_time} ${t("configurator.days")}` : "—"}</b>
                </div>
              </>
            )}
            {!requiredOk && <p className="summary-hint">{t("configurator.requiredHint")}</p>}
          </div>

          {/* 金融计算器 */}
          {financeParams.length > 0 && (
            <div className="finance-card">
              <h4>{t("finance.title")}</h4>
              <label>
                {t("finance.term")}
                <select value={term} onChange={(e) => setTerm(Number(e.target.value))}>
                  {financeParams.map((f) => (
                    <option key={f.term_months} value={f.term_months}>
                      {f.term_months} ({f.product_name || ""})
                    </option>
                  ))}
                </select>
              </label>
              <label>
                {t("finance.downPayment")}
                <select value={down} onChange={(e) => setDown(Number(e.target.value))}>
                  {[0, 20, 30, 40, 50].map((d) => (
                    <option key={d} value={d}>{d}%</option>
                  ))}
                </select>
              </label>
              <div className="summary-row total">
                <span>{t("finance.monthly")}</span>
                <b>{finance ? formatPrice(finance.monthly) : "—"}</b>
              </div>
              <div className="summary-row">
                <span>{t("finance.totalInterest")}</span>
                <b>{finance ? formatPrice(finance.interest) : "—"}</b>
              </div>
              <p className="summary-hint">{t("finance.hint")}</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
