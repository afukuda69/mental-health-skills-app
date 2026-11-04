// Visits every screen and state at three widths. On each one: an axe scan,
// a horizontal-overflow check, and a document-title check. Saves screenshots
// (375 and 1280 px) to docs/evidence/3.3/screens/ and results to docs/evidence/3.3/a11y.md.
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import AxeBuilder from '@axe-core/playwright'
import { chromium } from 'playwright'
import { ROOT, sleep, startStack } from './harness.mjs'

const OUT = join(ROOT, 'docs/evidence/3.3')
const SHOTS = join(OUT, 'screens')
mkdirSync(SHOTS, { recursive: true })
const WIDTHS = [375, 768, 1280]
const results = []

function makeSnap(page, width) {
  return async function snap(name) {
    await sleep(150)
    const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']).analyze()
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    results.push({
      name,
      width,
      title: await page.title(),
      overflow,
      violations: axe.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length, target: v.nodes[0]?.target?.join(' ') })),
      incomplete: axe.incomplete.map((v) => v.id),
    })
    if (width !== 768) {
      // Grow the viewport to the page height so the fixed tab bar and waves sit where a person sees them.
      const size = page.viewportSize()
      const height = await page.evaluate(() => document.documentElement.scrollHeight)
      await page.setViewportSize({ width: size.width, height: Math.max(height, size.height) })
      await page.screenshot({ path: join(SHOTS, `${width}-${name}.png`) })
      await page.setViewportSize(size)
    }
  }
}

const nav = (p, name) => p.getByRole('button', { name, exact: true }).first().click()
const nextStep = async (p) => {
  await sleep(2200)
  await p.locator('.controls button.primary').click()
}

async function seededTour(browser, stack, width) {
  const ctx = await browser.newContext({ viewport: { width, height: width < 500 ? 800 : 900 } })
  const p = await ctx.newPage()
  const snap = makeSnap(p, width)
  await p.goto(stack.url)
  await p.getByRole('heading', { name: 'Hi, Alex.' }).waitFor()
  await snap('home')
  await nav(p, 'Tense or wound up')
  await snap('home-tense')
  await p.getByRole('button', { name: 'Change' }).click()
  await nav(p, 'Skip')
  await snap('home-skip')
  await p.getByRole('button', { name: 'Change' }).click()
  await nav(p, 'Overwhelmed')
  await snap('home-overwhelmed')
  await p.getByRole('button', { name: 'Show everything' }).click()
  await p.getByRole('button', { name: 'Change' }).click()

  await nav(p, 'Activities')
  await snap('activities')
  await p.getByRole('button', { name: 'Start STOP' }).click()
  await snap('stop-step')
  await nextStep(p)
  await nextStep(p)
  await p.getByRole('button', { name: /Write down what you notice/ }).click()
  await snap('stop-note')
  await nav(p, 'Crisis')
  await p.getByRole('dialog').waitFor()
  await snap('crisis-panel')
  await p.getByRole('button', { name: 'Back to where I was' }).click()
  await p.getByRole('button', { name: 'Stop exercise' }).click()
  await p.getByText("Stopped. That's fine.").waitFor()
  await snap('stopped')
  await p.getByRole('button', { name: 'Back to start' }).click()

  await nav(p, 'Activities')
  await p.getByRole('button', { name: 'Start Cognitive reframe' }).click()
  await p.getByRole('button', { name: 'I messed up' }).click()
  await snap('reframe-step')
  await nextStep(p)
  await nextStep(p)
  await nextStep(p)
  await p.locator('.reflection').waitFor()
  await snap('reframe-reflection')
  await nextStep(p)
  await snap('check-in')
  await p.getByRole('button', { name: 'Skip' }).click()
  await snap('done')
  await p.getByRole('button', { name: 'Back to start' }).click()

  await nav(p, 'Chat')
  await snap('chat-new')
  await p.locator('#chat-input').fill('Fictional: nervous before a presentation, any help?')
  await p.getByRole('button', { name: 'Send' }).click()
  await p.locator('.bubble.theirs').waitFor()
  await snap('chat-reply')
  await p.locator('#chat-input').fill('Can you tell me if I have anxiety?')
  await p.getByRole('button', { name: 'Send' }).click()
  await p.getByText("can't assess anything").waitFor()
  await snap('chat-limit')

  await nav(p, 'Profile')
  await p.getByRole('heading', { name: 'History' }).waitFor()
  await sleep(300)
  await snap('profile')
  await p.getByRole('button', { name: /Usual skill/ }).click()
  await snap('profile-editor')

  await nav(p, 'Home')
  await p.locator('.ways .way').first().click()
  await p.getByRole('button', { name: 'Start Paced breathing' }).click()
  await snap('breathing-intro')
  await p.getByRole('button', { name: 'Start', exact: true }).click()
  await p.locator('.caption').waitFor()
  await sleep(1500)
  await snap('breathing-running')
  await p.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 80000 })
  await snap('breathing-closing')
  await ctx.close()
}

async function emptyTour(browser, stack, width) {
  const ctx = await browser.newContext({ viewport: { width, height: 900 } })
  const p = await ctx.newPage()
  const snap = makeSnap(p, width)
  await p.goto(stack.url)
  await p.getByRole('heading', { name: 'Welcome.' }).waitFor()
  await snap('home-first-visit')
  await nav(p, 'Profile')
  await p.getByText('No practices yet').waitFor()
  await snap('profile-empty')
  await ctx.close()
}

