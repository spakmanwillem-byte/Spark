// v10_kb_save_robust_001 — robuuste fetch voor KB saves op productie
// Fix voor bug: bij lag op deployed versie werd kaart-invulling niet opgeslagen
// zonder feedback naar user. Retry + timeout + localStorage-queue voor offline replay.

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1500;
const TIMEOUT_MS = 15000;
const QUEUE_KEY = "kb_save_queue_v1";

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

/**
 * Fetch met retry, timeout, en persistente queue.
 * @param {string} url - endpoint
 * @param {object} opts - fetch options
 * @param {object} meta - {kind, description} voor queue-logging
 */
export async function robustFetch(url, opts = {}, meta = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let lastError = null;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const r = await fetch(url, { ...opts, signal: controller.signal });
      clearTimeout(timer);
      if (r.ok) {
        return await r.json();
      }
      // HTTP-fout: 4xx niet retryen, 5xx wel
      if (r.status >= 400 && r.status < 500) {
        const body = await r.text();
        throw new Error(`HTTP ${r.status}: ${body.slice(0, 200)}`);
      }
      lastError = new Error(`HTTP ${r.status}`);
    } catch (e) {
      lastError = e;
      if (e.name === "AbortError") lastError = new Error("Timeout na 15s");
      if (attempt < MAX_RETRIES) {
        await sleep(RETRY_DELAY_MS * attempt);  // exponential-ish backoff
      }
    }
  }

  // Alle retries mislukt → queue voor later
  clearTimeout(timer);
  try {
    const queue = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
    queue.push({
      url, opts, meta,
      queued_at: new Date().toISOString(),
      last_error: lastError?.message || "unknown",
    });
    localStorage.setItem(QUEUE_KEY, JSON.stringify(queue.slice(-50)));  // cap 50
  } catch {}

  throw lastError;
}

/** Toon aantal items in de queue (voor UI-badge). */
export function getQueueSize() {
  try {
    return (JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]")).length;
  } catch { return 0; }
}

/** Probeer alle items in de queue opnieuw. Retourneert {succeeded, failed}. */
export async function replayQueue() {
  let queue = [];
  try {
    queue = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
  } catch { return { succeeded: 0, failed: 0 }; }
  if (!queue.length) return { succeeded: 0, failed: 0 };

  const remaining = [];
  let succeeded = 0;
  for (const item of queue) {
    try {
      const r = await fetch(item.url, item.opts);
      if (r.ok) { succeeded++; continue; }
      remaining.push(item);
    } catch { remaining.push(item); }
  }
  localStorage.setItem(QUEUE_KEY, JSON.stringify(remaining));
  return { succeeded, failed: remaining.length };
}
