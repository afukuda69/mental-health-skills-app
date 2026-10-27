// Re-run of the 3.2 browser checks after the visual restyle (headless Chromium
// via Playwright). Not part of the app or the test suite. Fictional data only.
// Expects my own servers on free ports, scratch DB, LLM_MODE=mock:
//   backend :8051, frontend :5211 (API_PORT=8051), frontend :5212 (API_PORT=8098, nothing listening = backend down)
// Run from a folder with playwright installed:  node restyle-run.mjs <outdir>
import { chromium } from 'playwright'

const OUT = process.argv[2] || '.'
const UP = 'http://localhost:5211'
const DOWN = 'http://localhost:5212'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const results = {}

async function open(browser, url, name) {
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } })
  const log = []
  page.on('console', (m) => /^\[(timing|model|session)\]/.test(m.text()) && log.push(m.text()))
  await page.goto(url)
  results[name] = log
  return page
}
const tap = (page, name, exact = true) => page.getByRole('button', { name, exact }).first().click()
// The featured card's button reads "Open practice", or "Use my usual: …" once history has a usual.
const openPractice = (page) => page.locator('.featured button.primary').click()
const tabs = (page) => page.locator('nav.tabbar button').allInnerTexts()

async function cleanRun(browser) {
  const p = await open(browser, UP, 'clean')
  await p.screenshot({ path: `${OUT}/01-home.png` })
  await tap(p, 'Tense or wound up')
  await openPractice(p)
  await p.screenshot({ path: `${OUT}/02-intro.png` })
  results.tabs_during_exercise = await tabs(p)
  await p.getByText('Cycle 1 of 7').waitFor({ timeout: 10000 })
  await sleep(1500)
  await p.screenshot({ path: `${OUT}/03-breathing.png` })
  await p.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 100000 })
  results.clean_closing = await p.locator('.instruction').innerText()
  await p.screenshot({ path: `${OUT}/04-closing.png` })
  await tap(p, 'Continue')
  await tap(p, 'Helped')
  await p.getByText('Done.').waitFor()
  results.tabs_after_exercise = await tabs(p)
  await p.screenshot({ path: `${OUT}/05-done.png` })
  await p.close()
}

async function pauseAndCrisisRun(browser) {
  const p = await open(browser, UP, 'pause+crisis')
  await openPractice(p)
  await p.getByText('Cycle 1 of 7').waitFor({ timeout: 10000 })
  await sleep(6000)
  await tap(p, 'Pause')
  await sleep(3000)
  await tap(p, 'Resume')
  await sleep(4000)
  const before = await p.locator('.caption').innerText()
  await tap(p, 'Crisis')
  await p.getByText('988 Suicide & Crisis Lifeline').waitFor()
  await p.screenshot({ path: `${OUT}/06-crisis-during-breathing.png` })
  await sleep(5000)
  await tap(p, 'Back to where I was')
  results.cycle_before_after_crisis = [before, await p.locator('.caption').innerText()]
  await p.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 110000 })
  await p.close()
}

async function backendDownRun(browser) {
  const p = await open(browser, DOWN, 'backend-down')
  await tap(p, 'Crisis')
  await p.getByText('988 Suicide & Crisis Lifeline').waitFor()
  await p.screenshot({ path: `${OUT}/07-backend-down-crisis.png` })
  await tap(p, 'Back to where I was')
  await openPractice(p)
  await p.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 100000 })
  results.down_closing = await p.locator('.instruction').innerText()
  await p.screenshot({ path: `${OUT}/08-backend-down-closing.png` })
  await p.close()
}

async function stopRun(browser) {
  const p = await open(browser, UP, 'stop')
  await openPractice(p)
  await p.getByText('Cycle 1 of 7').waitFor({ timeout: 10000 })
  await sleep(8000)
  await tap(p, 'Stop exercise')
  await p.getByText("Stopped. That's fine.").waitFor()
  await p.screenshot({ path: `${OUT}/09-stopped.png` })
  await p.close()
}

async function historyAndUsual(browser) {
  const p = await open(browser, UP, 'history')
  await p.getByRole('button', { name: /Use my usual/ }).waitFor({ timeout: 5000 })
  results.usual_button = await p.getByRole('button', { name: /Use my usual/ }).innerText()
  await p.screenshot({ path: `${OUT}/10-home-usual.png` })
  await tap(p, 'History')
  await p.locator('.history .row').first().waitFor()
  results.history_chips = await p.locator('.status').allInnerTexts()
  await p.screenshot({ path: `${OUT}/11-history.png`, fullPage: true })
  await p.close()
}

const browser = await chromium.launch()
const t0 = Date.now()
await Promise.all([cleanRun(browser), pauseAndCrisisRun(browser), backendDownRun(browser)])
await stopRun(browser)
await historyAndUsual(browser)
await browser.close()
results.wall_clock_s = Math.round((Date.now() - t0) / 1000)
console.log(JSON.stringify(results, null, 2))
