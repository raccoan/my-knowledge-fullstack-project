import request from './request'


export interface ChatParams {
  question: string
}


export interface ChatSource {
  document_id: number
  content: string
  distance: number
}


interface StreamEvent {
  type: 'sources' | 'content' | 'done'
  sources?: ChatSource[]
  content?: string
}


export async function streamChat(
  params: ChatParams,
  onSources: (sources: ChatSource[]) => void,
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

      signal,
    },
  )


  if (!response.ok) {
    throw new Error(
      `请求失败：${response.status}`
    )
  }


  if (!response.body) {
    throw new Error(
      '浏览器不支持流式响应'
    )
  }


  const reader = response.body.getReader()

  const decoder = new TextDecoder(
    'utf-8'
  )

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
        }
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


          let data =
            line.slice(5)


          if (data.startsWith(' ')) {
            data = data.slice(1)
          }


          if (!data) {
            continue
          }


          const eventData =
            JSON.parse(data) as StreamEvent


          if (
            eventData.type === 'sources'
          ) {

            onSources(
              eventData.sources || []
            )

          } else if (
            eventData.type === 'content'
          ) {

            onMessage(
              eventData.content || ''
            )

          } else if (
            eventData.type === 'done'
          ) {

            onDone()

            return
          }
        }
      }
    }


    onDone()

  } catch (error) {

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