<template>
  <div class="chat-page">

    <!-- 顶部 -->
    <header class="chat-header">

      <div class="title">
        AI 知识库助手
      </div>

      <button
        class="logout-btn"
        @click="logout"
      >
        退出登录
      </button>

    </header>


    <!-- 聊天区域 -->
    <main
      ref="chatContentRef"
      class="chat-content"
    >

      <!-- 空状态 -->
      <div
        v-if="messages.length === 0"
        class="empty-state"
      >

        <h2>
          AI 知识库助手
        </h2>

        <p>
          基于你的知识库回答问题
        </p>

      </div>


      <!-- 消息 -->
      <div
        v-for="message in messages"
        :key="message.id"
        class="message-row"
        :class="message.role"
      >

        <!-- 头像 -->
        <div class="message-avatar">
          {{
            message.role === 'user'
              ? '你'
              : 'AI'
          }}
        </div>


        <!-- 内容 -->
        <div class="message-wrapper">

          <!-- 用户消息 -->
          <div
            v-if="message.role === 'user'"
            class="message-content user-content"
          >
            {{ message.content }}
          </div>


          <!-- AI消息 -->
          <div
            v-else
            class="assistant-content"
          >

            <div
              class="markdown-body"
              v-html="
                renderMarkdown(
                  message.content
                )
              "
            />

            <!-- 生成中的光标 -->
            <span
              v-if="
                loading &&
                message.id ===
                  currentAssistantId
              "
              class="cursor"
            >
              ▌
            </span>


            <!-- AI操作 -->
            <div
              v-if="
                !loading &&
                message.content
              "
              class="message-actions"
            >

              <button
                @click="
                  copyMessage(
                    message.content
                  )
                "
              >
                复制
              </button>

              <button
                @click="
                  regenerate(message)
                "
              >
                重新生成
              </button>

            </div>

          </div>

        </div>

      </div>

    </main>


    <!-- 输入区域 -->
    <footer class="chat-footer">

      <div class="input-wrapper">

        <textarea
          v-model="question"
          placeholder="输入你想问的问题..."
          :disabled="loading"
          @keydown.enter.exact.prevent="
            sendMessage
          "
        />

        <!-- 停止 -->
        <button
          v-if="loading"
          class="stop-btn"
          @click="stopGeneration"
        >
          停止
        </button>

        <!-- 发送 -->
        <button
          v-else
          :disabled="
            !question.trim()
          "
          @click="sendMessage"
        >
          发送
        </button>

      </div>

    </footer>

  </div>
</template>


<script setup lang="ts">

import {
  nextTick,
  ref,
} from 'vue'

import { useRouter } from 'vue-router'

import {
  streamChat,
} from '../../api/chat'

import {
  renderMarkdown,
} from '../../utils/markdown'


interface ChatMessage {
  id: number

  role:
    | 'user'
    | 'assistant'

  content: string
}


// router
const router =
  useRouter()


// 输入框
const question =
  ref('')


// 是否正在生成
const loading =
  ref(false)


// 消息列表
const messages =
  ref<ChatMessage[]>([])


// 当前AI消息
const currentAssistantId =
  ref<number | null>(null)


// 聊天区域
const chatContentRef =
  ref<HTMLElement | null>(null)


// 消息ID
let messageId = 0


// 当前请求控制器
let abortController:
  AbortController | null = null


/**
 * 滚动到底部
 */
async function scrollToBottom() {

  await nextTick()

  const element =
    chatContentRef.value

  if (!element) {
    return
  }

  element.scrollTop =
    element.scrollHeight
}


/**
 * 发送消息
 */
async function sendMessage() {

  const text =
    question.value.trim()

  if (
    !text ||
    loading.value
  ) {
    return
  }


  // 清空输入框
  question.value = ''


  // 用户消息
  const userMessage:
    ChatMessage = {

    id: ++messageId,

    role: 'user',

    content: text,
  }

  messages.value.push(
    userMessage,
  )


  await scrollToBottom()


  // 创建AI消息
  const assistantId =
    ++messageId

  const assistantMessage:
    ChatMessage = {

    id: assistantId,

    role: 'assistant',

    content: '',
  }

  messages.value.push(
    assistantMessage,
  )


  currentAssistantId.value =
    assistantId

  loading.value = true


  // 创建 AbortController
  abortController =
    new AbortController()


  await scrollToBottom()


  try {

    await streamChat(

      {
        question: text,
      },

      // 收到AI内容
      async (content) => {

        const message =
          messages.value.find(
            item =>
              item.id ===
              assistantId
          )

        if (!message) {
          return
        }


        message.content +=
          content


        await scrollToBottom()
      },


      // 完成
      () => {

        loading.value =
          false

        currentAssistantId.value =
          null

        abortController =
          null
      },


      // AbortSignal
      abortController.signal,
    )

  } catch (error) {

    console.error(
      '聊天失败：',
      error,
    )


    const message =
      messages.value.find(
        item =>
          item.id ===
          assistantId
      )


    if (message) {

      message.content =
        '请求失败，请检查后端服务是否正常运行。'
    }


    loading.value =
      false

    currentAssistantId.value =
      null

    abortController =
      null
  }
}


/**
 * 停止生成
 */
function stopGeneration() {

  if (!abortController) {
    return
  }

  abortController.abort()

  loading.value =
    false

  currentAssistantId.value =
    null

  abortController =
    null
}


/**
 * 重新生成
 */
