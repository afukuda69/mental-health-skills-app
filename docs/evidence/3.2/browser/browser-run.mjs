// Automated browser run (headless Chromium via Playwright), used for the 3.2
// evidence. Not part of the app or the test suite. Fictional data only.
// Expects: backend on :8010 (LLM_MODE=mock), frontend on :5180 (API_PORT=8010),
// and a second frontend on :5181 whose API_PORT points at nothing (backend down).
// Run from a folder with playwright installed:  node browser-run.mjs <outdir>
import { chromium } from 'playwright'

const OUT = process.argv[2] || '.'
const UP = 'http://localhost:5180'
const DOWN = 'http://localhost:5181'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function open(browser, url, name) {
  const page = await browser.newPage({ viewport: { width: 900, height: 760 } })
  const log = []
  page.on('console', (m) => log.push(`[${name}] ${m.type()}: ${m.text()}`))
  await page.goto(url)
  return { page, log }
}

async function startBreathing(page) {
  await page.getByRole('button', { name: 'Tense or wound up' }).click()
  await page.getByRole('button', { name: /Paced breathing/ }).click()
  await page.getByText('Breathe in as the circle grows').waitFor()
}

const results = {}

async function cleanRun(browser) {
  const { page, log } = await open(browser, UP, 'clean')
  await startBreathing(page)
  await page.screenshot({ path: `${OUT}/01-intro.png` })
  await page.getByText('1 of 7').waitFor({ timeout: 10000 })
  await sleep(1500)
  await page.screenshot({ path: `${OUT}/02-breathing.png` })
  await page.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 100000 })
  results.cleanClosing = await page.locator('.instruction').innerText()
  await page.screenshot({ path: `${OUT}/03-closing.png` })
  await page.getByRole('button', { name: 'Continue' }).click()
  await page.getByRole('button', { name: 'Helped' }).click()
  await page.getByText('Done.').waitFor()
  await page.screenshot({ path: `${OUT}/04-done.png` })
  results.clean = log
  await page.close()
}

async function pauseAndCrisisRun(browser) {
  const { page, log } = await open(browser, UP, 'pause+crisis')
  await startBreathing(page)
  await page.getByText('1 of 7').waitFor({ timeout: 10000 })
  await sleep(6000)
  await page.getByRole('button', { name: 'Pause' }).click()
  await sleep(3000)
  await page.getByRole('button', { name: 'Resume' }).click()
  await sleep(4000)
  const before = await page.locator('.counter').innerText()
  await page.getByRole('button', { name: 'Crisis support' }).click()
  await page.getByText('988 Suicide & Crisis Lifeline').waitFor()
  await page.screenshot({ path: `${OUT}/05-crisis-during-breathing.png` })
  await sleep(5000)
  await page.getByRole('button', { name: 'Back to where I was' }).click()
  const after = await page.locator('.counter').innerText()
  results.crisisCounter = { before, after }
  await page.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 110000 })
  results.pauseCrisis = log
  await page.close()
}

async function backendDownRun(browser) {
  const { page, log } = await open(browser, DOWN, 'backend-down')
  await page.getByRole('button', { name: 'Crisis support' }).click()
  await page.getByText('988 Suicide & Crisis Lifeline').waitFor()
  await page.screenshot({ path: `${OUT}/06-backend-down-crisis.png` })
  await page.getByRole('button', { name: 'Back to where I was' }).click()
  results.downUsualButton = await page.getByRole('button', { name: /Use my usual/ }).count()
  await startBreathing(page)
  await page.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 100000 })
  results.downClosing = await page.locator('.instruction').innerText()
  await page.screenshot({ path: `${OUT}/07-backend-down-closing.png` })
  results.down = log
  await page.close()
}

async function stopRun(browser) {
  const { page, log } = await open(browser, UP, 'stop')
  await startBreathing(page)
  await page.getByText('1 of 7').waitFor({ timeout: 10000 })
  await sleep(8000)
  await page.getByRole('button', { name: 'Stop exercise' }).click()
  await page.getByText("Stopped. That's fine.").waitFor()
  await page.screenshot({ path: `${OUT}/08-stopped.png` })
  results.stop = log
  await page.close()
}

async function leftRun(browser) {
  const { page, log } = await open(browser, UP, 'left')
  await startBreathing(page)
  await page.getByText('1 of 7').waitFor({ timeout: 10000 })
  await sleep(6000)
  await page.close({ runBeforeUnload: true })
  await sleep(1500)
  results.left = log
}

async function historyAndUsual(browser) {
  const { page } = await open(browser, UP, 'history')
  await page.getByRole('button', { name: /Use my usual/ }).waitFor({ timeout: 5000 })
  results.usualLabel = await page.getByRole('button', { name: /Use my usual/ }).innerText()
  await page.screenshot({ path: `${OUT}/09-entry-usual.png` })
  await page.getByRole('button', { name: 'History' }).click()
  await page.locator('.history li').first().waitFor()
  results.history = await page.locator('.history ul').innerText()
  await page.getByRole('button', { name: 'Show message' }).first().click()
  await page.screenshot({ path: `${OUT}/10-history.png` })
  await page.close()
}

const browser = await chromium.launch()
const t0 = Date.now()
await Promise.all([cleanRun(browser), pauseAndCrisisRun(browser), backendDownRun(browser)])
await stopRun(browser)
await leftRun(browser)
await historyAndUsual(browser)
await browser.close()
results.wallClockS = Math.round((Date.now() - t0) / 1000)
console.log(JSON.stringify(results, null, 2))
