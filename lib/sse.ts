import { startMockStream } from "./mock-sse";
import type { StreamEvent } from "./types";

const eventTypes = new Set(["provisional", "facet", "counts", "final"]);

export function parseStreamEvent(raw: string): StreamEvent | "done" | "error" {
  const value = JSON.parse(raw) as { type?: unknown };
  if (value.type === "done" || value.type === "error") return value.type;
  if (!eventTypes.has(String(value.type))) throw new Error("Unknown stream event");
  return value as StreamEvent;
}

function frameData(frame: string): string | null {
  const lines = frame.split(/\r?\n/);
  const data = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n");
  return data || null;
}

export function connectStream(
  claim: string,
  onEvent: (event: StreamEvent) => void,
  onError: () => void,
): () => void {
  const mockRequested =
    process.env.NEXT_PUBLIC_MOCK === "1" ||
    new URLSearchParams(window.location.search).get("mock") === "1";

  if (mockRequested) return startMockStream(claim, onEvent);

  const controller = new AbortController();
  let stopped = false;

  void consumeStream(claim, controller.signal, onEvent, () => {
    if (!stopped) onError();
  });

  return () => {
    stopped = true;
    controller.abort();
  };
}

async function consumeStream(
  claim: string,
  signal: AbortSignal,
  onEvent: (event: StreamEvent) => void,
  onError: () => void,
) {
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ claim }),
      signal,
    });
    if (!response.ok || !response.body) throw new Error("Stream unavailable");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let complete = false;

    while (!complete) {
      const chunk = await reader.read();
      complete = chunk.done;
      buffer += decoder.decode(chunk.value, { stream: !complete }).replace(/\r\n/g, "\n");
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";
      for (const frame of frames) {
        const data = frameData(frame);
        if (!data) continue;
        const event = parseStreamEvent(data);
        if (event === "error") throw new Error("Pipeline failed");
        if (event === "done") return;
        onEvent(event);
      }
    }

    if (buffer.trim()) {
      const data = frameData(buffer);
      if (data) {
        const event = parseStreamEvent(data);
        if (event !== "done" && event !== "error") onEvent(event);
        if (event === "error") throw new Error("Pipeline failed");
      }
    }
  } catch (error) {
    if (!(error instanceof DOMException && error.name === "AbortError")) onError();
  }
}
