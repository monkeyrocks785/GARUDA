import { useWorkspaceStore } from "../../store/useWorkspaceStore";

const DRAW_TOOLS = [
  { id: "pan", icon: "🖐️", label: "Pan", shortcut: "H" },
  { id: "draw_point", icon: "📍", label: "Draw Point", shortcut: "P" },
  { id: "draw_line", icon: "📏", label: "Draw Line", shortcut: "L" },
  { id: "draw_polygon", icon: "⬠", label: "Draw Polygon", shortcut: "G" },
  { id: "draw_rectangle", icon: "⬜", label: "Draw Rectangle", shortcut: "R" },
  { id: "draw_circle", icon: "⭕", label: "Draw Circle", shortcut: "C" },
];

const MEASURE_TOOLS = [
  { id: "measure_distance", icon: "📐", label: "Measure Distance", shortcut: "D" },
  { id: "measure_area", icon: "◼", label: "Measure Area", shortcut: "A" },
  { id: "measure_bearing", icon: "🧭", label: "Measure Bearing", shortcut: "B" },
];

const EDIT_TOOLS = [
  { id: "edit_shape", icon: "✏️", label: "Edit", shortcut: "E" },
  { id: "delete_shape", icon: "🗑️", label: "Delete", shortcut: "X" },
];

export default function DrawingToolbar() {
  const { activeTool, setActiveTool, undo, redo, undoStack, redoStack } =
    useWorkspaceStore();

  return (
    <div className="absolute top-2 left-2 z-[1000] flex flex-col gap-1">
      {/* Draw tools */}
      <div className="bg-slate-800/95 border border-slate-700 rounded-lg p-1 shadow-lg">
        <div className="text-[9px] text-slate-500 uppercase tracking-wider px-1.5 py-0.5">
          Draw
        </div>
        {DRAW_TOOLS.map((tool) => (
          <button
            key={tool.id}
            onClick={() => setActiveTool(tool.id)}
            className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors ${
              activeTool === tool.id
                ? "bg-primary-600 text-white"
                : "text-slate-400 hover:bg-slate-700 hover:text-white"
            }`}
            title={`${tool.label} (${tool.shortcut})`}
          >
            <span className="w-5 text-center">{tool.icon}</span>
            <span className="hidden lg:inline">{tool.label}</span>
          </button>
        ))}
      </div>

      {/* Measure tools */}
      <div className="bg-slate-800/95 border border-slate-700 rounded-lg p-1 shadow-lg">
        <div className="text-[9px] text-slate-500 uppercase tracking-wider px-1.5 py-0.5">
          Measure
        </div>
        {MEASURE_TOOLS.map((tool) => (
          <button
            key={tool.id}
            onClick={() => setActiveTool(tool.id)}
            className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors ${
              activeTool === tool.id
                ? "bg-primary-600 text-white"
                : "text-slate-400 hover:bg-slate-700 hover:text-white"
            }`}
            title={`${tool.label} (${tool.shortcut})`}
          >
            <span className="w-5 text-center">{tool.icon}</span>
            <span className="hidden lg:inline">{tool.label}</span>
          </button>
        ))}
      </div>

      {/* Edit tools */}
      <div className="bg-slate-800/95 border border-slate-700 rounded-lg p-1 shadow-lg">
        <div className="text-[9px] text-slate-500 uppercase tracking-wider px-1.5 py-0.5">
          Edit
        </div>
        {EDIT_TOOLS.map((tool) => (
          <button
            key={tool.id}
            onClick={() => setActiveTool(tool.id)}
            className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors ${
              activeTool === tool.id
                ? "bg-primary-600 text-white"
                : "text-slate-400 hover:bg-slate-700 hover:text-white"
            }`}
            title={`${tool.label} (${tool.shortcut})`}
          >
            <span className="w-5 text-center">{tool.icon}</span>
            <span className="hidden lg:inline">{tool.label}</span>
          </button>
        ))}
      </div>

      {/* Undo/Redo */}
      <div className="bg-slate-800/95 border border-slate-700 rounded-lg p-1 shadow-lg flex gap-1">
        <button
          onClick={() => undo()}
          disabled={undoStack.length === 0}
          className="flex-1 px-2 py-1.5 rounded text-xs text-slate-400 hover:bg-slate-700 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          title="Undo (Ctrl+Z)"
        >
          ↩
        </button>
        <button
          onClick={() => redo()}
          disabled={redoStack.length === 0}
          className="flex-1 px-2 py-1.5 rounded text-xs text-slate-400 hover:bg-slate-700 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          title="Redo (Ctrl+Y)"
        >
          ↪
        </button>
      </div>
    </div>
  );
}
