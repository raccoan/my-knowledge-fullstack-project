import request from "./request";

export interface Conversation {
  id:number
  title:string
  created_at:string
  updated_at:string
}

export interface ChatMessage {
  id:number
  conversation_id:number
  created_at:string
  role:'user' | 'assistant'
  content:string
}

// 创建会话
export async function createConversation(){
  const response = await request.post<Conversation>(
    '/conversations'
  )
  return response.data
}

// 获取所有会话
export async function getConversations(){
  const response = await request.get<Conversation[]>(
    '/conversations'
  )
  return response.data
}

// 获取单个会话所有消息
export async function getConversationMessages(conversationId:number) {
  const response = await request.get(`/conversations/${conversationId}/messages`)
  return response.data
}

// 删除某个会话

export async function deleteConversation(conversationId:number) {
  const response = await request.delete(`/conversations/${conversationId}`)
  return response.data
}


export const updateConversationTitle = (
  id: number,
  title: string
) => {

  return request.put(
    `/conversations/${id}`,
    null,
    {
      params: {
        title
      }
    }
  )
}



