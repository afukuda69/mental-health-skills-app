// @vitest-environment happy-dom
// STOP's optional Observe note: it never reaches the API client, it clears when
// the exercise ends, and a crisis phrase in it opens the panel without clearing it.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'

vi.mock('../src/api.js', () => ({
  send: vi.fn(),
  beacon: vi.fn(),
  getJSON: vi.fn(() => Promise.reject(new Error('offline'))),
  requestAcknowledgment: vi.fn(() => Promise.resolve(null)),
  requestReflection: vi.fn(() => Promise.resolve(null)),
}))
const api = await import('../src/api.js')
const { default: StopSkill } = await import('../src/components/StopSkill.vue')

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

async function next(wrapper) {
  now += 2500
  vi.advanceTimersByTime(400)
  await flushPromises()
  await wrapper.find('button.primary').trigger('click')
  await flushPromises()
}

async function toObserve(wrapper) {
  await flushPromises()
  await next(wrapper)
  await next(wrapper)
  expect(wrapper.text()).toContain('Observe.')
}

const everyApiCall = () =>
  JSON.stringify([api.send, api.beacon, api.requestAcknowledgment, api.requestReflection].map((f) => f.mock.calls))

it('hides the note until asked, and offers it only on the Observe step', async () => {
  const wrapper = mount(StopSkill, { props: { setupMs: 0 } })
  await flushPromises()
  expect(wrapper.find('.note-toggle').exists()).toBe(false)
  await next(wrapper)
  await next(wrapper)
  expect(wrapper.find('.note-toggle').exists()).toBe(true)
  expect(wrapper.find('textarea').exists()).toBe(false)
  wrapper.unmount()
})

it('never passes the note to the API client, through to the end of the session', async () => {
  const wrapper = mount(StopSkill, { props: { setupMs: 0 } })
  await toObserve(wrapper)
  await wrapper.find('.note-toggle').trigger('click')
  await wrapper.find('textarea').setValue('FICTIONAL-STOP-NOTE a loud room')
  await next(wrapper)
  await next(wrapper) // Finish

  const end = api.send.mock.calls.find(([path]) => path.endsWith('/end'))
  expect(end[1].end_reason).toBe('completed')
  expect(end[1].steps_completed).toBe(4)
  expect(api.send.mock.calls.length).toBeGreaterThan(0) // the check below is not vacuous
  expect(everyApiCall()).not.toContain('FICTIONAL-STOP-NOTE')
  expect(api.requestReflection).not.toHaveBeenCalled()
  expect(api.requestAcknowledgment).not.toHaveBeenCalled()
  wrapper.unmount()
})

it('does not send the note when stopped mid-exercise, and clears it', async () => {
  const wrapper = mount(StopSkill, { props: { setupMs: 0 } })
  await toObserve(wrapper)
  await wrapper.find('.note-toggle').trigger('click')
  await wrapper.find('textarea').setValue('FICTIONAL-STOP-NOTE stopped early')
  await wrapper.find('button.danger-soft').trigger('click')
  await flushPromises()

  expect(everyApiCall()).toContain('stopped')
  expect(everyApiCall()).not.toContain('FICTIONAL-STOP-NOTE')
  expect(wrapper.vm.$.setupState.note).toBe('')
  wrapper.unmount()
})

it('a crisis phrase in the note opens the panel once, keeps the text, and is not sent', async () => {
  const wrapper = mount(StopSkill, { props: { setupMs: 0 } })
  await toObserve(wrapper)
  await wrapper.find('.note-toggle').trigger('click')
  await wrapper.find('textarea').setValue('fictional test: I want to die')
  expect(wrapper.emitted('crisis')).toHaveLength(1)
  await wrapper.find('textarea').setValue('fictional test: I want to die today')
  expect(wrapper.emitted('crisis')).toHaveLength(1)
  expect(wrapper.find('textarea').element.value).toBe('fictional test: I want to die today')
  expect(everyApiCall()).not.toContain('want to die')
  wrapper.unmount()
})
