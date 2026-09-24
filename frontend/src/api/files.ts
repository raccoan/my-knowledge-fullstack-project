import request from "./request";

export interface FileItem {
  id: number
  file_id: number
  filename: string
  status: string
  chunk_count: number
  file_size: number | null
  created_at: string
}

export interface ChunkItem {
  id: number
  chunk_index: number
  content: string
}

export interface FileDetail {
  id: number
  file_id: number
  filename: string
  file_size: number | null
  status: string
  chunk_count: number
  created_at: string
  chunks: ChunkItem[]
}

// 获取用户文件列表
export async function getFiles() {
  const response = await request.get<FileItem[]>('/files')
  return response.data
}

// 获取文件详情
export async function getFileDetail(documentId: number) {
  const response = await request.get<FileDetail>(`/files/${documentId}`)
  return response.data
}

// 上传文件
export async function uploadFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await request.post('/files/upload', formData)

  return response.data
}

// 删除文件
export async function deleteFile(documentId: number) {
  const response = await request.delete(`/files/${documentId}`)

  return response.data
}