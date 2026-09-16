import request from './request'

export interface InterviewMessage {
  id: number
  role: 'interviewer' | 'candidate'
  content: string
  score: number | null
  feedback: string | null
  created_at: string
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
  next_question: string
  finished: boolean
}

export async function createInterview(
  resumeId: number
) {
  const response = await request.post<CreateInterviewResponse>(
    '/interviews',
    {
      resume_id: resumeId,
    },
  )

  return response.data
}

export async function answerInterview(
  interviewId: number,
  answer: string,
) {
  const response = await request.post<AnswerInterviewResponse>(
    `/interviews/${interviewId}/answer`,
    {
      answer,
    },
  )

  return response.data
}

export async function getInterview(
  interviewId: number
) {
  const response = await request.get<Interview>(
    `/interviews/${interviewId}`,
  )

  return response.data
}