// =============================================================
// 段功能：M4 后台仪表盘
// 说明：拉取 /admin/dashboard 聚合数据，展示 KPI 卡片 + 趋势折线(轻量 SVG)
//       + 品牌/城市分布(横向条形) + 转化漏斗。不引入重型图表库，用 SVG/div 绘制。
// =============================================================

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getDashboard, type DashboardData } from "../../api/admin";

const RANGES = [
  { v: 7, label: "近 7 天" },
  { v: 30, label: "近 30 天" },
  { v: 90, label: "近 90 天" },
];

export default function AdminDashboard() {
  const [params, setParams] = useSearchParams();
  const range = Number(params.get("range") || "30");
  const [data, setData] = useState<DashboardData | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    getDashboard(range).then(setData).catch((e: Error) => setErr(e.message));
  }, [range]);

  if (err) return <div className="admin-error">{err}</div>;
  if (!data) return <div className="admin-loading">加载中…</div>;

  const maxTrend = Math.max(1, ...data.trend.map((t) => t.leads));
  const kpis = data.kpis;
  const maxBar = Math.max(1, ...data.by_brand.map((b) => b.count), ...data.by_city.map((c) => c.count));

  return (
    <div className="admin-dashboard">
      <div className="admin-page-head">
        <h2>仪表盘</h2>
        <div className="seg">
          {RANGES.map((r) => (
            <button
              key={r.v}
              className={r.v === range ? "on" : ""}
              onClick={() => { const p = new URLSearchParams(params); p.set("range", String(r.v)); setParams(p); }}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI 卡片 */}
      <div className="kpi-grid">
        <div className="kpi-card"><span>线索总量</span><b>{kpis.leads_total}</b></div>
        <div className="kpi-card"><span>试驾</span><b>{kpis.test_drive}</b></div>
        <div className="kpi-card"><span>询价</span><b>{kpis.inquiry}</b></div>
        <div className="kpi-card"><span>成交率</span><b>{Math.round(kpis.deal_rate * 100)}%</b></div>
      </div>

      <div className="dash-cols">
        {/* 趋势折线（SVG） */}
        <section className="panel">
          <h3>线索趋势</h3>
          <svg viewBox="0 0 400 160" className="trend-svg">
            {data.trend.map((t, i) => {
              const x = (i / Math.max(1, data.trend.length - 1)) * 380 + 10;
              const y = 140 - (t.leads / maxTrend) * 120;
              return (
                <g key={i}>
                  <circle cx={x} cy={y} r="3" fill="#c2a36b" />
                  {i > 0 && <line x1={(i - 1) / Math.max(1, data.trend.length - 1) * 380 + 10} y1={140 - (data.trend[i - 1].leads / maxTrend) * 120} x2={x} y2={y} stroke="#c2a36b" strokeWidth="2" />}
                </g>
              );
            })}
          </svg>
        </section>

        {/* 转化漏斗 */}
        <section className="panel">
          <h3>试驾转化漏斗</h3>
          {data.funnel.map((f) => (
            <div key={f.stage} className="funnel-row">
              <span>{f.stage}</span>
              <div className="funnel-bar">
                <div style={{ width: `${Math.max(8, (f.count / Math.max(1, data.funnel[0]?.count)) * 100)}%` }} />
              </div>
              <b>{f.count}</b>
            </div>
          ))}
        </section>
      </div>

      <div className="dash-cols">
        {/* 品牌分布 */}
        <section className="panel">
          <h3>品牌分布</h3>
          {data.by_brand.length === 0 && <p className="muted">暂无数据</p>}
          {data.by_brand.map((b) => (
            <div key={b.brand} className="bar-row">
              <span>{b.brand}</span>
              <div className="hbar"><div style={{ width: `${(b.count / maxBar) * 100}%` }} /></div>
              <b>{b.count}</b>
            </div>
          ))}
        </section>
        {/* 城市分布 */}
        <section className="panel">
          <h3>城市分布</h3>
          {data.by_city.length === 0 && <p className="muted">暂无数据</p>}
          {data.by_city.map((c) => (
            <div key={c.city} className="bar-row">
              <span>{c.city}</span>
              <div className="hbar"><div style={{ width: `${(c.count / maxBar) * 100}%` }} /></div>
              <b>{c.count}</b>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