async function regenerate(
  message: ChatMessage,
) {

  const index =
    messages.value.findIndex(
      item =>
        item.id ===
        message.id
    )

  if (index === -1) {
    return
  }


  // AI消息前面的用户消息
  const userMessage =
    messages.value[index - 1]

  if (
    !userMessage ||
    userMessage.role !== 'user'
  ) {
    return
  }


  // 清空原回答
  message.content = ''


  currentAssistantId.value =
    message.id

  loading.value = true


  abortController =
    new AbortController()


  try {

    await streamChat(

      {
        question:
          userMessage.content,
      },

      async (content) => {

        message.content +=
          content

        await scrollToBottom()
      },

      () => {

        loading.value =
          false

        currentAssistantId.value =
          null

        abortController =
          null
      },

      abortController.signal,
    )

  } catch (error) {

    console.error(
      '重新生成失败：',
      error,
    )

    loading.value =
      false

    currentAssistantId.value =
      null

    abortController =
      null
  }
}


/**
 * 复制
 */
async function copyMessage(
  content: string,
) {

  try {

    await navigator.clipboard.writeText(
      content,
    )

  } catch (error) {

    console.error(
      '复制失败：',
      error,
    )
  }
}


/**
 * 退出登录
 */
function logout() {

  localStorage.removeItem(
    'token',
  )

  router.push('/login')
}

</script>


<style scoped>

.chat-page {
  height: 100vh;

  display: flex;

  flex-direction: column;

  background: #f7f7f8;
}


/* header */

.chat-header {

  height: 60px;

  flex-shrink: 0;

  display: flex;

  align-items: center;

  justify-content:
    space-between;

  padding:
    0 24px;

  background:
    #ffffff;

  border-bottom:
    1px solid #e5e5e5;
}


.title {

  font-size: 18px;

  font-weight: 600;
}


.logout-btn {

  padding:
    6px 14px;

  border:
    1px solid #d9d9d9;

  border-radius:
    6px;

  background:
    #ffffff;

  cursor:
    pointer;
}


/* chat */

.chat-content {

  flex: 1;

  overflow-y: auto;

  padding:
    30px 20px;
}


/* empty */

.empty-state {

  height: 100%;

  display: flex;

  flex-direction: column;

  align-items: center;

  justify-content:
    center;

  color:
    #666;
}


.empty-state h2 {

  margin-bottom:
    10px;

  color:
    #222;
}


/* message */

.message-row {

  display: flex;

  max-width:
    900px;

  margin:
    0 auto 28px;

  gap:
    12px;
}


.message-row.user {

  flex-direction:
    row-reverse;
}


.message-avatar {

  width:
    36px;

  height:
    36px;

  flex-shrink: 0;

  display: flex;

  align-items: center;

  justify-content:
    center;

  border-radius:
    50%;

  background:
    #e5e5e5;

  font-size:
    13px;
}


.message-row.user
.message-avatar {

  background:
    #222;

  color:
    #ffffff;
}


.message-wrapper {

  max-width:
    75%;
}


/* user */

.user-content {

  padding:
    12px 16px;

  border-radius:
    10px;

  background:
    #222;

  color:
    #ffffff;

  line-height:
    1.7;

  white-space:
    pre-wrap;

  word-break:
    break-word;
}


/* assistant */

.assistant-content {

  position:
    relative;

  padding:
    4px 0;

  line-height:
    1.7;

  word-break:
    break-word;
}


/* markdown */

.markdown-body {

  color:
    #222;
}


/* markdown 标题 */

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {

  margin-top:
    18px;

  margin-bottom:
    10px;
}


/* markdown 段落 */

.markdown-body :deep(p) {

  margin:
    8px 0;
}


/* markdown 列表 */

.markdown-body :deep(ul),
.markdown-body :deep(ol) {

  padding-left:
    24px;
}


/* markdown code */

.markdown-body :deep(code) {

  padding:
    2px 5px;

  border-radius:
    4px;

  background:
    #eeeeee;

  font-family:
    Consolas,
    monospace;
}


/* 代码块 */

.markdown-body :deep(pre) {

  margin:
    14px 0;

  padding:
    14px;

  overflow-x:
    auto;

  border-radius:
    8px;

  background:
    #f0f0f0;
}


.markdown-body :deep(pre code) {

  padding:
    0;

  background:
    transparent;
}


/* cursor */

.cursor {

  margin-left:
    2px;

  animation:
    blink 1s infinite;
}


@keyframes blink {

  50% {
    opacity: 0;
  }

}


/* actions */

.message-actions {

  display: flex;

  gap:
    8px;

  margin-top:
    8px;
}


.message-actions button {

  border:
    none;

  background:
    transparent;

  color:
    #666;

  font-size:
    12px;

  cursor:
    pointer;
}


.message-actions button:hover {

  color:
    #222;
}


/* footer */

.chat-footer {

  flex-shrink: 0;

  padding:
    20px;

  background:
    #ffffff;

  border-top:
    1px solid #e5e5e5;
}


.input-wrapper {

  max-width:
    900px;

  margin:
    0 auto;

  display:
    flex;

  gap:
    10px;
}


textarea {

  flex: 1;

  min-height:
    50px;

  max-height:
    150px;

  padding:
    12px;

  resize:
    vertical;

  border:
    1px solid #d9d9d9;

  border-radius:
    8px;

  outline:
    none;

  font-size:
    14px;
}


textarea:focus {

  border-color:
    #999;
}


.input-wrapper button {

  width:
    80px;

  align-self:
    flex-end;

  height:
    44px;

  border:
    none;

  border-radius:
    8px;

  background:
    #222;

  color:
    #ffffff;

  cursor:
    pointer;
}


.input-wrapper button:disabled {

  background:
    #aaa;

  cursor:
    not-allowed;
}


.stop-btn {

  background:
    #d9363e !important;
}

</style>