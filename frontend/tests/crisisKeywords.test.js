import { expect, it } from 'vitest'
import { matchesCrisisPhrase } from '../src/content/crisisKeywords.js'

it('reads the shared phrase list, same matches as the backend', () => {
  expect(matchesCrisisPhrase('Fictional: I want to die')).toBe(true)
  expect(matchesCrisisPhrase('fictional: I’m going to END IT ALL')).toBe(true)
  expect(matchesCrisisPhrase('I want to diet')).toBe(false)
  expect(matchesCrisisPhrase('')).toBe(false)
})
