interface Sensor {
  name: string;
  count?: number;
}

interface Props {
  sensors: Sensor[];
  selected: string | null;
  onSelect: (sensor: string | null) => void;
}

export default function SensorFilter({ sensors, selected, onSelect }: Props) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <label className="text-sm text-slate-400">Sensor:</label>
      <button
        onClick={() => onSelect(null)}
        className={`px-3 py-1 rounded text-sm ${!selected ? "bg-primary-600 text-white" : "bg-slate-800/50 text-slate-400 hover:bg-slate-700/50"}`}
      >
        All
      </button>
      {sensors.map((s) => (
        <button
          key={s.name}
          onClick={() => onSelect(s.name)}
          className={`px-3 py-1 rounded text-sm ${selected === s.name ? "bg-primary-600 text-white" : "bg-slate-800/50 text-slate-400 hover:bg-slate-700/50"}`}
        >
          {s.name}
        </button>
      ))}
    </div>
  );
}
