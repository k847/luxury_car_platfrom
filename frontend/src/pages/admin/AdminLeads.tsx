// =============================================================
// 段功能：M4 后台线索管理（试驾 / 询价）
// 说明：列表 + 分配跟进人 + 状态机推进（试驾 pending→contacted→arrived→deal/invalid；
//       询价 new→processing→quoted→deal/invalid）。后端越级返回 40022。
// =============================================================

import { useEffect, useState } from "react";
import { getTestDriveLeads, getInquiryLeads, assignLead, advanceLead, type AdminLead } from "../../api/admin";

const TD_NEXT: Record<string, string> = { pending: "contacted", contacted: "arrived", arrived: "deal" };
const IQ_NEXT: Record<string, string> = { new: "processing", processing: "quoted", quoted: "deal" };

export default function AdminLeads() {
  const [tab, setTab] = useState<"test-drive" | "inquiry">("test-drive");
  const [leads, setLeads] = useState<AdminLead[]>([]);
  const [err, setErr] = useState("");

  const refresh = () => {
    if (tab === "test-drive") getTestDriveLeads().then((r) => setLeads(r.list)).catch((e: Error) => setErr(e.message));
    else getInquiryLeads().then((r) => setLeads(r.list)).catch((e: Error) => setErr(e.message));
  };
  useEffect(refresh, [tab]);

  const onAdvance = (id: number) => {
    const next = tab === "test-drive" ? TD_NEXT[leads.find((l) => l.id === id)?.status || ""] : IQ_NEXT[leads.find((l) => l.id === id)?.status || ""];
    if (!next) return;
    advanceLead(tab, id, next).then(refresh).catch((e: Error) => setErr(e.message));
  };
  const onInvalid = (id: number) => {
    advanceLead(tab, id, "invalid").then(refresh).catch((e: Error) => setErr(e.message));
  };
  const onAssign = (id: number) => {
    // 演示：分配到当前登录用户(id 取 1，即 seed 的 admin)
    assignLead(tab, id, 1).then(refresh).catch((e: Error) => setErr(e.message));
  };

  const statusZh = (s: string) => ({ pending: "待跟进", contacted: "已联系", arrived: "已到店", deal: "成交", invalid: "失效", new: "新建", processing: "处理中", quoted: "已报价" })[s] || s;

  return (
    <div className="admin-page">
      <div className="admin-page-head">
        <h2>线索管理</h2>
        <div className="seg">
          <button className={tab === "test-drive" ? "on" : ""} onClick={() => setTab("test-drive")}>试驾</button>
          <button className={tab === "inquiry" ? "on" : ""} onClick={() => setTab("inquiry")}>询价</button>
        </div>
      </div>
      {err && <div className="admin-error">{err}</div>}
      <section className="panel">
        <table className="admin-table">
          <thead><tr><th>ID</th><th>姓名</th><th>手机号</th><th>城市</th>{tab === "inquiry" && <th>意向</th>}<th>状态</th><th>操作</th></tr></thead>
          <tbody>
            {leads.map((l) => (
              <tr key={l.id}>
                <td>{l.id}</td><td>{l.name}</td><td>{l.phone}</td><td>{l.city || "—"}</td>
                {tab === "inquiry" && <td>{l.intent || "—"}</td>}
                <td><span className="badge">{statusZh(l.status)}</span></td>
                <td>
                  <button className="btn-gold sm" onClick={() => onAdvance(l.id)} disabled={l.status === "deal" || l.status === "invalid"}>推进</button>
                  <button className="btn-ghost sm" onClick={() => onAssign(l.id)}>分配</button>
                  {l.status !== "invalid" && l.status !== "deal" && <button className="btn-danger sm" onClick={() => onInvalid(l.id)}>失效</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
