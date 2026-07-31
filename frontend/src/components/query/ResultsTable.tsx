import { useState } from "react";

interface ResultsTableProps {
  results: Record<string, unknown>[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

const COLUMNS = [
  { key: "name", label: "Name", width: "w-40" },
  { key: "entity_type", label: "Type", width: "w-24" },
  { key: "status", label: "Status", width: "w-20" },
  { key: "confidence", label: "Confidence", width: "w-24" },
  { key: "observation_count", label: "Obs", width: "w-16" },
  { key: "first_observed_at", label: "First Seen", width: "w-36" },
  { key: "last_observed_at", label: "Last Seen", width: "w-36" },
  { key: "description", label: "Description", width: "flex-1" },
];

export default function ResultsTable({
  results,
  total,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: ResultsTableProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const totalPages = Math.ceil(total / pageSize);

  if (results.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        {total === 0 ? "Run a query to see results" : "No results found"}
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className={`${col.width} px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider`}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {results.map((row) => {
              const rowId = String(row.id || "");
              return (
                <tr
                  key={rowId}
                  onClick={() => setSelectedId(selectedId === rowId ? null : rowId)}
                  className={`cursor-pointer transition-colors ${
                    selectedId === rowId ? "bg-blue-50" : "hover:bg-gray-50"
                  }`}
                >
                  {COLUMNS.map((col) => (
                    <td key={col.key} className={`${col.width} px-3 py-2 truncate`}>
                      {col.key === "confidence" && typeof row[col.key] === "number"
                        ? `${((row[col.key] as number) * 100).toFixed(0)}%`
                      : col.key === "entity_type" ? (
                        <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-700 capitalize">
                          {String(row[col.key] || "")}
                        </span>
                      ) : col.key === "first_observed_at" || col.key === "last_observed_at" ? (
                        row[col.key]
                          ? new Date(row[col.key] as string).toLocaleDateString()
                          : "-"
                      ) : (
                        String(row[col.key] ?? "-")
                      )}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 border-t bg-white">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>{total} results</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="border border-gray-200 rounded px-2 py-1 text-xs"
          >
            {[25, 50, 100, 200].map((n) => (
              <option key={n} value={n}>{n} / page</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button
            disabled={page === 0}
            onClick={() => onPageChange(page - 1)}
            className="px-3 py-1 text-sm border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-30"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">
            Page {page + 1} of {totalPages || 1}
          </span>
          <button
            disabled={page >= totalPages - 1}
            onClick={() => onPageChange(page + 1)}
            className="px-3 py-1 text-sm border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-30"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
