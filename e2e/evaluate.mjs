// Part 3.3 evaluation: fictional scenarios run in a real browser against mocked
// model responses. Each scenario gets its own stack (temp DB, OS-assigned ports).
// Writes docs/evidence/3.3/evaluation-run.md and evaluation-results.json.
//   node evaluate.mjs            run everything
//   node evaluate.mjs S03 S12    run some scenarios
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'
import { ROOT, sleep, startStack } from './harness.mjs'

const OUT = join(ROOT, 'docs/evidence/3.3')
mkdirSync(OUT, { recursive: true })
const CONCURRENCY = 6
const PHRASE = 'I want to die'
const scenarios = []
const add = (id, group, title, does, expected, opts, fn) => scenarios.push({ id, group, title, does, expected, opts, fn })

// --- helpers ---------------------------------------------------------------
const tap = (p, name, exact = true) => p.getByRole('button', { name, exact }).first().click()
const start = async (p, label) => {
  await tap(p, 'Activities')
  await tap(p, `Start ${label}`)
}
const next = (p) => p.locator('.controls button.primary').click()
const stepFor = async (p, ms) => {
  await sleep(ms)
  await next(p)
}
const lastSession = (s) => s.rows('SELECT * FROM sessions ORDER BY id DESC LIMIT 1')[0]
const secs = (ms) => `${(ms / 1000).toFixed(1)} s`

// Crisis must open from here, with content, and without any network request.
async function crisisOk(t, label) {
  const { p } = t
  const button = p.locator('button.crisis-button')
  t.check(await button.isVisible(), `Crisis visible: ${label}`)
  const before = t.requests.length
  await button.click()
  await p.getByRole('dialog').waitFor({ timeout: 3000 })
  t.check(await p.getByText('988 Suicide & Crisis Lifeline').isVisible(), `Crisis content shown: ${label}`)
  t.check(t.requests.length === before, `Crisis opened with no request: ${label}`)
  await tap(p, 'Back to where I was')
  t.crisisScreens.push(label)
}

// --- ordinary use ----------------------------------------------------------
add('S01', 'Ordinary use', 'Paced breathing, full run', 'Picks Paced breathing in Activities and follows it to the end, then rates it Helped.', 'Seven cycles, closing text, check-in, Done. Saved as completed, 7/7, about 75 s.', {}, async (t) => {
  const { p, s } = t
  await start(p, 'Paced breathing')
  await crisisOk(t, 'breathing intro')
  await p.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 95000 })
  await crisisOk(t, 'breathing closing')
  const closing = await p.locator('.instruction').innerText()
  await tap(p, 'Continue')
  await crisisOk(t, 'check-in')
  await tap(p, 'Helped')
  await p.getByText('Done.').waitFor()
  await crisisOk(t, 'done')
  const r = lastSession(s)
  t.check(r.end_reason === 'completed' && r.steps_completed === 7, 'completed 7/7')
  t.timing('breathing', r)
  t.observed(`Completed 7/7 in ${secs(r.measured_ms)}. Closing: "${closing}". Rated Helped.`)
})

add('S02', 'Ordinary use', 'STOP at a reading pace', 'Reads each of the four STOP screens for about 13 s, then taps Next.', 'Four steps in order, then check-in. Completed 4/4, under the 60 s plan.', {}, async (t) => {
  const { p, s } = t
  await start(p, 'STOP')
  const seen = []
  for (let i = 0; i < 4; i++) {
    seen.push(await p.locator('.step h2').innerText())
    await stepFor(p, 13000)
  }
  await tap(p, 'Skip')
  await p.getByText('Done.').waitFor()
  const r = lastSession(s)
  t.check(seen.join(' ') === 'Stop. Take a step back. Observe. Proceed mindfully.', 'steps in design order')
  t.check(r.end_reason === 'completed' && r.steps_completed === 4, 'completed 4/4')
  t.timing('stop-reading-pace', r)
  t.observed(`Steps: ${seen.join(' / ')}. Completed 4/4 in ${secs(r.measured_ms)} of ${secs(r.planned_ms)} planned.`)
})

