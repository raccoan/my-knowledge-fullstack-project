import request from './request'

/**
 * =========================
 * 面试消息
 * =========================
 */
export interface InterviewMessage {
  id: number
  role: 'interviewer' | 'candidate'
  content: string
  score: number | null
  feedback: string | null
  reference_answer: string | null
  knowledge_gap: string[]
  created_at: string
}

/**
 * =========================
 * 面试详情
 * =========================
 */
export interface Interview {
  id: number
  resume_id: number
  status: 'ongoing' | 'finished'
  total_score: number
  current_question: string | null
  messages: InterviewMessage[]
}

/**
 * =========================
 * 创建面试返回
 * =========================
 */
export interface CreateInterviewResponse {
  id: number
  resume_id: number
  status: 'ongoing' | 'finished'
  question: string
}

/**
 * =========================
 * 提交回答返回
 * =========================
 */
export interface AnswerInterviewResponse {
  score: number
  feedback: string
  reference_answer: string
  knowledge_gap: string[]
  next_question: string
  finished: boolean
  report?: InterviewReport
}

/**
 * =========================
 * 面试报告
 * =========================
 */
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

/**
 * =========================
 * 面试列表项
 * =========================
 */
export interface InterviewListItem {
  id: number
  resume_id: number
  status: 'ongoing' | 'finished'
  total_score: number
  created_at: string
  updated_at: string
}

/**
 * =========================
 * 创建面试
 * =========================
 */
export async function createInterview(
  resumeId: number
) {
  const response =
    await request.post<CreateInterviewResponse>(
      '/interviews',
      {
        resume_id: resumeId
      },
      {
        timeout: 150000
      }
    )

  return response.data
}

/**
 * =========================
 * 提交面试回答
 * =========================
 */
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
        timeout: 120000
      }
    )

  return response.data
}

/**
 * =========================
 * 获取面试详情
 * =========================
 */
export async function getInterview(
  interviewId: number
) {
  const response =
    await request.get<Interview>(
      `/interviews/${interviewId}`
    )

  return response.data
}

/**
 * =========================
 * 获取所有面试记录
 * =========================
 */
export async function getInterviews() {
  const response =
    await request.get<InterviewListItem[]>(
      '/interviews'
    )

  return response.data
}

/**
 * =========================
 * 获取面试报告
 * =========================
 */
export async function getInterviewReport(
  interviewId: number
) {
  const response =
    await request.get<InterviewReport>(
      `/interviews/${interviewId}/report`
    )

  return response.data
}