// =============================================================
// 段功能：分页组件（M2 列表页）
// 说明：根据 total / page_size 计算总页数，提供上一页/下一页与页码显示。
//       仅 1 页时不渲染，避免无谓控件。
// =============================================================

export default function Pagination({
  page,
  pageSize,
  total,
  onChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onChange: (p: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;
  return (
    <div className="pagination">
      <button disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ‹
      </button>
      <span>
        {page} / {totalPages}
      </span>
      <button disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
        ›
      </button>
    </div>
  );
}
