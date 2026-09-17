<template>
  <div class="interview-page">
    <!-- 顶部 -->
    <div class="page-header">
      <div class="header-left">
        <a-button type="text" @click="goBack">
          <template #icon>
            <ArrowLeftOutlined />
          </template>
          返回
        </a-button>

        <div class="header-title">
          <div class="title">AI 模拟面试</div>
          <div class="subtitle">
            基于你的真实简历进行针对性技术面试
          </div>
        </div>
      </div>

      <div class="header-right">
        <a-tag
          v-if="!finished"
          color="processing"
        >
          面试进行中
        </a-tag>

        <a-tag
          v-else
          color="success"
        >
          面试已结束
        </a-tag>
      </div>
    </div>

    <!-- 页面主体 -->
    <div class="page-content">
      <a-row :gutter="20">
        <!-- 左侧 -->
        <a-col :xs="24" :lg="7">
          <div class="left-column">

            <!-- 面试信息 -->
            <a-card
              title="面试信息"
              :bordered="false"
              class="info-card"
            >
              <div class="info-item">
                <span class="label">面试 ID</span>
                <span class="value">
                  {{ interviewId || '-' }}
                </span>
              </div>

              <div class="info-item">
                <span class="label">题目数量</span>
                <span class="value">
                  {{ questionCount }}
                </span>
              </div>

              <div class="info-item">
                <span class="label">当前状态</span>
                <span class="value">
                  <a-tag
                    v-if="!finished"
                    color="processing"
                  >
                    进行中
                  </a-tag>

                  <a-tag
                    v-else
                    color="success"
                  >
                    已完成
                  </a-tag>
                </span>
              </div>

              <div
                v-if="finished && report"
                class="info-score"
              >
                <div class="score-label">
                  综合得分
                </div>

                <div class="score-value">
                  {{ report.overall_score }}
                </div>

                <div class="score-unit">
                  / 100
                </div>
              </div>
            </a-card>

            <!-- 能力维度 -->
            <a-card
              v-if="finished && report"
              title="能力维度"
              :bordered="false"
              class="info-card"
            >
              <div class="ability-item">
                <div class="ability-header">
                  <span>项目能力</span>
                  <span>
                    {{ report.project_ability }}
                  </span>
                </div>

                <a-progress
                  :percent="report.project_ability"
                  :show-info="false"
                />
              </div>

              <div class="ability-item">
                <div class="ability-header">
                  <span>技术能力</span>
                  <span>
                    {{ report.technical_ability }}
                  </span>
                </div>

                <a-progress
                  :percent="report.technical_ability"
                  :show-info="false"
                />
              </div>

              <div class="ability-item">
                <div class="ability-header">
                  <span>实践能力</span>
                  <span>
                    {{ report.practical_ability }}
                  </span>
                </div>

                <a-progress
                  :percent="report.practical_ability"
                  :show-info="false"
                />
              </div>

              <div class="ability-item">
                <div class="ability-header">
                  <span>沟通表达</span>
                  <span>
                    {{ report.communication_ability }}
                  </span>
                </div>

                <a-progress
                  :percent="report.communication_ability"
                  :show-info="false"
                />
              </div>
            </a-card>

          </div>
        </a-col>

        <!-- 右侧 -->
        <a-col :xs="24" :lg="17">
          <div class="right-column">

            <!-- 面试记录 -->
            <a-card
              title="面试过程"
              :bordered="false"
              class="conversation-card"
            >
              <!-- 没有消息 -->
              <a-empty
                v-if="messages.length === 0"
                description="暂无面试记录"
              />

              <!-- 消息列表 -->
              <div
                v-else
                class="message-list"
              >
                <div
                  v-for="(message, index) in messages"
                  :key="message.id"
                  class="message-item"
                >

                  <!-- 面试官问题 -->
                  <div
                    v-if="message.role === 'interviewer'"
                    class="interviewer-message"
                  >
                    <div class="message-role">
                      <div class="avatar interviewer-avatar">
                        AI
                      </div>

                      <span>
                        AI 面试官 · 第 {{ getQuestionNumber(index) }} 题
                      </span>
                    </div>

                    <div class="question-content">
                      {{ message.content }}
                    </div>
                  </div>

                  <!-- 候选人回答 -->
                  <div
                    v-if="message.role === 'candidate'"
                    class="candidate-message"
                  >
                    <div class="message-role candidate-role">
                      <span>我的回答</span>

                      <div class="avatar candidate-avatar">
                        我
                      </div>
                    </div>

                    <div class="answer-content">
                      {{ message.content }}
                    </div>

                    <!-- 得分 -->
                    <div
                      v-if="message.score !== null"
                      class="result-section"
                    >
                      <div class="result-header">
                        <span class="result-title">
                          本题得分
                        </span>

                        <a-tag
                          :color="getScoreColor(message.score)"
                        >
                          {{ message.score }} 分
                        </a-tag>
                      </div>

                      <!-- AI反馈 -->
                      <div
                        v-if="message.feedback"
                        class="feedback-box"
                      >
                        <div class="feedback-title">
                          AI 反馈
                        </div>

                        <div class="feedback-content">
                          {{ message.feedback }}
                        </div>
                      </div>

                      <!-- 参考答案 -->
                      <div
                        v-if="message.reference_answer"
                        class="reference-box"
                      >
                        <div
                          class="reference-header"
                          @click="toggleReferenceAnswer(message.id)"
                        >
                          <span class="reference-title">
                            参考答案
                          </span>

                          <span class="reference-toggle">
                            {{
                              showReferenceAnswers[message.id]
                                ? '收起'
                                : '查看'
                            }}

                            <DownOutlined
                              :class="{
                                'rotate-icon':
                                  showReferenceAnswers[message.id]
                              }"
                            />
                          </span>
                        </div>

                        <div
                          v-if="showReferenceAnswers[message.id]"
                          class="reference-content"
                        >
                          {{ message.reference_answer }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 分隔线 -->
                  <a-divider
                    v-if="index < messages.length - 1"
                    class="message-divider"
                  />
                </div>
              </div>
            </a-card>

            <!-- 当前问题 -->
            <a-card
              v-if="!finished"
              title="回答当前问题"
              :bordered="false"
              class="answer-card"
            >
              <div
                v-if="question"
                class="current-question"
              >
                <div class="current-question-label">
                  当前问题
                </div>

                <div class="current-question-content">
                  {{ question }}
                </div>
              </div>

              <a-textarea
                v-model:value="answer"
                :rows="7"
                placeholder="请输入你的回答..."
                :disabled="submitting"
                show-count
                :maxlength="5000"
              />

              <div class="answer-footer">
                <span class="answer-tip">
                  尽量结合你的实际项目经历进行回答
                </span>

                <a-button
                  type="primary"
                  :loading="submitting"
                  :disabled="!answer.trim()"
                  @click="submitAnswer"
                >
                  提交回答
                  <template #icon>
                    <SendOutlined />
                  </template>
                </a-button>
              </div>
            </a-card>

            <!-- 面试结束 -->
            <a-card
              v-if="finished"
              title="面试报告"
              :bordered="false"
              class="report-card"
            >
              <!-- 没有报告 -->
              <a-empty
                v-if="!report"
                description="暂无面试报告"
              />

              <template v-else>
                <!-- 总分 -->
                <div class="report-score">
                  <a-statistic
                    title="综合得分"
                    :value="report.overall_score"
                    suffix="/ 100"
                  />
                </div>

                <a-divider />

                <!-- 优势 -->
                <div class="report-section">
                  <div class="report-section-title">
                    <CheckCircleOutlined />
                    优势
                  </div>

                  <div
                    v-if="report.strengths?.length"
                    class="report-tags"
                  >
                    <a-tag
                      v-for="item in report.strengths"
                      :key="item"
                      color="success"
                    >
                      {{ item }}
                    </a-tag>
                  </div>

                  <a-empty
                    v-else
                    :image="false"
                    description="暂无"
                  />
                </div>

                <!-- 不足 -->
                <div class="report-section">
                  <div class="report-section-title">
                    <ExclamationCircleOutlined />
                    不足
                  </div>

                  <div
                    v-if="report.weaknesses?.length"
                    class="report-tags"
                  >
                    <a-tag
                      v-for="item in report.weaknesses"
                      :key="item"
                      color="warning"
                    >
                      {{ item }}
                    </a-tag>
                  </div>

                  <a-empty
                    v-else
                    :image="false"
                    description="暂无"
                  />
                </div>

                <!-- 知识薄弱点 -->
                <div class="report-section">
                  <div class="report-section-title">
                    <BookOutlined />
                    知识薄弱点
                  </div>

                  <div
                    v-if="report.knowledge_gaps?.length"
                    class="report-tags"
                  >
                    <a-tag
                      v-for="item in report.knowledge_gaps"
                      :key="item"
                    >
                      {{ item }}
                    </a-tag>
                  </div>

                  <a-empty
                    v-else
                    :image="false"
                    description="暂无"
                  />
                </div>

                <!-- 建议 -->
                <div class="report-section">
                  <div class="report-section-title">
                    <BulbOutlined />
                    学习建议
                  </div>

                  <ul
                    v-if="report.suggestions?.length"
                    class="suggestion-list"
                  >
                    <li
                      v-for="item in report.suggestions"
                      :key="item"
                    >
                      {{ item }}
                    </li>
                  </ul>

                  <a-empty
                    v-else
                    :image="false"
                    description="暂无"
                  />
                </div>

                <div class="report-actions">
                  <a-button
                    type="primary"
                    @click="goResume"
                  >
                    返回简历
                  </a-button>

                  <a-button
                    @click="goBack"
                  >
                    返回首页
                  </a-button>
                </div>
              </template>
            </a-card>

          </div>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ref,
  computed,
  onMounted
} from 'vue'

