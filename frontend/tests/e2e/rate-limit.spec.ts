import { expect, test, type Page } from '@playwright/test'

async function setup(page: Page, status = 429) {
  let calls = 0
  await page.addInitScript(() => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('user', JSON.stringify({ id: 1, username: '测试用户' }))
  })
  await page.route('http://127.0.0.1:8000/**', async route => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    const headers = {
      'Access-Control-Allow-Origin': 'http://127.0.0.1:4180',
      'Access-Control-Allow-Headers': 'authorization,content-type',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Expose-Headers': 'Retry-After',
    }
    if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers })
    if (request.method() === 'POST' && ['/chat/stream', '/interviews/1/answer', '/interviews'].includes(path)) {
      calls++
      return route.fulfill({ status, headers: { ...headers, 'Retry-After': '2' }, json: {
        detail: { code: status === 429 ? 'rate_limit_exceeded' : 'rate_limit_unavailable',
          message: status === 429 ? '请求过于频繁，请稍后再试' : 'AI 服务暂时不可用，请稍后重试', retry_after: 2 },
      } })
    }
    const data = path === '/conversations' && request.method() === 'GET' ? [{ id: 1, title: '测试会话', updated_at: '2026-01-01' }]
      : path === '/conversations/1/messages' ? [
        { id: 10, role: 'user', content: '原始问题' },
        { id: 11, role: 'assistant', content: '需要保留的原始回答', sources: [] },
      ] : path === '/interviews/1' ? {
        id: 1, resume_id: 1, title: '测试面试', status: 'ongoing', current_question: '什么是闭包？',
        total_score: 0, messages: [{ id: 1, role: 'interviewer', content: '什么是闭包？', knowledge_gap: [] }],
      } : { id: 1, title: '新对话' }
    await route.fulfill({ headers, json: data })
  })
  return () => calls
}

for (const status of [429, 503]) {
  test(`chat ${status} restores input, removes temporary messages and requires manual retry`, async ({ page }) => {
    const calls = await setup(page, status)
    await page.goto('/chat')
    const input = page.getByPlaceholder('输入你的问题，Enter 发送，Shift + Enter 换行')
    await input.fill('未被受理的问题')
    await input.press('Enter')
    await expect(page.getByRole('status')).toContainText('秒后可重试')
    await expect(input).toHaveValue('未被受理的问题')
    await expect(page.locator('.message-row')).toHaveCount(0)
    await expect(page.getByRole('button', { name: /秒后重试|秒后可重试|秒后可发送/ })).toBeDisabled()
    await expect(page.getByRole('status')).toHaveCount(0, { timeout: 5000 })
    expect(calls()).toBe(1)
  })
}

test('regenerate preserves the previous answer when admission fails', async ({ page }) => {
  await setup(page)
  await page.goto('/chat')
  await page.getByText('测试会话', { exact: true }).click()
  await expect(page.getByText('需要保留的原始回答', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: '重新生成' }).click()
  await expect(page.getByRole('status')).toContainText('秒后可重试')
  await expect(page.getByText('需要保留的原始回答', { exact: true })).toBeVisible()
  await expect(page.locator('.message-row')).toHaveCount(2)
})

test('interview answer survives 429 and becomes manually retryable', async ({ page }) => {
  const calls = await setup(page)
  await page.goto('/interview?id=1')
  const input = page.getByPlaceholder('请输入你的回答...')
  await input.fill('我的回答需要保留')
  await page.getByRole('button', { name: /提交回答/ }).click()
  await expect(page.getByRole('status')).toContainText('秒后可重试')
  await expect(input).toHaveValue('我的回答需要保留')
  await expect(page.getByRole('button', { name: /秒后可提交/ })).toBeDisabled()
  await expect(page.getByRole('button', { name: /提交回答/ })).toBeEnabled({ timeout: 5000 })
  expect(calls()).toBe(1)
})

test('creating interview exposes a manual retry after 429', async ({ page }) => {
  const calls = await setup(page)
  await page.goto('/interview?resumeId=1')
  await expect(page.getByRole('status')).toContainText('秒后可重试')
  await expect(page.getByRole('button', { name: /秒后可重试/ })).toBeDisabled()
  await expect(page.getByRole('button', { name: '重试创建面试' })).toBeEnabled({ timeout: 5000 })
  expect(calls()).toBe(1)
})