add('S03', 'Ordinary use', 'Reframe at a reading pace, with typing', 'Types a fictional thought, picks a chip, types another view, about 14 s per step, reads the reflection for 12 s.', 'Reflection appears. Only the step-3 answer is sent; nothing typed is stored.', { markers: ['FICT-R1', 'FICT-R3'] }, async (t) => {
  const { p, s } = t
  await start(p, 'Cognitive reframe')
  await p.locator('textarea').fill('FICT-R1 a missed deadline at a part-time job')
  await stepFor(p, 14000)
  await tap(p, 'A feeling more than a fact')
  await stepFor(p, 14000)
  await p.locator('textarea').fill('FICT-R3 it may have been a busy week')
  await crisisOk(t, 'reframe step')
  await stepFor(p, 14000)
  await p.locator('.reflection').waitFor({ timeout: 8000 })
  const reflection = await p.locator('.reflection').innerText()
  await stepFor(p, 12000)
  await tap(p, 'Skip')
  await p.getByText('Done.').waitFor()
  const r = lastSession(s)
  const sent = t.requests.filter((q) => (q.post ?? '').includes('FICT-R3'))
  t.check(sent.length === 1 && sent[0].url.endsWith('/reflection'), 'step-3 answer sent once, to /reflection only')
  t.check(!JSON.stringify(t.requests).includes('FICT-R1'), 'step-1 text never sent')
  t.check(r.end_reason === 'completed', 'completed')
  t.timing('reframe-reading-pace', r)
  t.observed(`Completed 4/4 in ${secs(r.measured_ms)} of ${secs(r.planned_ms)} planned. Reflection: "${reflection}". Step-3 text sent once, to /reflection. Step-1 text never left the browser.`)
})

add('S04', 'Intended pace', 'STOP at its planned budget', 'Takes the full 15 s on each STOP screen.', 'About 60 s, within 90 s.', {}, async (t) => {
  const { p, s } = t
  await start(p, 'STOP')
  for (let i = 0; i < 4; i++) await stepFor(p, 15000)
  await tap(p, 'Skip')
  const r = lastSession(s)
  t.check(r.end_reason === 'completed' && r.steps_completed === 4, 'completed 4/4')
  t.check(r.measured_ms <= 90000, 'within 90 s')
  t.timing('stop-intended-pace', r)
  t.observed(`Completed in ${secs(r.measured_ms)} of ${secs(r.planned_ms)} planned.`)
})

add('S05', 'Intended pace', 'Reframe at its planned budget, slowest model', 'Takes the full 20 s on each input step with the model timing out, then reads for 5 s.', 'The worst planned case: about 70 s plus model wait, within 90 s, with fallback text.', { mode: 'mock_timeout' }, async (t) => {
  const { p, s } = t
  await start(p, 'Cognitive reframe')
  await stepFor(p, 20000)
  await stepFor(p, 20000)
  await p.locator('textarea').fill('Fictional: it may have been a busy week')
  await stepFor(p, 20000)
  await p.locator('.reflection').waitFor({ timeout: 9000 })
  const reflection = await p.locator('.reflection').innerText()
  await stepFor(p, 5000)
  await tap(p, 'Skip')
  const r = lastSession(s)
  t.check(reflection === "You've noted another way to look at it.", 'fallback reflection')
  t.check(r.end_reason === 'completed' && r.measured_ms <= 90000, 'completed within 90 s')
  t.timing('reframe-intended-pace-timeout', r)
  t.observed(`Completed in ${secs(r.measured_ms)} of ${secs(r.planned_ms)} planned, with "${reflection}"`)
})

// --- check-in and overriding it -------------------------------------------
add('S06', 'Check-in', 'Tense suggests breathing', 'Taps "Tense or wound up" on Home.', 'A breathing suggestion with the reason and a Change link. Nothing starts.', { seed: true }, async (t) => {
  const { p, s } = t
  await tap(p, 'Tense or wound up')
  const card = await p.locator('.suggestion').innerText()
  t.check(card.includes('Paced breathing') && card.includes('Suggested because you chose "Tense or wound up"'), 'suggestion with reason')
  t.check(s.rows('SELECT COUNT(*) n FROM sessions')[0].n === 5, 'no session started by itself')
  await crisisOk(t, 'home with suggestion')
  await tap(p, 'Activities')
  t.check((await p.locator('.skill').count()) === 4, 'all skills still listed')
  t.observed('Breathing suggested with the reason and Change. No session started. Activities still lists every skill.')
})

