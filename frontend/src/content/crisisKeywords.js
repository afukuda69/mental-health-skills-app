// Supplementary keyword check for typed text (used by the reframe in Part 3.3).
// The phrase list is shared/crisis_phrases.json, the same file the backend reads.
// This is not the safety mechanism; the always-visible Crisis support button is.
// It misses misspellings, indirect phrasing, and other languages, and it opens
// the panel on idioms ("end it all" about a project). See docs/design.md section f.
import data from '../../../shared/crisis_phrases.json'

export const normalize = (text) => text.toLowerCase().replace(/’/g, "'").replace(/\s+/g, ' ').trim()

const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const PATTERNS = data.phrases.map((p) => new RegExp(`\\b${escape(normalize(p))}\\b`))

export function matchesCrisisPhrase(text) {
  if (!text) return false
  const normalized = normalize(text)
  return PATTERNS.some((re) => re.test(normalized))
}
