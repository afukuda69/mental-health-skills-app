import { describe, expect, it } from 'vitest'
import { SKILLS } from '../src/content/skills.js'
import { MIN_STEP_MS, plannedMs } from '../src/timing.js'

describe('STOP schedule', () => {
  const s = SKILLS.stop
  it('has the four design.md steps in order', () => {
    expect(s.steps.map((x) => x.title)).toEqual(['Stop.', 'Take a step back.', 'Observe.', 'Proceed mindfully.'])
  })
  it('plans 60 s (15 s per screen, design.md section d), within 90 s', () => {
    expect(plannedMs(s)).toBe(60000)
    expect(plannedMs(s)).toBeLessThanOrEqual(90000)
  })
})

describe('reframe schedule', () => {
  const r = SKILLS.reframe
  it('has three optional input steps and a reflection', () => {
    expect(r.steps.map((x) => x.prompt ?? 'reflection')).toEqual([
      "What's the thought?",
      'What supports that thought?',
      'Is there another way to see it?',
      'reflection',
    ])
    expect(r.steps.filter((x) => x.reflectOnNext)).toHaveLength(1)
  })
  it('plans 70 s assuming Next at each budget (3 x 20 s + 10 s reflection), within 90 s', () => {
    expect(plannedMs(r)).toBe(70000)
    expect(plannedMs(r)).toBeLessThanOrEqual(90000)
  })
})

it('Next waits 2 s per step, which fits inside every step budget', () => {
  for (const id of ['stop', 'reframe']) for (const st of SKILLS[id].steps) expect(st.stepMs).toBeGreaterThan(MIN_STEP_MS)
})