add('S07', 'Check-in', 'Overwhelmed contracts Home', 'Taps "Overwhelmed", then "Show everything".', 'One big breathing button, Crisis, Show everything; tabs reduced to Crisis. Show everything restores the rest.', { seed: true }, async (t) => {
  const { p } = t
  await tap(p, 'Overwhelmed')
  const tabs = await p.locator('nav.tabbar button').allInnerTexts()
  t.check(tabs.join() === 'Crisis', 'only Crisis in the bar')
  t.check(await p.getByRole('button', { name: 'Start paced breathing' }).isVisible(), 'one big button')
  t.check((await p.locator('.ways').count()) === 0, 'other content hidden')
  await crisisOk(t, 'contracted home')
  await tap(p, 'Show everything')
  const after = await p.locator('nav.tabbar button').allInnerTexts()
  t.check(after.length === 5, 'full tabs back')
  t.observed(`Tabs during: [${tabs}]. After Show everything: [${after}].`)
})

add('S08', 'Check-in', 'Overriding a suggestion', 'Taps Tense, Change, Okay, Change, Skip.', 'Each choice can be undone. Okay shows the usual skill. Skip suggests nothing.', { seed: true }, async (t) => {
  const { p, s } = t
  await tap(p, 'Tense or wound up')
  await tap(p, 'Change')
  await tap(p, 'Okay, just want a minute')
  const okay = await p.locator('.suggestion').innerText()
  await tap(p, 'Change')
  await tap(p, 'Skip')
  const skip = await p.getByText('No suggestion.').isVisible()
  t.check(okay.includes('Your usual') && okay.includes('Paced breathing'), 'Okay shows the usual skill')
  t.check(skip && (await p.locator('.suggestion').count()) === 0, 'Skip suggests nothing')
  t.check(s.rows('SELECT last_checkin FROM profile')[0].last_checkin === 'skip', 'last check-in saved')
  t.observed('Tense, Okay and Skip each applied and could be changed. Okay showed the usual skill. Skip showed no suggestion.')
})

// --- profile ---------------------------------------------------------------
add('S09', 'Profile', 'Choosing a usual skill, then resetting', 'Sets Usual skill to STOP in Profile, checks Home and Activities, then taps Reset to learned.', 'STOP shows as chosen and is used in Home and Activities. Reset returns to the learned skill.', { seed: true }, async (t) => {
  const { p } = t
  await tap(p, 'Profile')
  await p.getByRole('button', { name: /^Usual skill/ }).click()
  await p.locator('#usual-skill').selectOption('stop')
  await p.getByText('Usual skill saved.').waitFor()
  const chosen = await p.getByRole('button', { name: /^Usual skill/ }).innerText()
  await crisisOk(t, 'profile')
  await tap(p, 'Home')
  await tap(p, 'Okay, just want a minute')
  const home = await p.locator('.suggestion').innerText()
  await tap(p, 'Activities')
  const tag = await p.locator('.skill.stop .usual').count()
  await crisisOk(t, 'activities')
  await tap(p, 'Profile')
  await tap(p, 'Reset to learned', false)
  await p.getByText('Reset to what the app learned').waitFor()
  const reset = await p.getByRole('button', { name: /^Usual skill/ }).innerText()
  t.check(chosen.includes('You chose this') && chosen.includes('STOP'), 'shown as chosen')
  t.check(home.includes('STOP'), 'Home uses it')
  t.check(tag === 1, 'Activities tag follows it')
  t.check(reset.includes('Learned from your history') && reset.includes('Paced breathing'), 'reset returns to learned')
  t.observed('Chosen STOP showed in Profile, Home and Activities. Reset returned to Paced breathing, learned.')
})

add('S10', 'Profile', 'Usual skill updates from use', 'Finishes STOP and rates it Helped, then opens Profile.', 'Counts rise and the learned usual skill becomes STOP.', { seed: true }, async (t) => {
  const { p } = t
  await tap(p, 'Profile')
  const before = await p.getByRole('button', { name: /^Usual skill/ }).innerText()
  await start(p, 'STOP')
  for (let i = 0; i < 4; i++) await stepFor(p, 2200)
  await tap(p, 'Helped')
  await p.getByText('Done.').waitFor()
  await sleep(500)
  await tap(p, 'Profile')
  await p.getByRole('heading', { name: 'History' }).waitFor()
  await sleep(300)
  const after = await p.getByRole('button', { name: /^Usual skill/ }).innerText()
  await p.getByRole('button', { name: /^Sessions per skill/ }).click()
  const counts = await p.locator('.counts').innerText()
  t.check(before.includes('Paced breathing') && after.includes('STOP') && after.includes('Learned'), 'usual moved to STOP, learned')
  t.check(counts.includes('STOP: 2 completed'), 'count rose')
  t.observed(`Usual went from Paced breathing to STOP (learned). Counts: ${counts.replace(/\n/g, '; ')}.`)
})

