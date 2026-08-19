// =============================================================
// 段功能：询价留资页（M3，对应 §7.7）
// 说明：提交 /leads/inquiry，intent 必填之一 trade_in/finance/stock；
//       手机号校验与错误映射同试驾页。
// =============================================================

import { useState } from "react";
import { useLocation, useSearchParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { postInquiry, type LeadResponse } from "../api/public";

const PHONE_RE = /^1[3-9]\d{9}$/;

export default function InquiryPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const [params] = useSearchParams();
  const st = (location.state as { model_id?: number; config_summary?: unknown } | null) || null;
  const modelId = st?.model_id ?? (Number(params.get("model") || "") || undefined);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [city, setCity] = useState("");
  const [intent, setIntent] = useState<"trade_in" | "finance" | "stock">("finance");
  const [remark, setRemark] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState<LeadResponse | null>(null);
  const [err, setErr] = useState("");

  const submit = () => {
    setErr("");
    if (!name.trim() || !phone.trim()) {
      setErr(t("lead.required"));
      return;
    }
    if (!PHONE_RE.test(phone.trim())) {
      setErr(t("lead.invalidPhone"));
      return;
    }
    setSubmitting(true);
    postInquiry({
      name: name.trim(),
      phone: phone.trim(),
      intent,
      city: city.trim() || null,
      model_id: modelId,
      remark: remark.trim() || null,
    })
      .then((r) => setDone(r))
      .catch((e: Error) => setErr(e.message || t("lead.error")))
      .finally(() => setSubmitting(false));
  };

  if (done) {
    return (
      <div className="lead-page">
        <div className="lead-success">
          <h2>{t("lead.success")}</h2>
          <p>ID: #{done.lead_id}</p>
          <Link to="/models" className="btn-gold">{t("modelDetail.back")}</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="lead-page">
      <h1 className="page-title">{t("lead.inquiryTitle")}</h1>
      <form className="lead-form" onSubmit={(e) => { e.preventDefault(); submit(); }}>
        <label>
          {t("lead.name")}
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          {t("lead.phone")}
          <input value={phone} onChange={(e) => setPhone(e.target.value)} inputMode="numeric" />
        </label>
        <label>
          {t("lead.city")}
          <input value={city} onChange={(e) => setCity(e.target.value)} />
        </label>
        <label>
          {t("lead.intent")}
          <select value={intent} onChange={(e) => setIntent(e.target.value as "trade_in" | "finance" | "stock")}>
            <option value="trade_in">{t("lead.intentTradeIn")}</option>
            <option value="finance">{t("lead.intentFinance")}</option>
            <option value="stock">{t("lead.intentStock")}</option>
          </select>
        </label>
        <label>
          {t("lead.remark")}
          <textarea value={remark} onChange={(e) => setRemark(e.target.value)} />
        </label>
        {err && <div className="lead-error">{err}</div>}
        <button className="btn-gold" type="submit" disabled={submitting}>
          {submitting ? t("common.loading") : t("lead.submit")}
        </button>
      </form>
    </div>
  );
}
