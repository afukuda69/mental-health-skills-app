import { chromium } from 'playwright'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const browser = await chromium.launch()
async function begin() {
  const page = await browser.newPage()
  await page.goto('http://localhost:5180')
  await page.getByRole('button', { name: 'Tense or wound up' }).click()
  await page.getByRole('button', { name: /Paced breathing/ }).click()
  await page.getByText('1 of 7').waitFor({ timeout: 10000 })
  return page
}
// 1. Direct beacon through the Vite proxy
let page = await begin()
console.log('direct sendBeacon queued:', await page.evaluate(() =>
  navigator.sendBeacon('/api/sessions/diag-none/end', new Blob(['{"end_reason":"left"}'], { type: 'text/plain' }))))
await sleep(800)
// 2. Navigate away (pagehide on navigation)
await page.goto('about:blank'); await sleep(1500); console.log('navigated away')
// 3. Close with beforeunload
page = await begin(); await page.close({ runBeforeUnload: true }); await sleep(1500); console.log('closed (runBeforeUnload)')
// 4. Close plain
page = await begin(); await page.close(); await sleep(1500); console.log('closed (plain)')
await browser.close()