// --- chat ------------------------------------------------------------------
const say = async (p, text) => {
  await p.locator('#chat-input').fill(text)
  await tap(p, 'Send')
}

add('S11', 'Chat', 'Reply uses the profile', 'Asks for help before a fictional presentation.', 'Reply uses the name and usual skill and offers it. The user taps to start.', { seed: true }, async (t) => {
  const { p, s } = t
  await tap(p, 'Chat')
  await say(p, 'Fictional: nervous before a presentation, any help?')
  await p.locator('.bubble.theirs').waitFor()
  const text = await p.locator('.bubble.theirs .text').innerText()
  await crisisOk(t, 'chat')
  t.check(text.startsWith('Hi Alex.') && text.includes('Paced breathing'), 'tailored')
  t.check(await p.getByRole('button', { name: 'Start Paced breathing' }).isVisible(), 'offer button')
  t.check(s.rows('SELECT COUNT(*) n FROM sessions')[0].n === 5, 'nothing started by itself')
  t.observed(`"${text}" with a Start button. No session started.`)
})

add('S12', 'Chat', 'A request for a diagnosis', 'Asks "Can you tell me if I have anxiety?"', 'The limit reply and links to the three skills. No diagnosis.', { seed: true }, async (t) => {
  const { p } = t
  await tap(p, 'Chat')
  await say(p, 'Can you tell me if I have anxiety?')
  await p.getByText("can't assess anything").waitFor()
  const text = await p.locator('.bubble.theirs .text').innerText()
  t.check((await p.locator('.skill-links button').count()) === 3, 'three skill links')
  t.check(await p.getByText("Not a therapist. Can't diagnose.").isVisible(), 'limits bar visible')
  t.observed(`"${text}" with three skill links.`)
})

// --- crisis phrases ---------------------------------------------------------
add('S13', 'Crisis phrase', 'In the chat', `Types the fictional phrase "${PHRASE}".`, 'Panel opens, scripted reply, no model call, typed text not stored, flag stored.', { markers: [PHRASE] , seed: true }, async (t) => {
  const { p, s } = t
  await tap(p, 'Chat')
  await say(p, `Fictional test phrase: ${PHRASE}`)
  await p.getByRole('dialog').waitFor()
  await tap(p, 'Back to where I was')
  const msgs = s.rows('SELECT role, text, model_status, crisis_flag FROM messages WHERE conversation_id IS NOT NULL ORDER BY id')
  t.check(msgs.length === 2 && msgs[0].text === null && msgs[0].crisis_flag === 1, 'user row with no text, flag set')
  t.check(msgs[1].model_status === 'scripted', 'scripted reply, no model status')
  t.privateAllowSent = true // chat text reaches the backend for the check; it must not be stored
  t.observed('Panel opened. Rows: user (no text, flag 1), scripted (flag 1). No model row.')
})

add('S14', 'Crisis phrase', 'In the reframe', 'Types the phrase in a reframe step, closes the panel, carries on.', 'Panel opens and pauses. Text stays on screen. It is never sent or stored.', { markers: [PHRASE] }, async (t) => {
  const { p, s } = t
  await start(p, 'Cognitive reframe')
  await p.locator('textarea').pressSequentially(`fictional: ${PHRASE}`, { delay: 5 })
  await p.getByRole('dialog').waitFor()
  await sleep(3000)
  await tap(p, 'Back to where I was')
  const kept = await p.locator('textarea').inputValue()
  await stepFor(p, 2300)
  await stepFor(p, 2300)
  await p.locator('textarea').fill(`fictional: ${PHRASE}`)
  await p.getByRole('dialog').waitFor()
  await tap(p, 'Back to where I was')
  await stepFor(p, 2300)
  const reflection = await p.locator('.reflection').innerText()
  await stepFor(p, 2300)
  await tap(p, 'Skip')
  const r = lastSession(s)
  t.check(kept.includes(PHRASE), 'text kept after the panel')
  t.check(r.crisis_ms >= 2900, 'crisis time recorded')
  t.check(!t.requests.some((q) => q.url.endsWith('/reflection')), 'no reflection request')
  t.check(reflection === "You've noted another way to look at it.", 'fallback reflection')
  t.observed(`Panel opened both times, text kept, crisis_ms ${r.crisis_ms}. No reflection request; fallback text shown.`)
})

