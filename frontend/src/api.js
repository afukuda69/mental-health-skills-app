// All backend calls. Session writes are fire-and-forget: nothing in an
// exercise waits on them, and a failed write only logs a console warning.
// The crisis components never import this file.

const BASE = '/api'

export function send(path, body) {
  fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
    keepalive: true,
  })
    .then((res) => {
      if (!res.ok) console.warn(`[session] write failed: ${path} -> HTTP ${res.status}`)
    })
    .catch(() => console.warn(`[session] write failed: ${path} -> backend unreachable`))
}

// For pagehide / visibilitychange. text/plain keeps the beacon a "simple"
// request; backend/main.py parses the JSON body itself.
export function beacon(path, body) {
  const blob = new Blob([JSON.stringify(body)], { type: 'text/plain' })
  const queued = typeof navigator.sendBeacon === 'function' && navigator.sendBeacon(BASE + path, blob)
  if (!queued) send(path, body)
}

export async function getJSON(path, timeoutMs = 4000) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(BASE + path, { signal: controller.signal })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } finally {
    clearTimeout(timer)
  }
}

// Reframe step 4. Only the step-3 answer is passed here; steps 1-2 never
// leave the component. The backend stores neither the text nor the reply.
// Resolves to null on any failure, and the caller shows the fixed fallback.
export async function requestReflection(clientId, text, timeoutMs = 6500) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(`${BASE}/sessions/${clientId}/reflection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
      signal: controller.signal,
    })
    if (!res.ok) return null
    const data = await res.json()
    return typeof data.text === 'string' ? data : null
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

// The backend enforces the 5 s model timeout. This client-side limit is a
// backstop for a slow or unreachable backend. Resolves to null on any failure,
// and the caller shows the fixed fallback text.
export async function requestAcknowledgment(clientId, timeoutMs = 6500) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(`${BASE}/sessions/${clientId}/acknowledgment`, {
      method: 'POST',
      signal: controller.signal,
    })
    if (!res.ok) return null
    const data = await res.json()
    return typeof data.text === 'string' ? data : null
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

// "Talk it through". These are awaited by the chat screen only; no exercise
// waits on them. Errors throw so the chat can show a neutral notice.
async function requestJSON(path, { method = 'GET', body, timeoutMs = 8000 } = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(BASE + path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } finally {
    clearTimeout(timer)
  }
}

export const listConversations = () => requestJSON('/conversations').then((d) => d.conversations)
export const createConversation = () => requestJSON('/conversations', { method: 'POST' })
export const getConversationMessages = (id) => requestJSON(`/conversations/${id}/messages`).then((d) => d.messages)
export const sendChatMessage = (id, text) => requestJSON(`/conversations/${id}/messages`, { method: 'POST', body: { text } })
export const deleteAllHistory = () => requestJSON('/history', { method: 'DELETE' })

// The one local profile.
export const getProfile = () => requestJSON('/profile')
export const updateProfile = (changes) => requestJSON('/profile', { method: 'POST', body: changes })
export const resetProfile = () => requestJSON('/profile/reset', { method: 'POST' })
