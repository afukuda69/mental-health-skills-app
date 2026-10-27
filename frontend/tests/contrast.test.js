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

// Backgrounds text appears on: the app column, white cards, the sage featured card, the page edge.
const backgrounds = ['bg', 'surface', 'sage', 'page']

describe('contrast on the app backgrounds', () => {
  it.each(['text', 'muted', 'faint', 'accent', 'crisis-text'])('--%s text is at least 4.5:1 on every background', (name) => {
    for (const bg of backgrounds) expect(contrast(token(name), token(bg))).toBeGreaterThanOrEqual(4.5)
  })

  it('crisis text on its pale red button is at least 4.5:1', () => {
    expect(contrast(token('crisis-text'), token('crisis-bg'))).toBeGreaterThanOrEqual(4.5)
  })

  it.each(['circle-edge', 'crisis-border'])('--%s is at least 3:1 (non-text) on the app background', (name) => {
    expect(contrast(token(name), token('bg'))).toBeGreaterThanOrEqual(3)
  })

  it('white button text on --accent is at least 4.5:1', () => {
    expect(contrast('#ffffff', token('accent'))).toBeGreaterThanOrEqual(4.5)
  })

  it('the stylesheet has no animation (motion only on the breathing cue, D6)', () => {
    expect(css).not.toMatch(/@keyframes|animation\s*:/)
  })
})
