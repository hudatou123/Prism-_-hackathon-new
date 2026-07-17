import type { StreamEvent } from "./types";

type TimedEvent = { at: number; event: StreamEvent };

const metaEvents: TimedEvent[] = [
  { at: 2500, event: { type: "provisional", claim: "Did Meta really lay off 5% of its workforce?", earlyRead: "Likely true, scale disputed", sourcesSoFar: 4 } },
  { at: 3800, event: { type: "counts", sourcesExamined: 4, quotesVerified: 1, quotesTotal: 1 } },
  { at: 6000, event: { type: "facet", facet: "fact", status: "confirmed", summary: "Workforce reductions are confirmed across quality sources", conEmpty: true, conSearched: 4, sourcesExamined: 4, quotesVerified: 1, quotesTotal: 1, evidence: [
    { id: "fact-cbs", side: "pro", claim: "Meta announced performance-based workforce cuts", quote: "Meta plans to cut 5% of its workforce, or about 3,600 workers.", url: "https://www.cbsnews.com/news/meta-layoffs-5-percent-workforce-cuts-low-performers/", source: "cbsnews.com", publishedAt: "2025-01-15T02:19:17Z", verified: true, bias: "center" },
  ] } },
  { at: 7000, event: { type: "counts", sourcesExamined: 7, quotesVerified: 2, quotesTotal: 2 } },
  { at: 9000, event: { type: "facet", facet: "scale", status: "disputed", summary: "5% official figure vs broader estimates near 3,700 roles", sourcesExamined: 4, quotesVerified: 2, quotesTotal: 2, evidence: [
    { id: "scale-cnn", side: "pro", claim: "The target was about 5% of the workforce", quote: "Meta is aiming to cut about 5% of what it calls its lowest performers.", url: "https://www.cnn.com/2025/01/14/business/meta-layoffs-low-performers/index.html", source: "cnn.com", publishedAt: "2025-01-14T20:56:15Z", verified: true, bias: "left" },
    { id: "scale-register", side: "con", claim: "Headcount math produces a somewhat higher estimate", quote: "Some 5 percent of the workforce is being erased, equating to roughly 3,700 jobs.", url: "https://www.theregister.com/2025/02/10/meta_to_toss_5_of", source: "theregister.com", publishedAt: "2025-02-10T20:44:53Z", verified: true },
  ] } },
  { at: 10800, event: { type: "counts", sourcesExamined: 10, quotesVerified: 4, quotesTotal: 4 } },
  { at: 13000, event: { type: "facet", facet: "stakeholders", status: "disputed", summary: "Named: performance reset · Grassroots: worker impact", sourcesExamined: 3, quotesVerified: 1, quotesTotal: 2, evidence: [
    { id: "named-cnbc", side: "named", claim: "Leadership framed the cuts as a higher performance bar", quote: "Move out low performers faster.", url: "https://www.cnbc.com/2025/01/14/meta-targeting-lowest-performing-employees-in-latest-round-of-layoffs.html", source: "cnbc.com", publishedAt: "2025-01-14T22:26:33Z", verified: true, bias: "center" },
    { id: "grassroots-fastcompany", side: "grassroots", claim: "Affected workers challenged the low-performer label", quote: "Some laid-off employees said their recent reviews did not match the label applied to the cuts.", url: "https://www.fastcompany.com/91276893/meta-laid-off-low-performers-defend-themselves-on-linkedin-and-reddit", source: "reddit.com · public reactions", publishedAt: "2025-02-12T12:00:00Z", verified: false, score: 482 },
  ] } },
  { at: 13600, event: { type: "counts", sourcesExamined: 11, quotesVerified: 5, quotesTotal: 6 } },
  { at: 14000, event: { type: "final", verdict: "Mostly true", qualifier: "scale disputed", band: "high", facetScores: { fact: 1, scale: 0.5, stakeholders: 0.5 }, agreement: { agree: 9, total: 11 } } },
];

const settledEvents: TimedEvent[] = [
  { at: 1200, event: { type: "provisional", claim: "Is the Earth round?", earlyRead: "Confirmed by direct observation and measurement", sourcesSoFar: 2 } },
  { at: 2200, event: { type: "counts", sourcesExamined: 3, quotesVerified: 1, quotesTotal: 1 } },
  { at: 3200, event: { type: "facet", facet: "fact", status: "confirmed", summary: "Direct observation and measurement confirm an oblate sphere", conEmpty: true, conSearched: 3, sourcesExamined: 3, quotesVerified: 1, quotesTotal: 1, evidence: [
    { id: "earth-nasa", side: "pro", claim: "Earth is a round, rocky terrestrial planet", quote: "Earth is a terrestrial planet. It is small and rocky.", url: "https://science.nasa.gov/earth/facts/", source: "nasa.gov", publishedAt: "2024-09-10T00:00:00Z", verified: true },
  ] } },
  { at: 3600, event: { type: "final", verdict: "Confirmed", band: "high", facetScores: { fact: 1, scale: null, stakeholders: null }, agreement: { agree: 3, total: 3 } } },
];

export function startMockStream(claim: string, onEvent: (event: StreamEvent) => void): () => void {
  const events = /earth\s+(round|spherical)/i.test(claim) ? settledEvents : metaEvents;
  const timers = events.map(({ at, event }) => window.setTimeout(() => onEvent(event), at));
  return () => timers.forEach(window.clearTimeout);
}
