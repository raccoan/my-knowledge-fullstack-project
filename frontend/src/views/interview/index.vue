<script setup lang="ts">
import {
  computed,
  onMounted,
  ref
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
  getInterviewReport,

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
 * 是否提交中
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
 * 报告加载状态
 */
const reportLoading = ref(false)

/**
 * 每道题参考答案是否展开
 */
const showReferenceAnswers =
  ref<Record<number, boolean>>({})

/**
 * 面试题数量
 */
const questionCount = computed(() => {
  return messages.value.filter(
    item => item.role === 'interviewer'
  ).length
})

/**
 * 返回首页
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
 * 获取题目编号
 */
const getQuestionNumber = (
  index: number
) => {
  return messages.value
    .slice(0, index + 1)
    .filter(
      item => item.role === 'interviewer'
    )
    .length
}

/**
 * 切换参考答案
 */
const toggleReferenceAnswer = (
  messageId: number
) => {
  showReferenceAnswers.value[
    messageId
  ] =
    !showReferenceAnswers.value[
      messageId
    ]
}

/**
 * 根据分数返回颜色
 */
const getScoreColor = (
  score: number
) => {
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
 * 加载面试详情
 */
const loadInterview = async (
  id: number
) => {
  try {
    submitting.value = true

    const data = await getInterview(id)

    interviewId.value = data.id

    messages.value =
      data.messages || []

    finished.value =
      data.status === 'finished'

    /**
     * 当前问题
     *
     * 已结束的面试没有当前问题
     */
    question.value =
      data.current_question || ''

    /**
     * 如果面试已经结束，
     * 从后端加载报告
     */
    if (finished.value) {
      await loadInterviewReport()
    }
  } catch (error) {
    console.error(
      '加载面试失败:',
      error
    )

    antMessage.error(
      '加载面试失败'
    )
  } finally {
    submitting.value = false
  }
}

/**
 * 加载面试报告
 */
const loadInterviewReport = async () => {
  if (!interviewId.value) {
    return
  }

  reportLoading.value = true

  try {
    const data =
      await getInterviewReport(
        interviewId.value
      )

    /**
     * 后端当前接口直接返回 report JSON
     *
     * 为了兼容之前可能存在的：
     * { report: {...} }
     *
     * 这里同时处理两种情况。
     */
    report.value =
      (data as any)?.report ||
      data
  } catch (error) {
    console.error(
      '获取面试报告失败:',
      error
    )

    antMessage.error(
      '获取面试报告失败'
    )
  } finally {
    reportLoading.value = false
  }
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

    const data =
      await createInterview(
        resumeId
      )

    interviewId.value = data.id

    /**
     * 创建成功以后，
     * URL 变成：
     *
     * /interview?id=xxx
     */
    await router.replace({
      path: '/interview',
      query: {
        id: String(data.id)
      }
    })

    /**
     * 直接重新从数据库读取，
     * 不再手动制造临时消息。
     */
    await loadInterview(data.id)

    antMessage.success(
      '面试开始'
    )
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
 * 提交回答
 */
const submitAnswer = async () => {

  if (!interviewId.value) {
    antMessage.error(
      '当前面试不存在'
    )

    return
  }


  const currentAnswer =
    answer.value.trim()


  if (!currentAnswer) {
    antMessage.warning(
      '请输入回答内容'
    )

    return
  }


  try {

    submitting.value = true


    const data =
      await answerInterview(
        interviewId.value,
        currentAnswer
      )


    answer.value = ''


    await loadInterview(
      interviewId.value
    )


    if (data.finished) {

      finished.value = true

      question.value = ''

      await loadInterviewReport()

      antMessage.success(
        '本次面试已完成'
      )

      return

    }


  } catch(error){

    console.error(
      '提交回答失败:',
      error
    )


    antMessage.error(
      '提交回答失败，请稍后重试'
    )

  } finally {

    submitting.value=false

  }

}

/**
 * 页面初始化
 *
 * 两种情况：
 *
 * 1. /interview?resumeId=1
 *    开始新面试
 *
 * 2. /interview?id=12
 *    加载历史面试
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
                <span class="label">
                  面试 ID
                </span>

                <span class="value">
                  {{ interviewId || '-' }}
                </span>
              </div>

              <div class="info-item">
                <span class="label">
                  题目数量
                </span>

                <span class="value">
                  {{ questionCount }}
                </span>
              </div>

              <div class="info-item">
                <span class="label">
                  当前状态
                </span>

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

              <!-- 综合得分 -->
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

            <!-- 面试过程 -->
            <a-card
              title="面试过程"
              :bordered="false"
              class="conversation-card"
            >
              <a-empty
                v-if="messages.length === 0"
                description="暂无面试记录"
              />

              <div
                v-else
                class="message-list"
              >
                <div
                  v-for="(item, index) in messages"
                  :key="item.id"
                  class="message-item"
                >

                  <!-- 面试官 -->
                  <div
                    v-if="item.role === 'interviewer'"
                    class="interviewer-message"
                  >
                    <div class="message-role">
                      <div
                        class="avatar interviewer-avatar"
                      >
                        AI
                      </div>

                      <span>
                        AI 面试官 · 第
                        {{ getQuestionNumber(index) }}
                        题
                      </span>
                    </div>

                    <div class="question-content">
                      {{ item.content }}
                    </div>
                  </div>

                  <!-- 候选人 -->
                  <div
                    v-else-if="item.role === 'candidate'"
                    class="candidate-message"
                  >
                    <div
                      class="message-role candidate-role"
                    >
                      <span>
                        我的回答
                      </span>

                      <div
                        class="avatar candidate-avatar"
                      >
                        我
                      </div>
                    </div>

                    <div class="answer-content">
                      {{ item.content }}
                    </div>

                    <!-- 评分结果 -->
                    <div
                      v-if="item.score !== null"
                      class="result-section"
                    >
                      <div class="result-header">
                        <span class="result-title">
                          本题得分
                        </span>

                        <a-tag
                          :color="
                            getScoreColor(item.score)
                          "
                        >
                          {{ item.score }} 分
                        </a-tag>
                      </div>

                      <!-- AI反馈 -->
                      <div
                        v-if="item.feedback"
                        class="feedback-box"
                      >
                        <div class="feedback-title">
                          AI 反馈
                        </div>

                        <div class="feedback-content">
                          {{ item.feedback }}
                        </div>
                      </div>

                      <!-- 薄弱知识点 -->
                      <div
                        v-if="
                          item.knowledge_gap &&
                          item.knowledge_gap.length
                        "
                        class="knowledge-gap"
                      >
                        <div class="feedback-title">
                          薄弱知识点
                        </div>

                        <div class="knowledge-gap-list">
                          <a-tag
                            v-for="
                              gap in item.knowledge_gap
                            "
                            :key="gap"
                            color="orange"
                          >
                            {{ gap }}
                          </a-tag>
                        </div>
                      </div>

                      <!-- 参考答案 -->
                      <div
                        v-if="item.reference_answer"
                        class="reference-box"
                      >
                        <div
                          class="reference-header"
                          @click="
                            toggleReferenceAnswer(
                              item.id
                            )
                          "
                        >
                          <span class="reference-title">
                            参考答案
                          </span>

                          <span class="reference-toggle">
                            {{
                              showReferenceAnswers[
                                item.id
                              ]
                                ? '收起'
                                : '查看'
                            }}

                            <DownOutlined
                              :class="{
                                'rotate-icon':
                                  showReferenceAnswers[
                                    item.id
                                  ]
                              }"
                            />
                          </span>
                        </div>

                        <div
                          v-if="
                            showReferenceAnswers[
                              item.id
                            ]
                          "
                          class="reference-content"
                        >
                          {{
                            item.reference_answer
                          }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <a-divider
                    v-if="
                      index <
                      messages.length - 1
                    "
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

            <!-- 面试报告 -->
            <a-card
              v-if="finished"
              title="面试报告"
              :bordered="false"
              class="report-card"
            >
              <!-- 报告加载中 -->
              <a-spin
                v-if="reportLoading"
                class="report-loading"
              />

              <!-- 没有报告 -->
              <a-empty
                v-else-if="!report"
                description="暂无面试报告"
              />

              <!-- 报告 -->
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

                <!-- 能力维度 -->
                <div class="report-section">
                  <div class="report-section-title">
                    能力分析
                  </div>

                  <div class="report-ability-list">
                    <div class="report-ability-item">
                      <div class="report-ability-header">
                        <span>
                          项目能力
                        </span>

                        <span>
                          {{ report.project_ability }}
                        </span>
                      </div>

                      <a-progress
                        :percent="
                          report.project_ability
                        "
                        :show-info="false"
                      />
                    </div>

                    <div class="report-ability-item">
                      <div class="report-ability-header">
                        <span>
                          技术能力
                        </span>

                        <span>
                          {{ report.technical_ability }}
                        </span>
                      </div>

                      <a-progress
                        :percent="
                          report.technical_ability
                        "
                        :show-info="false"
                      />
                    </div>

                    <div class="report-ability-item">
                      <div class="report-ability-header">
                        <span>
                          实践能力
                        </span>

                        <span>
                          {{ report.practical_ability }}
                        </span>
                      </div>

                      <a-progress
                        :percent="
                          report.practical_ability
                        "
                        :show-info="false"
                      />
                    </div>

                    <div class="report-ability-item">
                      <div class="report-ability-header">
                        <span>
                          沟通表达
                        </span>

                        <span>
                          {{
                            report.communication_ability
                          }}
                        </span>
                      </div>

                      <a-progress
                        :percent="
                          report.communication_ability
                        "
                        :show-info="false"
                      />
                    </div>
                  </div>
                </div>

                <!-- 优势 -->
                <div class="report-section">
                  <div class="report-section-title">
                    <CheckCircleOutlined />

                    优势
                  </div>

                  <div
                    v-if="
                      report.strengths?.length
                    "
                    class="report-tags"
                  >
                    <a-tag
                      v-for="
                        item in report.strengths
                      "
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
                    v-if="
                      report.weaknesses?.length
                    "
                    class="report-tags"
                  >
                    <a-tag
                      v-for="
                        item in report.weaknesses
                      "
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
                    v-if="
                      report.knowledge_gaps?.length
                    "
                    class="report-tags"
                  >
                    <a-tag
                      v-for="
                        item in report.knowledge_gaps
                      "
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
                    v-if="
                      report.suggestions?.length
                    "
                    class="suggestion-list"
                  >
                    <li
                      v-for="
                        item in report.suggestions
                      "
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

                <!-- 操作 -->
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

```css
<style scoped>
.interview-page {
  min-height: 100%;
  background: #f7f8fa;
  color: #1f2329;
}

/* =========================
   Header
========================= */

.page-header {
  position: sticky;
  top: 0;
  z-index: 10;

  height: 64px;
  padding: 0 28px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  background: #ffffff;
  border-bottom: 1px solid #e8eaed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.header-left :deep(.ant-btn) {
  color: #667085;
  border-radius: 7px;
}

.header-left :deep(.ant-btn:hover) {
  color: #1677ff;
  background: #f2f7ff;
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.title {
  color: #1f2329;
  font-size: 16px;
  font-weight: 600;
  line-height: 22px;
}

.subtitle {
  overflow: hidden;

  color: #86909c;
  font-size: 12px;
  line-height: 18px;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-right :deep(.ant-tag) {
  margin: 0;
  border-radius: 12px;
  font-size: 12px;
}

/* =========================
   Content
========================= */

.page-content {
  width: min(1400px, 100%);
  margin: 0 auto;
  padding: 24px;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* =========================
   Common Card
========================= */

.info-card,
.conversation-card,
.answer-card,
.report-card {
  overflow: hidden;

  border: 1px solid #edf0f3 !important;
  border-radius: 12px !important;

  background: #ffffff;

  box-shadow: 0 2px 8px rgb(31 35 41 / 3%);
}

.info-card :deep(.ant-card-head),
.conversation-card :deep(.ant-card-head),
.answer-card :deep(.ant-card-head),
.report-card :deep(.ant-card-head) {
  min-height: 52px;
  padding: 0 18px;

  border-bottom: 1px solid #f0f1f3;
}

.info-card :deep(.ant-card-head-title),
.conversation-card :deep(.ant-card-head-title),
.answer-card :deep(.ant-card-head-title),
.report-card :deep(.ant-card-head-title) {
  color: #1f2329;
  font-size: 14px;
  font-weight: 600;
}

.info-card :deep(.ant-card-body),
.conversation-card :deep(.ant-card-body),
.answer-card :deep(.ant-card-body),
.report-card :deep(.ant-card-body) {
  padding: 18px;
}

/* =========================
   Info Card
========================= */

.info-item {
  min-height: 38px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  border-bottom: 1px solid #f5f6f7;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: #86909c;
  font-size: 13px;
}

.info-item .value {
  max-width: 60%;

  overflow: hidden;

  color: #1f2329;
  font-size: 13px;
  font-weight: 500;

  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.info-item .value :deep(.ant-tag) {
  margin: 0;
  border-radius: 10px;
  font-size: 11px;
}

/* =========================
   Score
========================= */

.info-score {
  margin-top: 18px;
  padding: 18px;

  text-align: center;

  background: linear-gradient(
    135deg,
    #f7faff,
    #f3f6ff
  );

  border: 1px solid #e8efff;
  border-radius: 10px;
}

.score-label {
  color: #86909c;
  font-size: 12px;
}

.score-value {
  margin-top: 4px;

  color: #1677ff;
  font-size: 38px;
  line-height: 1.2;
  font-weight: 700;
}

.score-unit {
  margin-top: 2px;

  color: #a9aeb8;
  font-size: 12px;
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

  margin-bottom: 7px;

  color: #4e5969;
  font-size: 12px;
}

.ability-header > span:last-child {
  color: #1f2329;
  font-weight: 600;
}

.ability-item :deep(.ant-progress) {
  margin: 0;
}

.ability-item :deep(.ant-progress-bg) {
  border-radius: 6px;
}

.ability-item :deep(.ant-progress-inner) {
  background: #f2f3f5;
}

/* =========================
   Conversation
========================= */

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

  margin-bottom: 8px;

  color: #667085;
  font-size: 12px;
  font-weight: 500;
}

.candidate-role {
  justify-content: flex-end;
}

.avatar {
  width: 30px;
  height: 30px;

  display: flex;
  align-items: center;
  justify-content: center;

  flex-shrink: 0;

  border-radius: 50%;

  font-size: 11px;
  font-weight: 600;
}

.interviewer-avatar {
  color: #1677ff;
  background: #e8f3ff;
  box-shadow: 0 2px 6px rgb(22 119 255 / 10%);
}

.candidate-avatar {
  color: #389e0d;
  background: #f0f9eb;
}

/* =========================
   Interviewer Question
========================= */

.interviewer-message {
  max-width: 90%;
}

.question-content {
  padding: 14px 16px;

  color: #1f2329;
  font-size: 13px;
  line-height: 1.8;

  white-space: pre-wrap;

  background: #f7f8fa;
  border: 1px solid #edf0f3;
  border-radius: 10px;
}

/* =========================
   Candidate Answer
========================= */

.candidate-message {
  max-width: 90%;
  margin-top: 18px;
  margin-left: auto;
}

.answer-content {
  padding: 14px 16px;

  color: #1f2329;
  font-size: 13px;
  line-height: 1.8;

  white-space: pre-wrap;

  background: #e8f3ff;
  border: 1px solid #d9eaff;
  border-radius: 10px;
}

/* =========================
   Result
========================= */

.result-section {
  margin-top: 14px;
  padding: 14px;

  background: #fafbfc;
  border: 1px solid #edf0f3;
  border-radius: 10px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-bottom: 12px;
}

.result-title {
  color: #1f2329;
  font-size: 13px;
  font-weight: 600;
}

.result-header :deep(.ant-tag) {
  margin: 0;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

/* =========================
   Feedback
========================= */

.feedback-box {
  margin-bottom: 12px;
  padding: 12px 14px;

  background: #ffffff;
  border-left: 3px solid #1677ff;
  border-radius: 0 8px 8px 0;
}

.feedback-title {
  margin-bottom: 6px;

  color: #4e5969;
  font-size: 12px;
  font-weight: 600;
}

.feedback-content {
  color: #667085;
  font-size: 12px;
  line-height: 1.75;

  white-space: pre-wrap;
}

/* =========================
   Knowledge Gap
========================= */

.knowledge-gap {
  margin-top: 12px;
}

.knowledge-gap-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;

  margin-top: 7px;
}

.knowledge-gap-list :deep(.ant-tag) {
  margin: 0;
  border-radius: 6px;
  font-size: 11px;
}

/* =========================
   Reference Answer
========================= */

.reference-box {
  overflow: hidden;

  margin-top: 12px;

  border: 1px solid #e8eaed;
  border-radius: 8px;

  background: #ffffff;
}

.reference-header {
  min-height: 40px;
  padding: 9px 12px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  cursor: pointer;

  background: #f7f8fa;

  transition:
    background-color 0.18s ease,
    color 0.18s ease;
}

.reference-header:hover {
  background: #f2f5f9;
}

.reference-title {
  color: #4e5969;
  font-size: 12px;
  font-weight: 600;
}

.reference-toggle {
  display: flex;
  align-items: center;
  gap: 5px;

  color: #1677ff;
  font-size: 11px;
}

.reference-toggle :deep(.anticon) {
  transition: transform 0.2s ease;
}

.reference-content {
  padding: 12px 14px;

  color: #667085;
  font-size: 12px;
  line-height: 1.8;

  white-space: pre-wrap;

  border-top: 1px solid #edf0f3;
}

.rotate-icon {
  transform: rotate(180deg);
}

/* =========================
   Divider
========================= */

.message-divider {
  margin: 22px 0;
  border-color: #f0f1f3;
}

/* =========================
   Current Answer
========================= */

.current-question {
  margin-bottom: 16px;
  padding: 14px 16px;

  background: #f7faff;
  border: 1px solid #e4efff;
  border-radius: 10px;
}

.current-question-label {
  margin-bottom: 6px;

  color: #86909c;
  font-size: 11px;
}

.current-question-content {
  color: #1f2329;
  font-size: 14px;
  line-height: 1.8;
  font-weight: 500;

  white-space: pre-wrap;
}

.answer-card :deep(.ant-input) {
  padding: 10px 12px;

  color: #1f2329;
  font-size: 13px;
  line-height: 1.8;

  border-color: #d9dce1;
  border-radius: 9px;
  resize: vertical;

  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.answer-card :deep(.ant-input:hover) {
  border-color: #b8c7dc;
}

.answer-card :deep(.ant-input:focus) {
  border-color: #91bfff;
  box-shadow: 0 0 0 3px rgb(22 119 255 / 7%);
}

.answer-footer {
  margin-top: 12px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  gap: 12px;
}

.answer-tip {
  color: #a9aeb8;
  font-size: 11px;
}

.answer-footer :deep(.ant-btn) {
  min-width: 100px;
  height: 34px;

  border-radius: 7px;

  box-shadow: 0 2px 6px rgb(22 119 255 / 12%);
}

/* =========================
   Report
========================= */

.report-loading {
  display: block;
  padding: 40px;
  text-align: center;
}

.report-score {
  padding: 18px 0;

  text-align: center;
}

.report-score :deep(.ant-statistic-title) {
  margin-bottom: 5px;

  color: #86909c;
  font-size: 12px;
}

.report-score :deep(.ant-statistic-content) {
  color: #1677ff;
  font-size: 40px;
  font-weight: 700;
}

.report-score :deep(.ant-statistic-content-suffix) {
  color: #a9aeb8;
  font-size: 14px;
  font-weight: 400;
}

.report-card :deep(.ant-divider) {
  margin: 18px 0;
  border-color: #f0f1f3;
}

.report-section {
  margin-bottom: 24px;
}

.report-section:last-child {
  margin-bottom: 0;
}

.report-section-title {
  display: flex;
  align-items: center;
  gap: 7px;

  margin-bottom: 12px;

  color: #1f2329;
  font-size: 14px;
  font-weight: 600;
}

.report-section-title :deep(.anticon) {
  color: #1677ff;
  font-size: 15px;
}

.report-ability-list {
  display: flex;
  flex-direction: column;
  gap: 17px;

  padding: 14px 16px;

  background: #fafbfc;
  border: 1px solid #edf0f3;
  border-radius: 10px;
}

.report-ability-item {
  width: 100%;
}

.report-ability-header {
  margin-bottom: 6px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  color: #4e5969;
  font-size: 12px;
}

.report-ability-header > span:last-child {
  color: #1f2329;
  font-weight: 600;
}

.report-ability-item :deep(.ant-progress) {
  margin: 0;
}

.report-ability-item :deep(.ant-progress-inner) {
  background: #f2f3f5;
}

.report-ability-item :deep(.ant-progress-bg) {
  border-radius: 6px;
}

.report-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.report-tags :deep(.ant-tag) {
  margin: 0;
  padding: 3px 9px;

  border-radius: 6px;

  font-size: 11px;
}

.suggestion-list {
  margin: 0;
  padding: 12px 16px 12px 32px;

  color: #667085;
  font-size: 13px;
  line-height: 1.9;

  background: #fafbfc;
  border: 1px solid #edf0f3;
  border-radius: 10px;
}

.suggestion-list li {
  padding-left: 3px;
}

.report-actions {
  margin-top: 28px;

  display: flex;
  justify-content: center;
  gap: 10px;
}

.report-actions :deep(.ant-btn) {
  min-width: 100px;
  height: 34px;
  border-radius: 7px;
}

/* =========================
   Responsive
========================= */

@media (max-width: 992px) {
  .page-content {
    padding: 18px;
  }

  .left-column {
    margin-bottom: 0;
  }
}

@media (max-width: 768px) {
  .page-header {
    height: auto;
    min-height: 64px;
    padding: 10px 14px;
  }

  .header-left {
    min-width: 0;
  }

  .header-title {
    min-width: 0;
  }

  .title {
    font-size: 15px;
  }

  .subtitle {
    max-width: 180px;
  }

  .header-right {
    flex-shrink: 0;
  }

  .page-content {
    padding: 12px;
  }

  .info-card :deep(.ant-card-body),
  .conversation-card :deep(.ant-card-body),
  .answer-card :deep(.ant-card-body),
  .report-card :deep(.ant-card-body) {
    padding: 14px;
  }

  .interviewer-message,
  .candidate-message {
    max-width: 100%;
  }

  .question-content,
  .answer-content {
    padding: 12px 14px;
  }

  .answer-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .answer-footer .answer-tip {
    width: 100%;
  }

  .answer-footer :deep(.ant-btn) {
    width: 100%;
  }

  .report-actions {
    flex-direction: column;
  }

  .report-actions :deep(.ant-btn) {
    width: 100%;
  }
}
</style>
```




