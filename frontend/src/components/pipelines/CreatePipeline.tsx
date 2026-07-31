import { useState } from "react";
import { useCreatePipeline, useNodeTypes } from "../../hooks/usePipelines";
import { usePipelineStore } from "../../store/usePipelineStore";
import type { NodeType, NodeConfig } from "../../types/pipeline";
import { useToastStore } from "../../store/useToastStore";
import { getErrorMessage } from "../../utils/errorMessage";

export default function CreatePipeline() {
  const { projectId } = usePipelineStore();
  const createMutation = useCreatePipeline();
  const { data: nodeTypes, isError } = useNodeTypes();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [nodes, setNodes] = useState<NodeConfig[]>([
    { name: "Import File", node_type: "import_file", inputs: {} },
    { name: "Validate", node_type: "validate", inputs: {} },
    { name: "Extract Metadata", node_type: "extract_metadata", inputs: {} },
    { name: "Create Thumbnail", node_type: "create_thumbnail", inputs: {} },
    { name: "Save to Database", node_type: "save_db", inputs: {} },
  ]);
  const [showForm, setShowForm] = useState(false);
  const toast = useToastStore.getState();

  const handleCreate = () => {
    if (!name.trim()) return;
    createMutation.mutate(
      {
        name,
        description,
        project_id: projectId || undefined,
        nodes: nodes.map((n, i) => ({
          ...n,
          depends_on: i > 0 ? [] : undefined,
        })),
      },
      {
        onSuccess: () => {
          toast.success("Pipeline created");
          setName("");
          setDescription("");
          setShowForm(false);
        },
        onError: (err) => toast.error(getErrorMessage(err)),
      }
    );
  };

  return (
    <div className="p-3">
      <button
        onClick={() => setShowForm(!showForm)}
        className="w-full px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded-lg transition-colors"
      >
        {showForm ? "Cancel" : "New Pipeline"}
      </button>

      {showForm && (
        <div className="mt-3 space-y-3">
          <input
            type="text"
            placeholder="Pipeline name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
          />
          <div>
            <p className="text-xs text-slate-500 mb-1">Nodes ({nodes.length})</p>
            {nodes.map((node, i) => (
              <div key={i} className="flex items-center gap-2 mb-1">
                <select
                  value={node.node_type}
                  onChange={(e) => {
                    const newNodes = [...nodes];
                    newNodes[i] = { ...newNodes[i], node_type: e.target.value };
                    setNodes(newNodes);
                  }}
                  className="bg-slate-700/50 border border-slate-600/50 rounded px-2 py-1 text-xs text-white"
                >
                  {isError ? (
                    <option value="">Failed to load types</option>
                  ) : (
                    (nodeTypes || []).map((nt: NodeType) => (
                      <option key={nt.type} value={nt.type}>{nt.type}</option>
                    ))
                  )}
                </select>
                <input
                  type="text"
                  value={node.name}
                  onChange={(e) => {
                    const newNodes = [...nodes];
                    newNodes[i] = { ...newNodes[i], name: e.target.value };
                    setNodes(newNodes);
                  }}
                  className="flex-1 bg-slate-700/50 border border-slate-600/50 rounded px-2 py-1 text-xs text-white"
                />
                <button
                  onClick={() => setNodes(nodes.filter((_, j) => j !== i))}
                  className="text-red-400 hover:text-red-300 text-xs"
                >
                  x
                </button>
              </div>
            ))}
            <button
              onClick={() => setNodes([...nodes, { name: `Node ${nodes.length + 1}`, node_type: "custom" }])}
              className="text-xs text-primary-400 hover:text-primary-300 mt-1"
            >
              + Add Node
            </button>
          </div>
          <button
            onClick={handleCreate}
            disabled={!name.trim() || createMutation.isPending}
            className="w-full px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded-lg disabled:opacity-50"
          >
            {createMutation.isPending ? "Creating..." : "Create Pipeline"}
          </button>
        </div>
      )}
    </div>
  );
}
