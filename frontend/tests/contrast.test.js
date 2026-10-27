// Checks the style tokens against WCAG AA on both background gradient stops.
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

const stops = [token('bg-top'), token('bg-bottom')]

describe('contrast on the gradient background', () => {
  it.each(['text', 'muted', 'faint', 'crisis-text'])('--%s text is at least 4.5:1 on both stops', (name) => {
    for (const bg of stops) expect(contrast(token(name), bg)).toBeGreaterThanOrEqual(4.5)
  })

  it.each(['circle-edge', 'crisis-border'])('--%s is at least 3:1 (non-text) on both stops', (name) => {
    for (const bg of stops) expect(contrast(token(name), bg)).toBeGreaterThanOrEqual(3)
  })

  it('white button text on --accent is at least 4.5:1', () => {
    expect(contrast('#ffffff', token('accent'))).toBeGreaterThanOrEqual(4.5)
  })

  it('the gradient layer is static', () => {
    const rule = css.slice(css.indexOf('body::before'), css.indexOf('}', css.indexOf('body::before')))
    expect(rule).toContain('position: fixed')
    expect(rule).toContain('linear-gradient')
    expect(rule).not.toMatch(/animation|transition/)
  })
})
