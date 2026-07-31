import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { useProjects } from "../hooks/useProjects";
import { useQueryConfig, useExecuteQuery, useSaveQuery, useSavedQueries } from "../hooks/useQuery";
import FilterPanel from "../components/query/FilterPanel";
import ResultsTable from "../components/query/ResultsTable";
import type { QueryRequest } from "../types/query";

export default function QueryBuilderPage() {
  const { id: projectId } = useParams();
  const [searchParams] = useSearchParams();
  const savedQueryId = searchParams.get("saved");

  const { data: projects } = useProjects();
  const { data: config } = useQueryConfig();
  const executeQuery = useExecuteQuery();
  const saveQuery = useSaveQuery();
  const { data: savedQueries } = useSavedQueries(projectId || null);

  const [query, setQuery] = useState<QueryRequest>({
    project_id: projectId || "",
    page: 0,
    page_size: 50,
  });
  const [results, setResults] = useState<Record<string, unknown>[]>([]);
  const [total, setTotal] = useState(0);
  const [executionTime, setExecutionTime] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  useEffect(() => {
    if (projectId) {
      setQuery((q) => ({ ...q, project_id: projectId }));
    }
  }, [projectId]);

  const handleRunQuery = async () => {
    setRunning(true);
    setError(null);
    try {
      const resp = await executeQuery.mutateAsync({ data: query });
      setResults(resp.items);
      setTotal(resp.total);
      setExecutionTime(resp.execution_time_ms);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Query execution failed";
      setError(msg);
    } finally {
      setRunning(false);
    }
  };

  const handleSaveQuery = async () => {
    if (!saveName.trim()) return;
    if (!projectId) {
      setError("Cannot save a query without a project. Open this page from a project first.");
      return;
    }
    setError(null);
    try {
      await saveQuery.mutateAsync({
        project_id: projectId,
        name: saveName.trim(),
        filters_json: JSON.stringify(query),
      });
      setShowSaveDialog(false);
      setSaveName("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save the query";
      setError(msg);
    }
  };

  const projectName = projects?.projects?.find((p: { id: string }) => p.id === projectId)?.name || "Loading...";

  return (
    <div className="flex h-full">
      <FilterPanel
        config={config || null}
        query={query}
        onChange={setQuery}
        onRun={handleRunQuery}
        running={running}
        savedQueries={savedQueries?.items || []}
        savedQueryId={savedQueryId}
      />
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between p-4 border-b bg-white">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">Intelligence Query Engine</h1>
            <p className="text-sm text-gray-500">Project: {projectName}</p>
          </div>
          <div className="flex items-center gap-3">
            {executionTime > 0 && (
              <span className="text-xs text-gray-400">
                {total} results in {executionTime.toFixed(0)}ms
              </span>
            )}
            <button
              onClick={handleRunQuery}
              disabled={running}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
            >
              {running ? "Running..." : "Run Query"}
            </button>
            <button
              onClick={() => setShowSaveDialog(true)}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium"
            >
              Save
            </button>
          </div>
        </div>

        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <ResultsTable
          results={results}
          total={total}
          page={query.page || 0}
          pageSize={query.page_size || 50}
          onPageChange={(page) => setQuery((q) => ({ ...q, page }))}
          onPageSizeChange={(pageSize) => setQuery((q) => ({ ...q, page_size: pageSize }))}
        />

        {showSaveDialog && (
          <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl p-6 w-96">
              <h3 className="text-lg font-semibold mb-4">Save Query</h3>
              <input
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                placeholder="Query name..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 text-sm"
                onKeyDown={(e) => e.key === "Enter" && handleSaveQuery()}
              />
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowSaveDialog(false)}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveQuery}
                  disabled={!saveName.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
