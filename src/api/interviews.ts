import request from './request'

export interface InterviewMessage {
  id: number
  role: 'interviewer' | 'candidate'
  content: string
  score: number | null
  feedback: string | null
  reference_answer: string | null
  created_at: string
  knowledge_gap: string[]
}

export interface Interview {
  id: number
  resume_id: number
  status: 'ongoing' | 'finished'
  total_score: number
  current_question: string | null
  messages: InterviewMessage[]
}

export interface CreateInterviewResponse {
  id: number
  resume_id: number
  status: string
  question: string
}

export interface AnswerInterviewResponse {
  score: number
  feedback: string
  reference_answer: string
  knowledge_gap: string[]
  next_question: string
  finished: boolean
  report?: InterviewReport
}

export interface InterviewReport {
  overall_score: number
  project_ability: number
  technical_ability: number
  practical_ability: number
  communication_ability: number
  strengths: string[]
  weaknesses: string[]
  knowledge_gaps: string[]
  suggestions: string[]
}

export interface InterviewListItem {
  id: number
  resume_id: number
  status: 'ongoing' | 'finished'
  total_score: number
  created_at: string
  updated_at: string
}




export async function createInterview(
  resumeId: number
) {
  const response = await request.post<CreateInterviewResponse>(
    '/interviews',
    {
      resume_id: resumeId
    },
    {
      timeout: 150000,
    }
    
  )

  return response.data
}

export async function answerInterview(
  interviewId: number,
  answer: string
) {
  const response =
    await request.post<AnswerInterviewResponse>(
      `/interviews/${interviewId}/answer`,
      {
        answer
      },
      {
        timeout: 120000,
      }
    )

  return response.data
}

export async function getInterview(
  interviewId: number
) {
  const response =
    await request.get<Interview>(
      `/interviews/${interviewId}`
    )

  return response.data
}

export async function getInterviewReport(
  interviewId: number
) {
  const response =
    await request.get<{
      interview_id: number
      total_score: number
      report: InterviewReport
    }>(
      `/interviews/${interviewId}/report`
    )

  return response.data
}

export async function getInterviews() {
  const response = await request.get<InterviewListItem[]>(
    '/interviews'
  )

  return response.data
}



