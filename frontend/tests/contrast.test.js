// Checks the style tokens against WCAG AA on every background a text token sits on.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const css = readFileSync(resolve(process.cwd(), 'src/styles.css'), 'utf8')
const root = css.slice(css.indexOf(':root {'), css.indexOf('}', css.indexOf(':root {')))
const token = (name) => {
  const m = root.match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6})`))
  if (!m) throw new Error(`token --${name} not found as a hex color`)
  return m[1]
}

const lum = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
  const f = (c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
}
const contrast = (a, b) => {
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

// Backgrounds text sits on: the app column, white cards, the pale-blue featured card.
const backgrounds = ['bg', 'surface', 'tint']

describe('contrast on the baby-blue palette', () => {
  it.each(['text', 'muted', 'faint', 'accent'])('--%s text is at least 4.5:1 on every background', (name) => {
    for (const bg of backgrounds) expect(contrast(token(name), token(bg))).toBeGreaterThanOrEqual(4.5)
  })

  it('deep-blue text on the pale-blue secondary button is at least 4.5:1', () => {
    expect(contrast(token('accent'), token('secondary'))).toBeGreaterThanOrEqual(4.5)
  })

  it('white button text on --accent is at least 4.5:1', () => {
    expect(contrast('#ffffff', token('accent'))).toBeGreaterThanOrEqual(4.5)
  })

  it('coral crisis text is at least 4.5:1 on its pale coral fill and on white', () => {
    expect(contrast(token('crisis-text'), token('crisis-bg'))).toBeGreaterThanOrEqual(4.5)
    expect(contrast(token('crisis-text'), token('surface'))).toBeGreaterThanOrEqual(4.5)
  })

  it.each([
    ['circle-edge', 'bg'],
    ['circle-edge', 'tint'],
    ['crisis-border', 'surface'],
    ['status-completed', 'surface'],
    ['status-stopped', 'surface'],
    ['status-left', 'surface'],
  ])('--%s is at least 3:1 (non-text) on --%s', (name, bg) => {
    expect(contrast(token(name), token(bg))).toBeGreaterThanOrEqual(3)
  })

  it('no colour token is green', () => {
    const hexes = [...root.matchAll(/--[\w-]+:\s*(#[0-9a-fA-F]{6})/g)].map((m) => m[1])
    for (const hex of hexes) {
      const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16))
      expect(g > r + 10 && g > b + 10, `${hex} looks green`).toBe(false)
    }
  })

  it('the stylesheet has no animation (motion only on the breathing cue, D6)', () => {
    expect(css).not.toMatch(/@keyframes|animation\s*:/)
  })
})
