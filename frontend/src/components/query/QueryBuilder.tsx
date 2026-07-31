interface QueryBuilderProps {
  filters: Record<string, unknown>;
  onChange: (filters: Record<string, unknown>) => void;
}

export default function QueryBuilder({ filters, onChange }: QueryBuilderProps) {
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    try {
      const parsed = JSON.parse(e.target.value);
      onChange(parsed);
    } catch {
      // Invalid JSON while typing
    }
  };

  return (
    <div className="p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Raw Query (JSON)</h3>
      <textarea
        value={JSON.stringify(filters, null, 2)}
        onChange={handleChange}
        className="w-full h-48 px-3 py-2 border border-gray-300 rounded-lg text-xs font-mono"
        placeholder='{ "entity_types": ["building"], ... }'
      />
    </div>
  );
}
