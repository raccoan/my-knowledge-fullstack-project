import request from './request'

export interface FileItem {
  id: number
  file_id: number
  filename: string
  status: 'processing' | 'completed' | 'failed'
  chunk_count: number
  file_size: number | null
  created_at: string
}

export interface ChunkItem {
  id: number
  chunk_index: number
  content: string
}

export interface FileDetail extends Omit<FileItem, 'created_at'> {
  created_at: string
  chunks: ChunkItem[]
}

// 【新增】异步处理状态；前端据此判断是否继续轮询。
export interface ProcessingStatus {
  document_id: number
  status: FileItem['status']
  chunk_count: number
}

export const getFiles = async () => (await request.get<FileItem[]>('/files')).data
export const getFileDetail = async (documentId: number) =>
  (await request.get<FileDetail>(`/files/${documentId}`)).data

// 保留旧同步上传接口，旧调用不会受影响。
export const uploadFile = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return (await request.post('/files/upload', formData)).data
}

// 【新增】调用后端 BackgroundTasks 异步入库接口。
export const uploadFileAsync = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return (await request.post<ProcessingStatus>('/files/upload-async', formData)).data
}

// 【新增】轮询单个文档状态。
export const getProcessingStatus = async (documentId: number) =>
  (await request.get<ProcessingStatus>(`/files/processing/${documentId}`)).data

// 【新增】仅对 failed 状态文档重试。
export const retryFile = async (documentId: number) =>
  (await request.post<ProcessingStatus>(`/files/${documentId}/retry`)).data

export const deleteFile = async (documentId: number) =>
  (await request.delete(`/files/${documentId}`)).data