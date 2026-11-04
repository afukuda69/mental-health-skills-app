// Final headless runs for manual-checks rows 2b, 4a, 4b, 6, 8 (Playwright, Chromium).
// Not part of the app or the test suite. Fictional data only.
// Expects one backend + frontend pair per mode, each with its own scratch DB:
//   mock :5293, mock_error :5294, mock_timeout :5295, live :5296
// Run from a folder with playwright installed:  node final-run.mjs <outdir>
import { chromium } from 'playwright'

const OUT = process.argv[2] || '.'
const URLS = { mock: 'http://localhost:5293', error: 'http://localhost:5294', timeout: 'http://localhost:5295', live: 'http://localhost:5296' }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const results = {}

async function open(browser, url, name) {
  const page = await browser.newPage({ viewport: { width: 420, height: 900 } })
  const log = []
  page.on('console', (m) => /^\[(timing|model|session)\]/.test(m.text()) && log.push(m.text()))
  await page.goto(url)
  results[name] = { console: log }
  return page
}
const tabs = (p) => p.locator('nav.tabbar button').allInnerTexts()

async function fullRun(browser, url, name) {
  const p = await open(browser, url, name)
  await p.getByRole('button', { name: 'Tense or wound up' }).click()
  await p.locator('.featured button.primary').click()
  await p.getByText('Cycle 7 of 7').waitFor({ timeout: 75000 })
  results[name].tabs_during = await tabs(p)
  await p.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 40000 })
  results[name].closing_text = await p.locator('.instruction').innerText()
  await p.screenshot({ path: `${OUT}/${name}-closing.png` })
  await p.close()
}

async function crisisTenSeconds(browser) {
  const name = 'row8_crisis'
  const p = await open(browser, URLS.mock, name)
  await p.locator('.featured button.primary').click()
  await p.getByText('Cycle 2 of 7').waitFor({ timeout: 25000 })
  await sleep(1000)
  const before = await p.locator('.caption').innerText()
  await p.getByRole('button', { name: 'Crisis', exact: true }).click()
  await p.getByText('988 Suicide & Crisis Lifeline').waitFor()
  await p.screenshot({ path: `${OUT}/${name}-panel.png` })
  await sleep(10000)
  const during = await p.locator('.caption').innerText()
  await p.getByRole('button', { name: 'Back to where I was' }).click()
  results[name].caption = { before, after_10s_in_panel: during, after_close: await p.locator('.caption').innerText() }
  await p.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 90000 })
  await p.close()
}

async function navigateAway(browser) {
  const name = 'row6_navigate_away'
  const p = await open(browser, URLS.mock, name)
  await p.locator('.featured button.primary').click()
  await p.getByText('Cycle 2 of 7').waitFor({ timeout: 25000 })
  await sleep(1000)
  await p.goto('about:blank')
  await sleep(1500)
  await p.close()
}

const browser = await chromium.launch()
await Promise.all([
  fullRun(browser, URLS.error, 'row4a_mock_error'),
  fullRun(browser, URLS.timeout, 'row4b_mock_timeout'),
  fullRun(browser, URLS.live, 'row2b_live'),
  crisisTenSeconds(browser),
  navigateAway(browser),
])
await browser.close()
console.log(JSON.stringify(results, null, 2))
