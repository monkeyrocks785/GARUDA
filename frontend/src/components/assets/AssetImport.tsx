import { useImportAsset } from "../../hooks/useAssets";
import { useAssetStore } from "../../store/useAssetStore";
import { useRef } from "react";

export default function AssetImport() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const importMutation = useImportAsset();
  const { projectId } = useAssetStore();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    importMutation.mutate({
      file,
      options: {
        project_id: projectId || undefined,
        name: file.name.replace(/\.[^/.]+$/, ""),
      } as Record<string, string>,
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="p-3">
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileChange}
        multiple={false}
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={importMutation.isPending}
        className="w-full px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
      >
        {importMutation.isPending ? "Importing..." : "Import Asset"}
      </button>
      {importMutation.isError && (
        <p className="text-xs text-red-400 mt-1">Import failed</p>
      )}
      {importMutation.isSuccess && (
        <p className="text-xs text-green-400 mt-1">Imported successfully</p>
      )}
    </div>
  );
}