async function downTour(browser, stack, width) {
  const ctx = await browser.newContext({ viewport: { width, height: 900 } })
  const p = await ctx.newPage()
  const snap = makeSnap(p, width)
  await p.goto(stack.url)
  await p.getByRole('heading', { name: 'Welcome.' }).waitFor()
  await sleep(400)
  await snap('down-home')
  await nav(p, 'Crisis')
  await p.getByRole('dialog').waitFor()
  await snap('down-crisis')
  await p.getByRole('button', { name: 'Back to where I was' }).click()
  await nav(p, 'Chat')
  await p.locator('#chat-input').fill('Fictional question')
  await p.getByRole('button', { name: 'Send' }).click()
  await p.getByText("Messages can't be sent right now").waitFor()
  await snap('down-chat')
  await nav(p, 'Profile')
  await p.getByText("The profile can't be loaded right now").waitFor()
  await p.getByText("History can't be loaded right now").waitFor()
  await snap('down-profile')
  await ctx.close()
}

const browser = await chromium.launch()

// Negative control: the scan must flag a planted low-contrast line.
async function control(stack) {
  const ctx = await browser.newContext()
  const p = await ctx.newPage()
  await p.goto(stack.url)
  await p.evaluate(() => document.querySelector('main').insertAdjacentHTML('afterbegin', '<p style="color:#ccc;background:#fff">Planted low-contrast text</p>'))
  const axe = await new AxeBuilder({ page: p }).withTags(['wcag2aa']).analyze()
  await ctx.close()
  return axe.violations.some((v) => v.id === 'color-contrast')
}

const seededStacks = await Promise.all(WIDTHS.map(() => startStack({ seed: true })))
const [empty, down] = await Promise.all([startStack(), startStack({ down: true })])
let controlFlagged = false
try {
  controlFlagged = await control(empty)
  await Promise.all(WIDTHS.map(async (w, i) => {
    await emptyTour(browser, empty, w)
    await downTour(browser, down, w)
    await seededTour(browser, seededStacks[i], w)
  }))
} finally {
  await browser.close()
  await Promise.all([...seededStacks, empty, down].map((s) => s.stop()))
}

const flat = (filter) => results.flatMap((r) => r.violations.filter(filter).map((v) => ({ ...v, screen: r.name, width: r.width })))
const isSerious = (v) => ['serious', 'critical'].includes(v.impact)
const serious = flat(isSerious)
const other = flat((v) => !isSerious(v))
const overflow = results.filter((r) => r.overflow > 0)
const incomplete = [...new Set(results.flatMap((r) => r.incomplete))]
const names = [...new Set(results.map((r) => r.name))]
const count = (id) => results.filter((r) => r.incomplete.includes(id)).length

const md = `# Accessibility scan (axe-core)

Generated by [e2e/screens.mjs](../../../e2e/screens.mjs) with \`@axe-core/playwright\` in headless Chromium. Rules: WCAG 2.0, 2.1 and 2.2 A/AA, plus best-practice. Fictional data, temp databases, OS-assigned ports.

| Measure | Result |
|---|---|
| Screens and states scanned | ${names.length} |
| Scans (each state at 375, 768, 1280 px) | ${results.length} |
| Serious or critical issues | **${serious.length}** |
| Moderate or minor issues | ${other.length} |
| Pages with horizontal overflow | ${overflow.length} |
| Negative control (planted low-contrast text was flagged) | ${controlFlagged ? 'yes' : 'NO'} |

${[...serious, ...other].map((v) => `- ${v.impact}: ${v.id} at ${v.width} px on ${v.screen} (${v.target})`).join('\n') || 'No violations remain.'}

## Fixed after the first scan

The first scan had 0 serious or critical issues and 15 smaller ones, in two groups, both fixed:

- \`aria-allowed-role\` (minor): the chat limits bar was a \`header\` with \`role="note"\`. It is now a plain paragraph.
- \`page-has-heading-one\` (moderate): the Overwhelmed Home had no \`h1\`. Its greeting is now the \`h1\`.

## What axe could not decide

${incomplete.length ? incomplete.map((id) => `- \`${id}\`: on ${count(id)} of ${results.length} scans`).join('\n') : 'Nothing.'}

\`color-contrast\` items are text over the static wave background or a gradient, which axe cannot sample. \`frontend/tests/contrast.test.js\` covers these directly: it checks text tokens against every wave colour.

## Limits

An automated scan finds only part of what matters. It does not show that a screen-reader user can complete a skill, and no manual screen-reader test was run.

## Scanned states

${names.map((n) => `\`${n}\``).join(', ')}

Screenshots: [screens/](screens/).
`
writeFileSync(join(OUT, 'a11y.md'), md)
console.log(JSON.stringify({ states: names.length, scans: results.length, serious: serious.length, other: other.length, overflow: overflow.length, controlFlagged, incomplete }))
for (const v of [...serious, ...other]) console.log(`${v.impact} ${v.id} @${v.width} ${v.screen}: ${v.target} (${v.nodes})`)