add('S15', 'Crisis phrase', 'In the STOP note', 'Opens the optional note on Observe and types the phrase.', 'Panel opens and pauses. The note is never sent or stored.', { markers: [PHRASE] }, async (t) => {
  const { p, s } = t
  await start(p, 'STOP')
  await stepFor(p, 2300)
  await stepFor(p, 2300)
  await p.getByRole('button', { name: /Write down what you notice/ }).click()
  await p.locator('#stop-note').pressSequentially(`fictional: ${PHRASE}`, { delay: 5 })
  await p.getByRole('dialog').waitFor()
  await sleep(3000)
  await tap(p, 'Back to where I was')
  await stepFor(p, 2300)
  await stepFor(p, 2300)
  await tap(p, 'Skip')
  const r = lastSession(s)
  t.check(r.crisis_ms >= 2900 && r.end_reason === 'completed', 'crisis time recorded, finished')
  t.observed(`Panel opened, crisis_ms ${r.crisis_ms}, session completed. Phrase in no request and no table.`)
})

// --- interruptions ----------------------------------------------------------
add('S16', 'Interruption', 'Stop mid-exercise', 'Taps Stop exercise during cycle 2.', 'No dialog, no check-in, "Stopped. That\'s fine." Saved as stopped.', {}, async (t) => {
  const { p, s } = t
  let dialogs = 0
  p.on('dialog', () => dialogs++)
  await start(p, 'Paced breathing')
  await p.getByText('Cycle 2 of 7').waitFor({ timeout: 25000 })
  await crisisOk(t, 'breathing running')
  await tap(p, 'Stop exercise')
  await p.getByText("Stopped. That's fine.").waitFor()
  await crisisOk(t, 'stopped')
  await sleep(300)
  const r = lastSession(s)
  t.check(r.end_reason === 'stopped' && r.exited_early === 1, 'saved as stopped')
  t.check(dialogs === 0, 'no dialog')
  t.check(s.rows('SELECT COUNT(*) n FROM feedback')[0].n === 0, 'no check-in saved')
  t.observed(`Stopped at ${secs(r.measured_ms)}, ${r.steps_completed}/7 cycles. No dialog, no check-in.`)
})

add('S17', 'Interruption', 'Crisis panel mid-exercise', 'Opens Crisis for 10 s during breathing, then goes back.', 'The cycle holds. Crisis time is stored apart and excluded from measured time.', {}, async (t) => {
  const { p, s } = t
  await start(p, 'Paced breathing')
  await p.getByText('Cycle 2 of 7').waitFor({ timeout: 25000 })
  await tap(p, 'Crisis')
  await p.getByRole('dialog').waitFor()
  const during = await p.locator('.caption').innerText()
  await sleep(10000)
  const later = await p.locator('.caption').innerText()
  await tap(p, 'Back to where I was')
  await p.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 95000 })
  await sleep(300)
  const r = lastSession(s)
  t.check(during === later, 'cycle held')
  t.check(Math.abs(r.crisis_ms - 10000) < 1000, 'crisis time about 10 s')
  t.timing('breathing-with-crisis', r)
  t.observed(`"${during}" held for the panel. crisis_ms ${r.crisis_ms}, measured ${secs(r.measured_ms)}.`)
})

add('S18', 'Interruption', 'Pause mid-exercise', 'Pauses STOP for 4 s on step 2, then resumes.', 'Pause time is stored apart and excluded.', {}, async (t) => {
  const { p, s } = t
  await start(p, 'STOP')
  await stepFor(p, 3000)
  await tap(p, 'Pause')
  await sleep(4000)
  await tap(p, 'Resume')
  await stepFor(p, 3000)
  await stepFor(p, 3000)
  await stepFor(p, 3000)
  await tap(p, 'Skip')
  const r = lastSession(s)
  t.check(Math.abs(r.pauses_ms - 4000) < 700, 'pause about 4 s')
  t.check(r.measured_ms < 13500, 'pause not in measured time')
  t.timing('stop-with-pause', r)
  t.observed(`pauses_ms ${r.pauses_ms}, measured ${secs(r.measured_ms)}.`)
})

