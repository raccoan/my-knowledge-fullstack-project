import { afterEach, describe, expect, it, vi } from 'vitest'
import { effectScope } from 'vue'
import { ApiRequestError, isAdmissionError, parseApiError } from '../../src/api/errors'
import { useRequestCooldown } from '../../src/composables/useRequestCooldown'
import { streamChat } from '../../src/api/chat'

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('server error contract', () => {
  it('prefers Retry-After and supports HTTP dates and body fallback', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-01T00:00:00Z'))
    expect(parseApiError(429, { detail: { retry_after: 9 } }, '3').retryAfterSeconds).toBe(3)
    expect(parseApiError(429, {}, 'Thu, 01 Jan 2026 00:00:05 GMT').retryAfterSeconds).toBe(5)
    expect(parseApiError(429, { detail: { retry_after: 9 } }, '-1').retryAfterSeconds).toBe(9)
    expect(parseApiError(429, null).retryAfterSeconds).toBe(1)
  })

  it('only classifies known pre-admission failures as safe to roll back', () => {
    expect(isAdmissionError(parseApiError(429, {}))).toBe(true)
    expect(isAdmissionError(parseApiError(503, { detail: { code: 'rate_limit_unavailable' } }))).toBe(true)
    expect(isAdmissionError(parseApiError(503, { detail: 'gateway unavailable' }))).toBe(false)
    expect(isAdmissionError(new Error('network failure'))).toBe(false)
  })
})

it('counts down from a deadline, never shortens an existing wait, cleans up on unmount', () => {
  vi.useFakeTimers()
  const scope = effectScope()
  const cooldown = scope.run(() => useRequestCooldown())!
  expect(cooldown.handleError(new Error('unrelated'))).toBe(false)
  cooldown.handleError(new ApiRequestError(429, 'wait', undefined, 5))
  vi.advanceTimersByTime(1000)
  cooldown.handleError(new ApiRequestError(429, 'wait', undefined, 1))
  expect(cooldown.remainingSeconds.value).toBe(4)
  vi.advanceTimersByTime(4000)
  expect(cooldown.blocked.value).toBe(false)
  expect(vi.getTimerCount()).toBe(0)
  cooldown.handleError(new ApiRequestError(429, 'wait', undefined, 5))
  scope.stop()
  expect(vi.getTimerCount()).toBe(0)
})

it.each([429, 503])('rejects SSE %s before accepted callback and never retries', async (status) => {
  vi.stubGlobal('localStorage', { getItem: () => 'test-token' })
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: {
    code: status === 429 ? 'rate_limit_exceeded' : 'rate_limit_unavailable', retry_after: 3,
  } }), { status, headers: { 'Retry-After': '3' } }))
  vi.stubGlobal('fetch', fetchMock)
  const accepted = vi.fn()
  await expect(streamChat({ question: 'hi', conversation_id: 1 }, vi.fn(), vi.fn(), vi.fn(), vi.fn(), undefined, accepted))
    .rejects.toMatchObject({ status, retryAfterSeconds: 3 })
  expect(accepted).not.toHaveBeenCalled()
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

it('still delivers accepted SSE content and done', async () => {
  vi.stubGlobal('localStorage', { getItem: () => 'test-token' })
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
    'data: {"type":"content","content":"hello"}\n\ndata: {"type":"done"}\n\n',
    { headers: { 'Content-Type': 'text/event-stream' } },
  )))
  const content = vi.fn(), done = vi.fn(), accepted = vi.fn()
  await streamChat({ question: 'hi', conversation_id: 1 }, vi.fn(), content, vi.fn(), done, undefined, accepted)
  expect(accepted).toHaveBeenCalledOnce()
  expect(content).toHaveBeenCalledWith('hello')
  expect(done).toHaveBeenCalledOnce()
})
