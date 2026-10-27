import { describe, expect, it } from 'vitest'
import { SKILLS } from '../src/content/skills.js'
import { breathingPosition, createExerciseClock, plannedMs } from '../src/timing.js'

const skill = SKILLS.breathing

describe('breathing schedule', () => {
  it('plans 75 s, within the 90 s budget', () => {
    expect(plannedMs(skill)).toBe(75000)
    expect(plannedMs(skill)).toBeLessThanOrEqual(90000)
  })

  it('uses 4 s in / 6 s out for 7 cycles', () => {
    expect([skill.inMs, skill.outMs, skill.cycles]).toEqual([4000, 6000, 7])
  })

  it('walks intro -> breathing -> closing', () => {
    expect(breathingPosition(skill, 4000, null).stage).toBe('intro')
    expect(breathingPosition(skill, 5000, 5000)).toMatchObject({ stage: 'breathing', cycle: 1, phase: 'in' })
    expect(breathingPosition(skill, 9500, 5000)).toMatchObject({ cycle: 1, phase: 'out', phaseRemainingS: 6 })
    expect(breathingPosition(skill, 25000, 5000)).toMatchObject({ cycle: 3, phase: 'in', cyclesDone: 2 })
    expect(breathingPosition(skill, 74999, 5000)).toMatchObject({ cycle: 7, phase: 'out' })
    expect(breathingPosition(skill, 75000, 5000)).toMatchObject({ stage: 'closing', cyclesDone: 7 })
  })
})

describe('exercise clock', () => {
  it('excludes user pauses and crisis time from measured time', () => {
    let t = 0
    const clock = createExerciseClock(() => t)
    clock.start()
    t = 10000
    clock.hold('user')
    t = 13000
    clock.release('user')
    t = 20000
    clock.hold('crisis')
    t = 27000
    clock.release('crisis')
    t = 30000
    expect(clock.report()).toEqual({ measured_ms: 20000, pauses_ms: 3000, crisis_ms: 7000 })
  })

  it('counts overlap of pause and crisis as crisis time only', () => {
    let t = 0
    const clock = createExerciseClock(() => t)
    clock.start()
    t = 1000
    clock.hold('user')
    t = 2000
    clock.hold('crisis')
    t = 5000
    clock.release('crisis')
    t = 6000
    clock.release('user')
    t = 7000
    expect(clock.report()).toEqual({ measured_ms: 2000, pauses_ms: 2000, crisis_ms: 3000 })
  })
})