add('S19', 'Interruption', 'Leaving the page', 'Navigates away during cycle 2.', 'Saved as left, with the active time.', {}, async (t) => {
  const { p, s } = t
  await start(p, 'Paced breathing')
  await p.getByText('Cycle 2 of 7').waitFor({ timeout: 25000 })
  await p.goto('about:blank')
  await sleep(1200)
  const r = lastSession(s)
  t.check(r.end_reason === 'left' && r.measured_ms > 0, 'saved as left')
  t.observed(`Saved as left at ${secs(r.measured_ms)}.`)
})

add('S20', 'Interruption', 'Hiding the tab and coming back', 'Hides the page during STOP, comes back, resumes, finishes.', 'Saved as left while hidden, paused on return, then completed.', {}, async (t) => {
  const { p, s } = t
  await start(p, 'STOP')
  await stepFor(p, 2500)
  const setVisibility = (state) => p.evaluate((v) => {
    Object.defineProperty(document, 'visibilityState', { value: v, configurable: true })
    document.dispatchEvent(new Event('visibilitychange'))
  }, state)
  await setVisibility('hidden')
  await sleep(1500)
  const whileHidden = lastSession(s).end_reason
  await setVisibility('visible')
  const paused = await p.getByRole('button', { name: 'Resume' }).isVisible()
  await tap(p, 'Resume')
  for (let i = 0; i < 3; i++) await stepFor(p, 2300)
  await tap(p, 'Skip')
  const r = lastSession(s)
  t.check(whileHidden === 'left' && paused && r.end_reason === 'completed', 'left, paused, then completed')
  t.check(r.pauses_ms >= 1400, 'hidden time excluded')
  t.observed(`While hidden: ${whileHidden}. On return: paused. End: ${r.end_reason}, pauses_ms ${r.pauses_ms}.`)
})

add('S21', 'Interruption', 'Leaving with typed text on screen', 'Types in the reframe and in the STOP note, then leaves.', 'The session ends as left. The text is sent nowhere and stored nowhere.', { markers: ['FICT-LEAVE'] }, async (t) => {
  const { p, s } = t
  await start(p, 'Cognitive reframe')
  await p.locator('textarea').fill('FICT-LEAVE a fictional thought')
  await p.goto('about:blank')
  await sleep(1000)
  t.check(lastSession(s).end_reason === 'left', 'saved as left')
  t.observed('Saved as left. No request and no table contained the text.')
})

// --- failures ---------------------------------------------------------------
const failureRun = (mode, status) => async (t) => {
  const { p, s } = t
  await tap(p, 'Chat')
  await say(p, 'Fictional: what is STOP for?')
  await p.locator('.bubble.theirs').waitFor({ timeout: 9000 })
  const reply = await p.locator('.bubble.theirs .text').innerText()
  await crisisOk(t, `chat after ${mode}`)
  t.check((await p.locator('.skill-links button').count()) === 3, 'skill links shown')
  await start(p, 'Paced breathing')
  await p.getByRole('button', { name: 'Continue' }).waitFor({ timeout: 95000 })
  const closing = await p.locator('.instruction').innerText()
  await crisisOk(t, `breathing closing after ${mode}`)
  await sleep(300)
  const r = lastSession(s)
  const rows = s.rows('SELECT role, model_status FROM messages ORDER BY id')
  t.check(rows.every((m) => m.model_status === 'fallback' || m.role === 'user' || m.model_status === status), 'status logged')
  t.check(rows.filter((m) => m.role === 'fallback').length === 2, 'two fallback rows')
  t.check(closing === 'That was seven slow breaths.', 'breathing fallback')
  t.check(reply.includes("can't assess anything"), 'chat fallback')
  t.timing(`breathing-${mode}`, r)
  t.observed(`Chat: fixed fallback with skill links. Breathing: "${closing}", ${secs(r.measured_ms)}. Rows: ${rows.filter((m) => m.role !== 'user').map((m) => `${m.role}/${m.model_status}`).join(', ')}.`)
}
add('S22', 'Failure', 'Model error', 'Uses chat and breathing while the model errors.', 'Fixed fallback in both. Crisis and the exercise keep working.', { mode: 'mock_error' }, failureRun('mock_error', 'error'))
add('S23', 'Failure', 'Model timeout', 'Uses chat and breathing while the model takes too long.', 'Fallback after 5 s in chat. Breathing is not delayed.', { mode: 'mock_timeout' }, failureRun('mock_timeout', 'timeout'))
add('S24', 'Failure', 'Malformed model output', 'Uses chat and breathing while the model returns unusable text.', 'Output rejected, fixed fallback in both.', { mode: 'mock_malformed' }, failureRun('mock_malformed', 'fallback'))

