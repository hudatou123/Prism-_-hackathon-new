import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  let claim = "";
  try {
    const body = await request.json() as { claim?: unknown };
    claim = typeof body.claim === "string" ? body.claim.trim() : "";
  } catch {
    return Response.json({ error: "Invalid request body" }, { status: 400 });
  }

  if (!claim || claim.length > 500) {
    return Response.json({ error: "Claim must contain 1 to 500 characters" }, { status: 422 });
  }

  const backendBase = process.env.PRISM_BACKEND_URL ?? "http://127.0.0.1:8000";
  let upstream: Response;
  try {
    upstream = await fetch(new URL("/analyze", backendBase), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ topic: claim }),
      cache: "no-store",
      signal: request.signal,
    });
  } catch {
    return Response.json({ error: "Fact-checking backend is unavailable" }, { status: 502 });
  }

  if (!upstream.ok || !upstream.body) {
    return Response.json({ error: "Fact-checking backend rejected the request" }, { status: 502 });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}
