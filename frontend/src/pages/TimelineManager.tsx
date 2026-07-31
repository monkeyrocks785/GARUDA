import { useTemporalStore } from "../store/useTemporalStore";
import TimelineList from "../components/temporal/TimelineList";
import TimelineDetails from "../components/temporal/TimelineDetails";

export default function TimelineManager() {
  const { view, selectedTimelineId } = useTemporalStore();

  if (view === "detail" && selectedTimelineId) {
    return <TimelineDetails timelineId={selectedTimelineId} />;
  }

  return <TimelineList />;
}
