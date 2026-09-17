<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  message
} from 'ant-design-vue'

import {
  createInterview,
  answerInterview,
  getInterview,
  type InterviewMessage,
  type InterviewReport
} from '@/api/interviews'

const route = useRoute()
const router = useRouter()

const interviewId = ref<number | null>(null)

const loading = ref(false)
const submitting = ref(false)

const question = ref('')
const answer = ref('')

const messages = ref<InterviewMessage[]>([])

const currentScore = ref<number | null>(null)
const currentFeedback = ref('')
const referenceAnswer = ref('')
const knowledgeGap = ref<string[]>([])

const showReferenceAnswer = ref(false)

const finished = ref(false)

const report = ref<InterviewReport | null>(null)


const startInterview = async () => {
  const resumeId = Number(
    route.query.resumeId
  )

  if (!resumeId) {
    message.error('没有指定简历')
    return
  }

  loading.value = true

  try {
    const data = await createInterview(
      resumeId
    )

    interviewId.value = data.id
    question.value = data.question

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

    router.replace({
      path: '/interview',
      query: {
        id: String(data.id)
      }
    })
  } catch (error) {
    console.error(error)
    message.error('创建面试失败')
  } finally {
    loading.value = false
  }
}


const loadInterview = async () => {
  const id = Number(
    route.query.id
  )

  if (!id) {
    return
  }

  loading.value = true

  try {
    const data = await getInterview(id)

    interviewId.value = data.id
    question.value =
      data.current_question || ''

    messages.value = data.messages

    finished.value =
      data.status === 'finished'
  } catch (error) {
    console.error(error)
    message.error('加载面试失败')
  } finally {
    loading.value = false
  }
}


const submitAnswer = async () => {
  if (!answer.value.trim()) {
    message.warning('请输入回答')
    return
  }

  if (!interviewId.value) {
    return
  }

  submitting.value = true

  try {
    const data = await answerInterview(
      interviewId.value,
      answer.value
    )

    currentScore.value =
      data.score

    currentFeedback.value =
      data.feedback

    referenceAnswer.value =
      data.reference_answer

    knowledgeGap.value =
      data.knowledge_gap

    showReferenceAnswer.value =
      false

    messages.value.push({
      id: Date.now(),
      role: 'candidate',
      content: answer.value,
      score: data.score,
      feedback: data.feedback,
      reference_answer:
        data.reference_answer,
      created_at:
        new Date().toISOString()
    })

    answer.value = ''

    if (data.finished) {
      finished.value = true
      report.value =
        data.report || null

      return
    }

    question.value =
      data.next_question

    messages.value.push({
      id: Date.now() + 1,
      role: 'interviewer',
      content: data.next_question,
      score: null,
      feedback: null,
      reference_answer: null,
      created_at:
        new Date().toISOString()
    })

  } catch (error) {
    console.error(error)
    message.error('提交回答失败')
  } finally {
    submitting.value = false
  }
}


onMounted(() => {
  const id = Number(
    route.query.id
  )

  if (id) {
    loadInterview()
  } else {
    startInterview()
  }
})
</script>