import {
  useRoute,
  useRouter
} from 'vue-router'

import {
  ArrowLeftOutlined,
  SendOutlined,
  DownOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  BookOutlined,
  BulbOutlined
} from '@ant-design/icons-vue'

import {
  message as antMessage
} from 'ant-design-vue'

import {
  createInterview,
  answerInterview,
  getInterview,
  getInterviewReport
} from '@/api/interviews'

import type {
  InterviewMessage,
  InterviewReport
} from '@/api/interviews'

const route = useRoute()
const router = useRouter()

/**
 * 当前面试 ID
 */
const interviewId = ref<number | null>(null)

/**
 * 当前问题
 */
const question = ref('')

/**
 * 用户回答
 */
const answer = ref('')

/**
 * 面试消息
 */
const messages = ref<InterviewMessage[]>([])

/**
 * 是否正在提交
 */
const submitting = ref(false)

/**
 * 是否结束
 */
const finished = ref(false)

/**
 * 面试报告
 */
const report = ref<InterviewReport | null>(null)

/**
 * 每一道题的参考答案是否展开
 *
 * key = candidate message id
 */
const showReferenceAnswers = ref<Record<number, boolean>>({})

/**
 * 题目数量
 */
const questionCount = computed(() => {
  return messages.value.filter(
    item => item.role === 'interviewer'
  ).length
})

