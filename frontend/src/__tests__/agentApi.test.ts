import { describe, it, expect, vi, afterEach } from "vitest";
import { streamRun } from "../agent/agentApi";
import { buildScreenContext } from "../agent/screenContext";
import type { AgentEvent } from "../agent/types";

function sseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const c of chunks) controller.enqueue(encoder.encode(c));
      controller.close();
    },
  });
  return new Response(stream, { status: 200 });
}

afterEach(() => vi.restoreAllMocks());

describe("streamRun", () => {
  it("invokes onEvent for each parsed SSE event across chunk boundaries", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      sseResponse([
        'data: {"type":"tool_call","id":"c1","name":"screen_stocks","arguments":{}}\n\n',
        'data: {"type":"final","con',
        'tent":"AAPL"}\n\n',
      ])
    ));
    const seen: AgentEvent[] = [];
    await streamRun("run-1", (e) => seen.push(e));
    expect(seen.map((e) => e.type)).toEqual(["tool_call", "final"]);
    expect(seen[1]).toEqual({ type: "final", content: "AAPL" });
  });

  it("emits a synthetic error event when the response is not ok", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("nope", { status: 500 })));
    const seen: AgentEvent[] = [];
    await streamRun("run-1", (e) => seen.push(e));
    expect(seen[seen.length - 1].type).toBe("error");
  });
});

describe("buildScreenContext", () => {
  it("captures the current pathname", () => {
    const ctx = buildScreenContext();
    expect(typeof ctx.route).toBe("string");
  });
});
