interface FailureDetail {
  code?: string
  message?: string
  retry_after?: number
}

export class ApiRequestError extends Error {
  readonly status: number
  readonly code: string | undefined
  readonly retryAfterSeconds: number | null

  constructor(status: number, message: string, code?: string, retryAfterSeconds: number | null = null) {
    super(message)
    this.name = 'ApiRequestError'
    this.status = status
    this.code = code
    this.retryAfterSeconds = retryAfterSeconds
  }
}

function retrySeconds(value: unknown): number | null {
  if (typeof value !== 'string' && typeof value !== 'number') return null
  const seconds = Number(value)
  if (Number.isFinite(seconds)) return seconds > 0 ? Math.min(86400, Math.ceil(seconds)) : null
  if (typeof value === 'string') {
    const date = Date.parse(value)
    if (Number.isFinite(date)) return Math.min(86400, Math.max(1, Math.ceil((date - Date.now()) / 1000)))
  }
  return null
}

/** Axios 与 fetch 共用错误协议；不在拦截器自动重试有副作用的模型请求。 */
export function parseApiError(status: number, body: unknown, retryAfter?: unknown): ApiRequestError {
  const detail = body && typeof body === 'object' && 'detail' in body ? body.detail : undefined
  const data: FailureDetail = detail && typeof detail === 'object' ? detail : {}
  const message = typeof detail === 'string' ? detail
    : typeof data.message === 'string' ? data.message : `请求失败（${status}）`
  const code = typeof data.code === 'string' ? data.code : undefined
  const wait = retrySeconds(retryAfter) ?? retrySeconds(data.retry_after) ?? (status === 429 ? 1 : null)
  return new ApiRequestError(status, message, code, wait)
}

/** 这两种准入失败发生在服务端写入之前，可以安全撤销前端临时消息。 */
export function isAdmissionError(error: unknown): error is ApiRequestError {
  return error instanceof ApiRequestError && (
    error.status === 429 || (error.status === 503 && error.code === 'rate_limit_unavailable')
  )
}
