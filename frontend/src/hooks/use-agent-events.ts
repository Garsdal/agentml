import { useState, useEffect } from "react";
import { useSWRConfig } from "swr";
import type { AgentEvent } from "@/types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export function useAgentEvents(runId: string | undefined) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [done, setDone] = useState(false);
  const { mutate } = useSWRConfig();

  // Poll every 3 seconds while a run is active
  useEffect(() => {
    if (!runId || done) return;

    const interval = setInterval(() => {
      void mutate(
        (key) =>
          typeof key === "string" &&
          (key.startsWith("/experiments") ||
            key.startsWith("/domains") ||
            key.startsWith("/knowledge") ||
            key.startsWith("/agent")),
        undefined,
        { revalidate: true },
      );
    }, 3000);

    return () => clearInterval(interval);
  }, [runId, done, mutate]);

  // SSE event stream — collect events only, no revalidation logic
  useEffect(() => {
    if (!runId) return;

    setEvents([]);
    setDone(false);

    const es = new EventSource(`${API_BASE}/agent/runs/${runId}/events`);

    const handleEvent = (e: MessageEvent) => {
      try {
        const parsed = JSON.parse(e.data) as AgentEvent;
        setEvents((prev) => [...prev, parsed]);
      } catch {
        // Ignore malformed events
      }
    };

    es.addEventListener("tool_call", handleEvent);
    es.addEventListener("tool_result", handleEvent);
    es.addEventListener("text", handleEvent);
    es.addEventListener("error", handleEvent);
    es.addEventListener("result", handleEvent);
    es.addEventListener("done", () => {
      setDone(true);
      es.close();
    });
    es.onerror = () => {
      setDone(true);
      es.close();
    };

    return () => {
      es.close();
    };
  }, [runId]);

  return { events, done };
}
