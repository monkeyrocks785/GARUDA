import { useHealth } from "../hooks/useHealth";

export default function About() {
  const { data: health } = useHealth();

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">About GARUDA</h1>
        <p className="text-slate-400 mt-1">
          AI-powered Geospatial Intelligence and Monitoring Platform
        </p>
      </div>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 space-y-4">
        <div>
          <h3 className="text-white font-semibold mb-2">Version</h3>
          <p className="text-slate-400">{health?.version || "Unavailable"}</p>
        </div>
        <div>
          <h3 className="text-white font-semibold mb-2">Environment</h3>
          <p className="text-slate-400 capitalize">{health?.environment || "Unavailable"}</p>
        </div>
        <div>
          <h3 className="text-white font-semibold mb-2">Description</h3>
          <p className="text-slate-400">
            GARUDA is an AI-powered platform designed for satellite imagery analysis,
            GIS operations, AI/ML model integration, remote sensing, time-series
            forecasting, and geospatial dashboards.
          </p>
        </div>
        <div>
          <h3 className="text-white font-semibold mb-2">Tech Stack</h3>
          <ul className="text-slate-400 space-y-1">
            <li>Backend: Python, FastAPI, SQLAlchemy</li>
            <li>Frontend: React, TypeScript, Vite, TailwindCSS</li>
            <li>Database: SQLite with Alembic migrations</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