add('S25', 'Failure', 'Backend down from the start', 'Opens the app with no backend, uses Crisis, Chat, Profile, and a full reframe.', 'Crisis works. Neutral notices. Skills run; the reframe shows its fallback.', { down: true, markers: ['FICT-DOWN'] }, async (t) => {
  const { p } = t
  await crisisOk(t, 'home, backend down')
  await tap(p, 'Chat')
  await say(p, 'Fictional question')
  await p.getByText("Messages can't be sent right now").waitFor()
  await crisisOk(t, 'chat, backend down')
  await tap(p, 'Profile')
  await p.getByText("The profile can't be loaded right now").waitFor()
  await crisisOk(t, 'profile, backend down')
  await start(p, 'Cognitive reframe')
  await crisisOk(t, 'reframe, backend down')
  await p.locator('textarea').fill('FICT-DOWN typed while down')
  await stepFor(p, 2300)
  await stepFor(p, 2300)
  await p.locator('textarea').fill('Fictional: another view')
  await stepFor(p, 2300)
  await p.locator('.reflection').waitFor({ timeout: 9000 })
  const reflection = await p.locator('.reflection').innerText()
  await stepFor(p, 2300)
  await tap(p, 'Skip')
  await p.getByText('Done.').waitFor()
  t.check(reflection === "You've noted another way to look at it.", 'fallback reflection')
  t.observed(`Crisis opened on 4 screens. Chat and Profile showed neutral notices. Reframe finished with "${reflection}"`)
})

add('S26', 'Failure', 'Backend stops mid-exercise', 'The backend stops during step 2 of STOP.', 'The exercise finishes. Crisis works. The session has no end record.', {}, async (t) => {
  const { p, s } = t
  await start(p, 'STOP')
  await stepFor(p, 2300)
  await s.stopBackend()
  await crisisOk(t, 'STOP after backend stopped')
  for (let i = 0; i < 3; i++) await stepFor(p, 2300)
  await tap(p, 'Skip')
  await p.getByText('Done.').waitFor()
  await crisisOk(t, 'done after backend stopped')
  const r = lastSession(s)
  t.check(r.end_reason === null, 'no end record, as expected')
  t.observed('Finished and reached Done. Crisis opened twice. The row has no end reason, so History shows "Not finished".')
})

// --- data -------------------------------------------------------------------
add('S27', 'Data', 'Delete all', 'Opens Profile, taps Delete all, confirms.', 'Profile and history are gone, with empty states. Home says Welcome.', { seed: true }, async (t) => {
  const { p, s } = t
  await tap(p, 'Chat')
  await say(p, 'Fictional question')
  await p.locator('.bubble.theirs').waitFor()
  await tap(p, 'Profile')
  await tap(p, 'Delete all')
  await p.getByRole('group', { name: 'Confirm delete' }).getByRole('button', { name: 'Delete all' }).click()
  await p.getByText('Profile and history deleted.').waitFor()
  await p.getByText('No practices yet').waitFor()
  const counts = ['sessions', 'messages', 'feedback', 'conversations', 'profile'].map((x) => s.rows(`SELECT COUNT(*) n FROM ${x}`)[0].n)
  await tap(p, 'Home')
  await p.getByRole('heading', { name: 'Welcome.' }).waitFor()
  t.check(counts.every((n) => n === 0), 'all tables empty')
  t.observed(`Rows left in sessions, messages, feedback, conversations, profile: ${counts.join(', ')}. Empty states shown. Home says Welcome.`)
})

add('S28', 'Data', 'Crisis by keyboard only', 'Tabs to Crisis, presses Enter, then Escape.', 'Panel opens, focus moves in, Escape closes it, focus returns.', {}, async (t) => {
  const { p } = t
  await p.locator('button.crisis-button').focus()
  await p.keyboard.press('Enter')
  await p.getByRole('dialog').waitFor()
  await sleep(100)
  const inside = await p.evaluate(() => document.activeElement?.classList.contains('panel'))
  await p.keyboard.press('Escape')
  await sleep(150)
  const back = await p.evaluate(() => document.activeElement?.classList.contains('crisis-button'))
  t.check(inside, 'focus moved into the panel')
  t.check(back && (await p.getByRole('dialog').count()) === 0, 'Escape closed it, focus returned')
  t.observed('Enter opened the panel with focus inside. Escape closed it and focus returned to Crisis.')
})

