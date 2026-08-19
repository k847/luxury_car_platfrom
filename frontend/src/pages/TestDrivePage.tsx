// =============================================================
// 段功能：试驾留资页（M3，对应 §7.7）
// 说明：提交 /leads/test-drive；手机号正则校验 + 服务端 40012/42900 错误映射；
//       支持从配置器携带 config_summary 与 model_id 预填。
// =============================================================

import { useState } from "react";
import { useLocation, useSearchParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { postTestDrive, type LeadResponse } from "../api/public";

const PHONE_RE = /^1[3-9]\d{9}$/;

export default function TestDrivePage() {
  const { t } = useTranslation();
  const location = useLocation();
  const [params] = useSearchParams();
  const st = (location.state as { model_id?: number; config_summary?: unknown } | null) || null;
  const modelId = st?.model_id ?? (Number(params.get("model") || "") || undefined);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [city, setCity] = useState("");
  const [preferredTime, setPreferredTime] = useState("");
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
    postTestDrive({
      name: name.trim(),
      phone: phone.trim(),
      city: city.trim() || null,
      model_id: modelId,
      preferred_time: preferredTime || null,
      remark: remark.trim() || null,
      config_summary: st?.config_summary,
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
      <h1 className="page-title">{t("lead.testDriveTitle")}</h1>
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
          {t("lead.preferredTime")}
          <input type="datetime-local" value={preferredTime} onChange={(e) => setPreferredTime(e.target.value)} />
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
