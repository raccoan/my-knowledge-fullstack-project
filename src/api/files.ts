import request from "./request";

export interface FileItem {
  id:number
  filename:string
  file_path?:string
  created_at?:string
}

// 获取用户文件列表
export async function getFiles(){
  const response = await request.get<FileItem[]>('/files')
  return response.data
}

// 上传文件

export async function uploadFile(file:File) {
  const formData = new FormData()
  formData.append('file',file)
  const response = await request.post('/files/upload',formData)
  return response.data
  
}

// 删除文件接口
export async function deleteFile(fileId:number){
  const response = await request.delete(`/files/${fileId}`)
  return response.data
}