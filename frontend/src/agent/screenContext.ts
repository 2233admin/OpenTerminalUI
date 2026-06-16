import type { RunContext } from "./types";

/** Capture lightweight context about the screen the user is on. */
export function buildScreenContext(): RunContext {
  const path = typeof window !== "undefined" ? window.location.pathname : "/";
  const ctx: RunContext = { route: path };
  // Pull a symbol out of common detail routes like /stock/AAPL or /equity/AAPL.
  const match = path.match(/\/(?:stock|equity|crypto|forex|commodities)\/([A-Za-z0-9.\-&]+)/);
  if (match) ctx.symbol = decodeURIComponent(match[1]).toUpperCase();
  return ctx;
}