/**
 * 返回
 */
const goBack = () => {
  router.push('/chat')
}

/**
 * 返回简历
 */
const goResume = () => {
  router.push('/resume')
}

/**
 * 获取当前问题是第几题
 *
 * 因为 messages 中同时存在：
 * interviewer
 * candidate
 *
 * 所以需要统计当前 index 前面出现了几个 interviewer
 */
const getQuestionNumber = (index: number) => {
  return messages.value
    .slice(0, index + 1)
    .filter(
      item => item.role === 'interviewer'
    ).length
}

/**
 * 切换参考答案
 */
const toggleReferenceAnswer = (
  messageId: number
) => {
  showReferenceAnswers.value[messageId] =
    !showReferenceAnswers.value[messageId]
}

/**
 * 根据分数获取 Tag 颜色
 */
const getScoreColor = (score: number) => {
  if (score >= 90) {
    return 'success'
  }

  if (score >= 80) {
    return 'processing'
  }

  if (score >= 60) {
    return 'warning'
  }

  return 'error'
}

/**
 * 开始新的面试
 */
const startInterview = async () => {
  const resumeId = Number(
    route.query.resumeId
  )

  if (!resumeId) {
    antMessage.error(
      '缺少简历 ID'
    )
    return
  }

  try {
    submitting.value = true

    const data = await createInterview(
      resumeId
    )

    interviewId.value = data.id

    question.value = data.question

    finished.value = false

    answer.value = ''

    messages.value = [
      {
        id: Date.now(),
        role: 'interviewer',
        content: data.question,
        score: null,
        feedback: null,
        reference_answer: null,
        created_at: new Date().toISOString()
      }
    ]

    /**
     * 创建成功以后把 URL 改成：
     *
     * /interview?id=xxx
     *
     * 后面刷新页面就可以直接加载当前面试
     */
    router.replace({
      path: '/interview',
      query: {
        id: String(data.id)
      }
    })

  } catch (error) {
    console.error(
      '创建面试失败:',
      error
    )

    antMessage.error(
      '创建面试失败'
    )
  } finally {
    submitting.value = false
  }
}

