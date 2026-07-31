import { Routes, Route } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard";
import Projects from "./pages/Projects";
import ProjectDashboard from "./pages/ProjectDashboard";
import MapPage from "./pages/MapPage";
import DatasetManager from "./pages/DatasetManager";
import AssetLibrary from "./pages/AssetLibrary";
import PipelineManager from "./pages/PipelineManager";
import MissionManager from "./pages/MissionManager";
import TimelineManager from "./pages/TimelineManager";
import Settings from "./pages/Settings";
import About from "./pages/About";
import QueryBuilderPage from "./pages/QueryBuilderPage";
import RuleManager from "./pages/RuleManager";
import AlertDashboard from "./pages/AlertDashboard";

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:id" element={<ProjectDashboard />} />
        <Route path="projects/:id/map" element={<MapPage />} />
        <Route path="projects/:id/datasets" element={<DatasetManager />} />
        <Route path="projects/:id/assets" element={<AssetLibrary />} />
        <Route path="projects/:id/pipelines" element={<PipelineManager />} />
        <Route path="projects/:id/queries" element={<QueryBuilderPage />} />
        <Route path="missions" element={<MissionManager />} />
        <Route path="timelines" element={<TimelineManager />} />
        <Route path="rules" element={<RuleManager />} />
        <Route path="alerts" element={<AlertDashboard />} />
        <Route path="settings" element={<Settings />} />
        <Route path="about" element={<About />} />
      </Route>
    </Routes>
  );
}

export default App;
