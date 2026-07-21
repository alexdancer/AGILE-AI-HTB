export async function drainLiveEvents({ sessionId, sinceId, getEvents, append, stopped = () => false }) {
  let cursor = sinceId;
  for (let page = 0; page < 100; page += 1) {
    const suffix = Number.isInteger(cursor) ? `?since_id=${cursor}` : "";
    const payload = await getEvents(`/api/sessions/${encodeURIComponent(sessionId)}/events${suffix}`);
    if (stopped()) return cursor;
    append(payload.events || []);
    const next = payload.next_since_id;
    if (!payload.has_more || !Number.isInteger(next) || next === cursor) return next ?? cursor;
    cursor = next;
  }
  return cursor;
}

export async function runSingleFlight(lock, work) {
  if (lock.current) return undefined;
  lock.current = true;
  try {
    return await work();
  } finally {
    lock.current = false;
  }
}