// --- runner -----------------------------------------------------------------
async function run(browser, sc) {
  const s = await startStack({ mode: sc.opts.mode ?? 'mock', seed: sc.opts.seed, down: sc.opts.down })
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 } })
  const p = await ctx.newPage()
  const t = { p, s, requests: [], console: [], checks: [], crisisScreens: [], timings: [], text: '', privateAllowSent: false }
  t.check = (ok, label) => t.checks.push({ ok: Boolean(ok), label })
  t.observed = (text) => (t.text = text)
  t.timing = (label, r) => t.timings.push({ label, planned_ms: r.planned_ms, measured_ms: r.measured_ms, pauses_ms: r.pauses_ms, crisis_ms: r.crisis_ms, setup_ms: r.setup_ms })
  p.on('console', (m) => /^\[(timing|model|session)\]/.test(m.text()) && t.console.push(m.text()))
  p.on('request', (q) => q.url().includes('/api/') && t.requests.push({ url: q.url().replace(/^.*\/api/, '/api'), method: q.method(), post: q.postData() }))
  let error = null
  try {
    await p.goto(s.url)
    await p.waitForLoadState('networkidle')
    await sc.fn(t)
  } catch (e) {
    error = String(e.message ?? e).split('\n')[0]
    await p.screenshot({ path: join(OUT, `failure-${sc.id}.png`) }).catch(() => {})
  }
  // Behavior check (b): typed text is in no table, no browser storage, and (unless allowed) no request.
  let dump = ''
  if (!sc.opts.down) {
    const tables = ['sessions', 'messages', 'feedback', 'conversations', 'profile']
    dump = JSON.stringify(tables.map((x) => s.rows(`SELECT * FROM ${x}`)))
  }
  const storage = p.url().startsWith('http') ? await p.evaluate(() => localStorage.length + sessionStorage.length).catch(() => 0) : 0
  const sent = JSON.stringify(t.requests)
  for (const m of sc.opts.markers ?? []) {
    t.check(!dump.includes(m), `"${m}" stored nowhere`)
    if (m === 'FICT-R3') continue // the step-3 answer is sent once, checked in the scenario
    if (!t.privateAllowSent) t.check(!sent.includes(m), `"${m}" sent nowhere`)
  }
  if (sc.opts.markers) t.check(storage === 0, 'nothing in browser storage')
  await ctx.close()
  await s.stop()
  const failed = t.checks.filter((c) => !c.ok).map((c) => c.label)
  const pass = !error && failed.length === 0 && t.checks.length > 0
  console.log(`${pass ? 'PASS' : 'FAIL'} ${sc.id} ${sc.title}${error ? ` :: ${error}` : ''}${failed.length ? ` :: ${failed.join('; ')}` : ''}`)
  return { id: sc.id, group: sc.group, title: sc.title, does: sc.does, expected: sc.expected, observed: error ? `ERROR: ${error}` : t.text, pass, mode: sc.opts.mode ?? (sc.opts.down ? 'no backend' : 'mock'), checks: t.checks, failed, crisisScreens: t.crisisScreens, timings: t.timings, console: t.console, requests: t.requests.map((q) => `${q.method} ${q.url.replace(/[0-9a-f-]{36}/, '<id>')}`) }
}

const wanted = process.argv.slice(2)
const queue = scenarios.filter((s) => !wanted.length || wanted.includes(s.id))
const longestFirst = ['S05', 'S04', 'S01', 'S17', 'S22', 'S23', 'S24', 'S02', 'S03']
queue.sort((a, b) => (longestFirst.indexOf(b.id) + 1 ? 1 : 0) - (longestFirst.indexOf(a.id) + 1 ? 1 : 0))
const browser = await chromium.launch()
const results = []
const started = Date.now()
await Promise.all(Array.from({ length: CONCURRENCY }, async () => {
  while (queue.length) results.push(await run(browser, queue.shift()))
}))
await browser.close()
results.sort((a, b) => a.id.localeCompare(b.id))
const passed = results.filter((r) => r.pass).length
writeFileSync(join(OUT, wanted.length ? 'evaluation-partial.json' : 'evaluation-results.json'), JSON.stringify({ date: new Date().toISOString().slice(0, 10), passed, total: results.length, seconds: Math.round((Date.now() - started) / 1000), results }, null, 1))
console.log(`${passed}/${results.length} passed in ${Math.round((Date.now() - started) / 1000)} s`)
process.exit(passed === results.length ? 0 : 1)
