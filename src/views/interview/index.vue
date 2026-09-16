<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRoute } from 'vue-router'

import {
  createInterview,
  answerInterview,
  getInterview,
  type InterviewMessage,
} from '@/api/interviews'

const route = useRoute()

const interviewId = ref<number | null>(null)

const loading = ref(false)
const answering = ref(false)
const finished = ref(false)

const question = ref('')
const answer = ref('')

const score = ref<number | null>(null)
const feedback = ref('')

const messages = ref<InterviewMessage[]>([])

const resumeId = Number(
  route.query.resumeId
)


const startInterview = async () => {
  if (!resumeId) {
    message.error('缺少简历ID')
    return
  }

  loading.value = true

  try {
    const result = await createInterview(
      resumeId
    )

    interviewId.value = result.id
    question.value = result.question

    messages.value = [
      {
        id: Date.now(),
        role: 'interviewer',
        content: result.question,
        score: null,
        feedback: null,
        created_at: new Date().toISOString(),
      },
    ]
  } catch (error) {
    console.error(error)
    message.error('创建面试失败')
  } finally {
    loading.value = false
  }
}


const submitAnswer = async () => {
  if (!interviewId.value) {
    message.error('面试尚未开始')
    return
  }

  if (!answer.value.trim()) {
    message.warning('请输入回答')
    return
  }

  answering.value = true

  try {
    const currentAnswer = answer.value

    messages.value.push({
      id: Date.now(),
      role: 'candidate',
      content: currentAnswer,
      score: null,
      feedback: null,
      created_at: new Date().toISOString(),
    })

    answer.value = ''

    const result = await answerInterview(
      interviewId.value,
      currentAnswer
    )

    score.value = result.score
    feedback.value = result.feedback

    if (result.finished) {
      finished.value = true
      question.value = ''
    } else {
      question.value = result.next_question

      messages.value.push({
        id: Date.now() + 1,
        role: 'interviewer',
        content: result.next_question,
        score: result.score,
        feedback: result.feedback,
        created_at: new Date().toISOString(),
      })
    }
  } catch (error) {
    console.error(error)
    message.error('提交回答失败')
  } finally {
    answering.value = false
  }
}


const loadInterview = async () => {
  if (!route.params.id) {
    return
  }

  const id = Number(
    route.params.id
  )

  if (!id) {
    return
  }

  try {
    const result = await getInterview(id)

    interviewId.value = result.id
    messages.value = result.messages
    finished.value = result.status === 'finished'
    question.value =
      result.current_question || ''
  } catch (error) {
    console.error(error)
    message.error('加载面试失败')
  }
}


onMounted(async () => {
  if (route.params.id) {
    await loadInterview()
  } else {
    await startInterview()
  }
})
</script>

<template>
  <div class="interview-page">
    <div class="interview-header">
      <div>
        <div class="title">
          AI 模拟面试
        </div>

        <div class="subtitle">
          根据你的真实简历进行针对性面试
        </div>
      </div>

      <a-tag
        v-if="finished"
        color="green"
      >
        面试结束
      </a-tag>

      <a-tag
        v-else
        color="blue"
      >
        面试进行中
      </a-tag>
    </div>

    <div class="interview-content">
      <div class="chat-panel">
        <div class="message-list">
          <div
            v-for="item in messages"
            :key="item.id"
            class="message-item"
            :class="item.role"
          >
            <div class="message-role">
              {{
                item.role === 'interviewer'
                  ? 'AI 面试官'
                  : '我'
              }}
            </div>

            <div class="message-content">
              {{ item.content }}
            </div>

            <div
              v-if="
                item.role === 'interviewer' &&
                item.score !== null
              "
              class="feedback"
            >
              <div class="score">
                本题得分：{{ item.score }}
              </div>

              <div>
                {{ item.feedback }}
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="!finished"
          class="answer-panel"
        >
          <a-textarea
            v-model:value="answer"
            :rows="6"
            placeholder="请输入你的回答..."
            :disabled="answering"
            @keydown.ctrl.enter="submitAnswer"
          />

          <div class="answer-footer">
            <span>
              Ctrl + Enter 提交
            </span>

            <a-button
              type="primary"
              :loading="answering"
              @click="submitAnswer"
            >
              提交回答
            </a-button>
          </div>
        </div>

        <a-result
          v-else
          status="success"
          title="面试完成"
          :sub-title="`本轮累计得分：${score ?? 0}`"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.interview-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.interview-header {
  height: 72px;
  flex-shrink: 0;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.title {
  font-size: 18px;
  font-weight: 600;
}

.subtitle {
  margin-top: 4px;
  color: #999;
  font-size: 13px;
}

.interview-content {
  flex: 1;
  min-height: 0;
  padding: 24px;
  overflow: hidden;
}

.chat-panel {
  height: 100%;
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.message-list {
  flex: 1;
  min-height: 0;
  padding: 24px;
  overflow-y: auto;
}

.message-item {
  max-width: 80%;
  margin-bottom: 24px;
}

.message-item.interviewer {
  margin-right: auto;
}

.message-item.candidate {
  margin-left: auto;
}

.message-role {
  margin-bottom: 6px;
  color: #999;
  font-size: 12px;
}

.message-content {
  padding: 12px 16px;
  line-height: 1.7;
  border-radius: 8px;
  white-space: pre-wrap;
}

.interviewer .message-content {
  background: #f5f5f5;
}

.candidate .message-content {
  background: #e6f4ff;
}

.feedback {
  margin-top: 10px;
  padding: 12px;
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 8px;
  line-height: 1.6;
}

.score {
  margin-bottom: 4px;
  font-weight: 600;
}

.answer-panel {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

.answer-footer {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #999;
  font-size: 12px;
}
</style>