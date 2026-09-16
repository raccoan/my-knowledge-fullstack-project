import request from './request'

export interface BasicInfo {
  name: string
  phone: string
  email: string
  location: string
}

export interface Education {
  school: string
  major: string
  degree: string
  start_date: string
  end_date: string
}

export interface Project {
  name: string
  description: string
  technologies: string[]
  responsibilities: string[]
  highlights: string[]
}

export interface Internship {
  company: string
  position: string
  start_date: string
  end_date: string
  responsibilities: string[]
  technologies: string[]
}

export interface StructuredResume {
  basic_info: BasicInfo
  education: Education[]
  skills: string[]
  projects: Project[]
  internships: Internship[]
  self_evaluation: string
}

export interface Resume {
  id: number
  filename: string
  file_path: string
  structured_data: StructuredResume | null
  created_at: string
  updated_at: string
}

export async function uploadResume(file: File) {
  const formData = new FormData()

  formData.append('file', file)

  const response = await request.post<{
    message: string
    resume: Resume
  }>('/resumes/upload', formData, {
    timeout: 120000,
  })

  return response.data
}

export async function getResumes() {
  const response = await request.get<Resume[]>(
    '/resumes',
  )

  return response.data
}