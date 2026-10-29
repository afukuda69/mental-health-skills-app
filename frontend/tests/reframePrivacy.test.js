// @vitest-environment happy-dom
// The reframe's typed text: steps 1-2 never reach the API client, the step-3
// answer reaches only requestReflection, and a crisis phrase opens the panel.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'

vi.mock('../src/api.js', () => ({
  send: vi.fn(),
  beacon: vi.fn(),
  getJSON: vi.fn(() => Promise.reject(new Error('offline'))),
  requestAcknowledgment: vi.fn(() => Promise.resolve(null)),
  requestReflection: vi.fn(() => Promise.resolve({ text: 'Another way to see it: fictional.', status: 'mock', crisis: false })),
}))
const api = await import('../src/api.js')
const { default: ReframeSkill } = await import('../src/components/ReframeSkill.vue')

let now = 0
beforeEach(() => {
  now = 0
  vi.spyOn(performance, 'now').mockImplementation(() => now)
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'setTimeout', 'clearTimeout'] })
})
afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
  vi.clearAllMocks()
})

async function waitStep(wrapper) {
  now += 2500
  vi.advanceTimersByTime(400)
  await flushPromises()
  await wrapper.find('button.primary').trigger('click')
  await flushPromises()
}

const allApiArgs = () =>
  JSON.stringify([api.send, api.beacon, api.requestAcknowledgment, api.requestReflection].map((f) => f.mock.calls))

it('keeps steps 1-2 private and sends only the step-3 answer for the reflection', async () => {
  const wrapper = mount(ReframeSkill, { props: { setupMs: 0 } })
  await flushPromises()
  await wrapper.find('textarea').setValue('FICTIONAL-STEP-ONE thought')
  await waitStep(wrapper)
  await wrapper.find('textarea').setValue('FICTIONAL-STEP-TWO support')
  await waitStep(wrapper)
  await wrapper.find('textarea').setValue('FICTIONAL-STEP-THREE other view')
  await waitStep(wrapper)

  expect(api.requestReflection).toHaveBeenCalledTimes(1)
  expect(api.requestReflection.mock.calls[0][1]).toBe('FICTIONAL-STEP-THREE other view')
  expect(allApiArgs()).not.toContain('FICTIONAL-STEP-ONE')
  expect(allApiArgs()).not.toContain('FICTIONAL-STEP-TWO')
  expect(wrapper.text()).toContain('Another way to see it: fictional.')

  await waitStep(wrapper) // Finish
  const endCall = api.send.mock.calls.find(([path]) => path.endsWith('/end'))
  expect(endCall[1].end_reason).toBe('completed')
  expect(endCall[1].steps_completed).toBe(4)
  expect(JSON.stringify(api.send.mock.calls)).not.toContain('FICTIONAL-STEP-THREE')
  wrapper.unmount()
})

it('a crisis phrase opens the panel, keeps the text, and is never sent', async () => {
  const wrapper = mount(ReframeSkill, { props: { setupMs: 0 } })
  await flushPromises()
  await wrapper.find('textarea').setValue('fictional test: I want to die')
  expect(wrapper.emitted('crisis')).toHaveLength(1)
  expect(wrapper.find('textarea').element.value).toBe('fictional test: I want to die')
  await waitStep(wrapper)
  await waitStep(wrapper)
  await wrapper.find('textarea').setValue('fictional: I want to die')
  await waitStep(wrapper)
  expect(api.requestReflection).not.toHaveBeenCalled()
  expect(allApiArgs()).not.toContain('want to die')
  wrapper.unmount()
})