/**
 * 加载历史面试
 */
const loadInterview = async (
  id: number
) => {
  try {
    submitting.value = true

    const data = await getInterview(id)

    interviewId.value = data.id

    messages.value = data.messages || []

    question.value =
      data.current_question || ''

    finished.value =
      data.status === 'finished'

    /**
     * 如果已经结束，继续加载报告
     */
    if (finished.value) {
      try {
        const reportData =
          await getInterviewReport(id)

        report.value =
          reportData.report
      } catch (error) {
        console.error(
          '加载面试报告失败:',
          error
        )
      }
    }

  } catch (error) {
    console.error(
      '加载面试失败:',
      error
    )

    antMessage.error(
      '加载面试记录失败'
    )
  } finally {
    submitting.value = false
  }
}

/**
 * 提交回答
 */
const submitAnswer = async () => {
  if (!interviewId.value) {
    antMessage.error(
      '当前面试不存在'
    )
    return
  }

  if (!answer.value.trim()) {
    antMessage.warning(
      '请输入回答内容'
    )
    return
  }

  try {
    submitting.value = true

    const currentAnswer =
      answer.value.trim()

    /**
     * 调用后端
     */
    const data =
      await answerInterview(
        interviewId.value,
        currentAnswer
      )

    /**
     * 先把用户回答添加到页面
     */
    messages.value.push({
      id: Date.now(),
      role: 'candidate',
      content: currentAnswer,
      score: data.score,
      feedback: data.feedback,
      reference_answer:
        data.reference_answer,
      created_at:
        new Date().toISOString()
    })

    /**
     * 清空输入框
     */
    answer.value = ''

    /**
     * 面试结束
     */
    if (data.finished) {
      finished.value = true

      /**
       * 后端返回了报告就直接使用
       */
      if (data.report) {
        report.value =
          data.report
      } else {
        /**
         * 如果没有直接返回报告，
         * 再请求一次
         */
        try {
          const reportData =
            await getInterviewReport(
              interviewId.value
            )

          report.value =
            reportData.report
        } catch (error) {
          console.error(
            '获取面试报告失败:',
            error
          )
        }
      }

      question.value = ''

      antMessage.success(
        '本次面试已完成'
      )

      return
    }

    /**
     * 没结束
     *
     * 后端会返回下一道题
     */
    if (data.next_question) {
      question.value =
        data.next_question

      messages.value.push({
        id: Date.now() + 1,
        role: 'interviewer',
        content:
          data.next_question,
        score: null,
        feedback: null,
        reference_answer: null,
        created_at:
          new Date().toISOString()
      })
    }

  } catch (error) {
    console.error(
      '提交回答失败:',
      error
    )

    antMessage.error(
      '提交回答失败，请稍后重试'
    )
  } finally {
    submitting.value = false
  }
}

/**
 * 页面初始化
 *
 * 两种情况：
 *
 * 1.
 * /interview?resumeId=1
 *
 * 开始新的面试
 *
 * 2.
 * /interview?id=12
 *
 * 加载历史面试
 */
onMounted(async () => {
  const id = Number(
    route.query.id
  )

  const resumeId = Number(
    route.query.resumeId
  )

  if (id) {
    await loadInterview(id)
    return
  }

  if (resumeId) {
    await startInterview()
    return
  }

  antMessage.error(
    '缺少面试参数'
  )
})
</script>

<style scoped>
.interview-page {
  min-height: 100%;
  background: #f5f7fa;
}

/* =========================
   Header
========================= */

.page-header {
  height: 72px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid #f0f0f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #1f1f1f;
}

.subtitle {
  font-size: 13px;
  color: #8c8c8c;
}

/* =========================
   Content
========================= */

.page-content {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* =========================
   Info Card
========================= */

.info-card {
  border-radius: 10px;
}

.info-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 38px;
  border-bottom: 1px solid #f5f5f5;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: #8c8c8c;
  font-size: 14px;
}

.info-item .value {
  color: #262626;
  font-size: 14px;
  font-weight: 500;
}

.info-score {
  margin-top: 24px;
  padding: 20px;
  text-align: center;
  background: #fafafa;
  border-radius: 8px;
}

.score-label {
  font-size: 14px;
  color: #8c8c8c;
}

.score-value {
  margin-top: 5px;
  font-size: 38px;
  line-height: 1.2;
  font-weight: 700;
}

.score-unit {
  color: #8c8c8c;
  font-size: 13px;
}

/* =========================
   Ability
========================= */