<template>
  <div class="interview-page">

    <a-spin :spinning="loading">

      <div class="interview-header">
        <div>
          <h2>AI 模拟面试</h2>
          <div class="sub-title">
            根据你的真实简历进行针对性面试
          </div>
        </div>

        <a-button
          @click="router.push('/resume')"
        >
          返回简历
        </a-button>
      </div>


      <a-row :gutter="20">

        <!-- 左侧面试信息 -->
        <a-col :xs="24" :lg="7">

          <a-card
            title="面试信息"
            :bordered="false"
          >

            <a-descriptions
              :column="1"
              size="small"
            >
              <a-descriptions-item label="状态">
                <a-tag
                  :color="
                    finished
                      ? 'green'
                      : 'blue'
                  "
                >
                  {{
                    finished
                      ? '已结束'
                      : '进行中'
                  }}
                </a-tag>
              </a-descriptions-item>

              <a-descriptions-item label="题目">
                最多 5 题
              </a-descriptions-item>

            </a-descriptions>

          </a-card>


          <a-card
            v-if="knowledgeGap.length"
            title="本题薄弱知识点"
            :bordered="false"
            class="side-card"
          >
            <a-space wrap>
              <a-tag
                v-for="item in knowledgeGap"
                :key="item"
                color="orange"
              >
                {{ item }}
              </a-tag>
            </a-space>
          </a-card>

        </a-col>


        <!-- 右侧面试区域 -->
        <a-col :xs="24" :lg="17">

          <a-card
            :bordered="false"
            class="interview-card"
          >

            <!-- 当前问题 -->
            <div class="question-section">

              <div class="section-title">
                AI 面试官
              </div>

              <div class="question">
                {{ question }}
              </div>

            </div>


            <!-- 回答 -->
            <div
              v-if="!finished"
              class="answer-section"
            >

              <a-textarea
                v-model:value="answer"
                :rows="7"
                placeholder="请输入你的回答..."
                :disabled="submitting"
              />

              <div class="submit-area">

                <a-button
                  type="primary"
                  :loading="submitting"
                  @click="submitAnswer"
                >
                  提交回答
                </a-button>

              </div>

            </div>


            <!-- 本题结果 -->
            <div
              v-if="currentScore !== null"
              class="result-section"
            >

              <a-divider />

              <a-statistic
                title="本题得分"
                :value="currentScore"
                suffix="/ 100"
              />

              <a-card
                size="small"
                title="AI 反馈"
                class="feedback-card"
              >
                {{ currentFeedback }}
              </a-card>


              <a-button
                v-if="referenceAnswer"
                type="link"
                @click="
                  showReferenceAnswer =
                    !showReferenceAnswer
                "
              >
                {{
                  showReferenceAnswer
                    ? '隐藏参考答案'
                    : '查看参考答案'
                }}
              </a-button>


              <a-card
                v-if="showReferenceAnswer"
                size="small"
                title="参考答案"
                class="reference-card"
              >
                {{ referenceAnswer }}
              </a-card>

            </div>


            <!-- 面试报告 -->
            <div
              v-if="finished && report"
              class="report-section"
            >

              <a-divider />

              <h3>
                面试结束
              </h3>

              <a-row :gutter="12">

                <a-col
                  :span="12"
                  :md="6"
                >
                  <a-statistic
                    title="综合得分"
                    :value="
                      report.overall_score
                    "
                  />
                </a-col>

                <a-col
                  :span="12"
                  :md="6"
                >
                  <a-statistic
                    title="项目能力"
                    :value="
                      report.project_ability
                    "
                  />
                </a-col>

                <a-col
                  :span="12"
                  :md="6"
                >
                  <a-statistic
                    title="技术能力"
                    :value="
                      report.technical_ability
                    "
                  />
                </a-col>

                <a-col
                  :span="12"
                  :md="6"
                >
                  <a-statistic
                    title="实践能力"
                    :value="
                      report.practical_ability
                    "
                  />
                </a-col>

              </a-row>


              <a-divider />

              <a-card
                title="优势"
                size="small"
              >
                <ul>
                  <li
                    v-for="item in report.strengths"
                    :key="item"
                  >
                    {{ item }}
                  </li>
                </ul>
              </a-card>


              <a-card
                title="不足"
                size="small"
                class="report-card"
              >
                <ul>
                  <li
                    v-for="item in report.weaknesses"
                    :key="item"
                  >
                    {{ item }}
                  </li>
                </ul>
              </a-card>


              <a-card
                title="知识薄弱点"
                size="small"
                class="report-card"
              >
                <a-space wrap>
                  <a-tag
                    v-for="item in report.knowledge_gaps"
                    :key="item"
                    color="orange"
                  >
                    {{ item }}
                  </a-tag>
                </a-space>
              </a-card>


              <a-card
                title="学习建议"
                size="small"
                class="report-card"
              >
                <ul>
                  <li
                    v-for="item in report.suggestions"
                    :key="item"
                  >
                    {{ item }}
                  </li>
                </ul>
              </a-card>

            </div>

          </a-card>

        </a-col>

      </a-row>

    </a-spin>

  </div>
</template>

<style scoped>
.interview-page {
  min-height: 100%;
  padding: 24px;
  background: #f5f5f5;
}

.interview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.interview-header h2 {
  margin: 0;
}

.sub-title {
  margin-top: 4px;
  color: #999;
  font-size: 13px;
}

.interview-card {
  min-height: 500px;
}

.side-card {
  margin-top: 16px;
}

.question-section {
  padding: 8px 0 20px;
}

.section-title {
  margin-bottom: 12px;
  color: #666;
  font-size: 14px;
  font-weight: 600;
}

.question {
  padding: 18px;
  border-radius: 8px;
  background: #f7f7f7;
  font-size: 16px;
  line-height: 1.8;
}

.answer-section {
  margin-top: 20px;
}

.submit-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.result-section {
  margin-top: 20px;
}

.feedback-card {
  margin-top: 20px;
}

.reference-card {
  margin-top: 8px;
  background: #fafafa;
}

.report-section {
  margin-top: 20px;
}

.report-card {
  margin-top: 12px;
}

@media (max-width: 768px) {
  .interview-page {
    padding: 12px;
  }

  .interview-header {
    align-items: flex-start;
  }

  .question {
    font-size: 15px;
  }
}
</style>