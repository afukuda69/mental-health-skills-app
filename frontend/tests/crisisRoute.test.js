// @vitest-environment happy-dom
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, expect, it, vi } from 'vitest'
import App from '../src/App.vue'

afterEach(() => vi.unstubAllGlobals())

it('crisis panel opens from the entry screen with the backend down', async () => {
  const fetch = vi.fn(() => Promise.reject(new TypeError('Failed to fetch')))
  vi.stubGlobal('fetch', fetch)
  const wrapper = mount(App, { attachTo: document.body })
  await flushPromises()

  const button = wrapper.find('button.crisis-button')
  expect(button.exists()).toBe(true)
  await button.trigger('click')
  expect(wrapper.text()).toContain('988 Suicide & Crisis Lifeline')
  expect(wrapper.find('a[href="tel:988"]').exists()).toBe(true)
  expect(wrapper.text()).toContain('Nobody monitors it.')

  const callsBefore = fetch.mock.calls.length
  await wrapper.find('button.back-to-step').trigger('click')
  await button.trigger('click')
  expect(fetch.mock.calls.length).toBe(callsBefore) // opening the panel makes no request
  wrapper.unmount()
})

it('crisis components import only static content: no fetch, no await, no api module', () => {
  for (const file of ['CrisisPanel.vue', 'CrisisButton.vue']) {
    const src = readFileSync(resolve(process.cwd(), 'src/components', file), 'utf8')
    expect(src).not.toMatch(/\bfetch\(|\bawait\s|api\.js/)
    const imports = [...src.matchAll(/from '([^']+)'/g)].map((m) => m[1])
    expect(imports).toEqual(['../content/crisis.js'])
  }
})