.ability-item {
  margin-bottom: 18px;
}

.ability-item:last-child {
  margin-bottom: 0;
}

.ability-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
}

/* =========================
   Conversation
========================= */

.conversation-card {
  border-radius: 10px;
}

.message-list {
  display: flex;
  flex-direction: column;
}

.message-item {
  width: 100%;
}

.message-role {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #595959;
  font-size: 13px;
  font-weight: 500;
}

.candidate-role {
  justify-content: flex-end;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;

  display: flex;
  align-items: center;
  justify-content: center;

  font-size: 12px;
  font-weight: 600;
}

.interviewer-avatar {
  background: #e6f4ff;
  color: #1677ff;
}

.candidate-avatar {
  background: #f6ffed;
  color: #389e0d;
}

/* =========================
   Question
========================= */

.interviewer-message {
  max-width: 90%;
}

.question-content {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  color: #262626;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* =========================
   Candidate
========================= */

.candidate-message {
  margin-top: 20px;
  margin-left: auto;
  max-width: 90%;
}

.answer-content {
  padding: 16px;
  background: #e6f4ff;
  border-radius: 8px;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* =========================
   Result
========================= */

.result-section {
  margin-top: 16px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.result-title {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.feedback-box {
  margin-bottom: 12px;
  padding: 14px 16px;
  background: #fafafa;
  border-left: 3px solid #1677ff;
  border-radius: 4px;
}

.feedback-title {
  margin-bottom: 7px;
  font-size: 13px;
  font-weight: 600;
  color: #262626;
}

.feedback-content {
  color: #595959;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* =========================
   Reference Answer
========================= */

.reference-box {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  overflow: hidden;
}

.reference-header {
  padding: 12px 14px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  cursor: pointer;
  background: #fafafa;

  transition: all 0.2s;
}

.reference-header:hover {
  background: #f5f5f5;
}

.reference-title {
  font-size: 13px;
  font-weight: 600;
  color: #262626;
}

.reference-toggle {
  display: flex;
  align-items: center;
  gap: 5px;

  color: #1677ff;
  font-size: 12px;
}

.reference-content {
  padding: 14px;

  color: #595959;
  font-size: 13px;
  line-height: 1.8;

  white-space: pre-wrap;

  border-top: 1px solid #f0f0f0;
}

.rotate-icon {
  transform: rotate(180deg);
}

/* =========================
   Divider
========================= */

.message-divider {
  margin: 24px 0;
}

/* =========================
   Current Answer
========================= */

.answer-card {
  border-radius: 10px;
}

.current-question {
  margin-bottom: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.current-question-label {
  margin-bottom: 8px;
  color: #8c8c8c;
  font-size: 13px;
}

.current-question-content {
  color: #262626;
  font-size: 15px;
  line-height: 1.8;
  font-weight: 500;
  white-space: pre-wrap;
}

.answer-footer {
  margin-top: 12px;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.answer-tip {
  color: #8c8c8c;
  font-size: 12px;
}

/* =========================
   Report
========================= */

.report-card {
  border-radius: 10px;
}

.report-score {
  padding: 20px 0;
  text-align: center;
}

.report-section {
  margin-bottom: 26px;
}

.report-section:last-child {
  margin-bottom: 0;
}

.report-section-title {
  display: flex;
  align-items: center;
  gap: 8px;

  margin-bottom: 12px;

  font-size: 15px;
  font-weight: 600;
  color: #262626;
}

.report-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-list {
  margin: 0;
  padding-left: 20px;
  color: #595959;
  line-height: 2;
}

.report-actions {
  margin-top: 30px;

  display: flex;
  justify-content: center;
  gap: 12px;
}

/* =========================
   Responsive
========================= */

@media (max-width: 992px) {
  .page-content {
    padding: 16px;
  }

  .left-column {
    margin-bottom: 20px;
  }
}

@media (max-width: 768px) {
  .page-header {
    height: auto;
    min-height: 64px;
    padding: 12px 16px;
  }

  .header-left {
    min-width: 0;
  }

  .header-title {
    min-width: 0;
  }

  .title {
    font-size: 16px;
  }

  .subtitle {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .page-content {
    padding: 12px;
  }

  .interviewer-message,
  .candidate-message {
    max-width: 100%;
  }

  .answer-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .answer-footer .ant-btn {
    width: 100%;
  }

  .report-actions {
    flex-direction: column;
  }

  .report-actions .ant-btn {
    width: 100%;
  }
}
</style>