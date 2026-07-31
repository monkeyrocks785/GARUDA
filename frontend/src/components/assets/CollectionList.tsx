import { useState } from "react";
import { useCollections, useCreateCollection } from "../../hooks/useAssets";
import { useAssetStore } from "../../store/useAssetStore";
import type { Collection } from "../../types/asset";
import { useToastStore } from "../../store/useToastStore";
import { getErrorMessage } from "../../utils/errorMessage";

export default function CollectionList() {
  const { projectId, selectedCollectionId, setSelectedCollectionId } = useAssetStore();
  const { data: collectionsData, isLoading } = useCollections();
  const createCollection = useCreateCollection();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const toast = useToastStore.getState();

  const handleCreate = () => {
    if (!newName.trim()) return;
    createCollection.mutate(
      {
        name: newName,
        description: newDesc,
        project_id: projectId || undefined,
      },
      {
        onSuccess: () => {
          toast.success("Collection created");
          setNewName("");
          setNewDesc("");
          setShowCreate(false);
        },
        onError: (err) => toast.error(getErrorMessage(err)),
      }
    );
  };

  const collections = collectionsData?.collections || [];

  return (
    <div className="p-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase">Collections</span>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="text-xs text-primary-400 hover:text-primary-300"
        >
          + New
        </button>
      </div>

      {showCreate && (
        <div className="space-y-2">
          <input
            type="text"
            placeholder="Collection name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
          />
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={!newName.trim()}
              className="px-3 py-1 bg-primary-600 hover:bg-primary-700 text-white text-xs rounded-lg disabled:opacity-50"
            >
              Create
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <p className="text-xs text-slate-500">Loading...</p>
      ) : collections.length === 0 ? (
        <p className="text-xs text-slate-500 text-center py-2">No collections</p>
      ) : (
        <div className="space-y-1">
          {collections.map((col: Collection) => (
            <button
              key={col.id}
              onClick={() => setSelectedCollectionId(
                selectedCollectionId === col.id ? null : col.id
              )}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                selectedCollectionId === col.id
                  ? "bg-primary-500/10 border border-primary-500/50 text-white"
                  : "hover:bg-slate-700/50 text-slate-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-primary-500"></span>
                <span className="truncate">{col.name}</span>
              </div>
              {col.description && (
                <p className="text-xs text-slate-500 ml-5 truncate">{col.description}</p>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
