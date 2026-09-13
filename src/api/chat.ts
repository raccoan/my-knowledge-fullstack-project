import request from './request'

export interface ChatParams {
  question: string
}

export async function streamChat(
  params: ChatParams,
  onMessage: (content: string) => void,
  onDone: () => void,
  signal?: AbortSignal,
) {
  const token = localStorage.getItem('token')

  if (!token) {
    throw new Error('未登录')
  }

  const response = await fetch(
    `${request.defaults.baseURL}/chat/stream`,
    {
      method: 'POST',

      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },

      body: JSON.stringify(params),

      // 用于停止生成
      signal,
    },
  )

  if (!response.ok) {
    throw new Error(`请求失败：${response.status}`)
  }

  if (!response.body) {
    throw new Error('浏览器不支持流式响应')
  }

  const reader =
    response.body.getReader()

  const decoder =
    new TextDecoder('utf-8')

  let buffer = ''

  try {
    while (true) {
      const {
        value,
        done,
      } = await reader.read()

      if (done) {
        break
      }

      buffer += decoder.decode(
        value,
        {
          stream: true,
        },
      )

      const events =
        buffer.split('\n\n')

      buffer =
        events.pop() || ''

      for (const event of events) {
        const lines =
          event.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data:')) {
            continue
          }

          let content =
            line.slice(5)

          if (content.startsWith(' ')) {
            content =
              content.slice(1)
          }

          if (content === '[DONE]') {
            onDone()
            return
          }

          onMessage(content)
        }
      }
    }

    onDone()
  } catch (error) {
    // 用户主动停止
    if (
      error instanceof DOMException &&
      error.name === 'AbortError'
    ) {
      return
    }

    throw error
  } finally {
    reader.releaseLock()
  }
}