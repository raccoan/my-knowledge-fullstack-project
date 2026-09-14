
<script setup lang="ts">
import {
  computed,
  nextTick,
  ref,
  onMounted,

} from 'vue'

import { useRouter } from 'vue-router'

import {
  message,
} from 'ant-design-vue'

import {
  SendOutlined,
  StopOutlined,
  CopyOutlined,
  ReloadOutlined,
  ArrowDownOutlined,
  RobotOutlined,
  UserOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue'

import {
  streamChat,
} from '@/api/chat'


import {createConversation,getConversationMessages,getConversations,deleteConversation} from '@/api/conversations'

import type {
  ChatSource,
} from '@/api/chat'

import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import type { Conversation,ChatMessage } from '@/api/conversations'
/**
 * =========================
 * Markdown
 * =========================
 */
const md: any = new MarkdownIt({
  html: false,
  breaks: true,

  highlight(
    code: string,
    language: string,
  ) {
    if (
      language &&
      hljs.getLanguage(language)
    ) {
      try {
        return (
          '<pre class="hljs"><code>' +
          hljs.highlight(
            code,
            {
              language,
            },
          ).value +
          '</code></pre>'
        )
      } catch {
        // ignore
      }
    }

    return (
      '<pre class="hljs"><code>' +
      md.utils.escapeHtml(code) +
      '</code></pre>'
    )
  },
})

/**
 * =========================
 * 类型
 * =========================
 */
interface MessageItem {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
}

/**
 * =========================
 * 状态
 * =========================
 */

const router = useRouter()
const messages = ref<MessageItem[]>([])

const conversations = ref<Conversation[]>([])

const currentConversationId = ref<number | null>(null)


const inputValue = ref('')

const loading = ref(false)

const currentAssistantId =
  ref<number | null>(null)

const abortController =
  ref<AbortController | null>(null)


/**
 * 真正的滚动容器
 *
 * 注意：
 * 这里绑定的是原生 div，
 * 所以 chatContainer.value 一定是 HTMLElement。
 */
const chatContainer =
  ref<HTMLElement | null>(null)

const showBackToBottom =
  ref(false)

/**
 * =========================
 * 计算属性
 * =========================
 */
const canSend = computed(() => {
  return (
    inputValue.value.trim().length > 0 &&
    !loading.value
  )
})

/**
 * =========================
 * Markdown 渲染
 * =========================
 */
const renderMarkdown = (
  content: string,
) => {
  return md.render(content || '')
}

/**
 * =========================
 * 滚动到底部
 * =========================
 */
const scrollToBottom = async (
  smooth = true,
) => {
  await nextTick()

  const container =
    chatContainer.value

  if (!container) {
    return
  }

  container.scrollTo({
    top: container.scrollHeight,
    behavior: smooth
      ? 'smooth'
      : 'auto',
  })

  showBackToBottom.value = false
}

/**
 * =========================
 * 检查是否接近底部
 * =========================
 */
const handleScroll = () => {
  const container =
    chatContainer.value

  if (!container) {
    return
  }

  const distance =
    container.scrollHeight -
    container.scrollTop -
    container.clientHeight

  showBackToBottom.value =
    distance > 150
}

/**
 * =========================
 * 发送消息
 * =========================
 */
const sendMessage = async (
  question?: string,
) => {
  const text = (
    question ??
    inputValue.value
  ).trim()

  if (!text) {
    return
  }

  if (loading.value) {
    return
  }

  if (
  currentConversationId.value === null
) {
  const conversation =
    await createConversation()

  conversations.value.unshift(
    conversation,
  )

  currentConversationId.value =
    conversation.id
}

  /**
   * =========================
   * 用户消息
   * =========================
   */
  const userMessage: MessageItem = {
    id: Date.now(),
    role: 'user',
    content: text,
  }

  messages.value.push(
    userMessage,
  )

  inputValue.value = ''

  await scrollToBottom()

  /**
   * =========================
   * AI 消息
   * =========================
   */
  const assistantId =
    Date.now() + 1

  const assistantMessage:
    MessageItem = {
      id: assistantId,
      role: 'assistant',
      content: '',
      sources: [],
    }

  messages.value.push(
    assistantMessage,
  )

  currentAssistantId.value =
    assistantId

  loading.value = true

  /**
   * =========================
   * AbortController
   *
   * 用于停止 SSE 请求
   * =========================
   */
  const controller =
    new AbortController()

  abortController.value =
    controller

  
  try {

    if(currentConversationId.value===null){
      const conversation = await createConversation()

      currentConversationId.value = conversation.id
      conversations.value.unshift(conversation)
    }

    await streamChat(
      {
        question: text,
        conversation_id:currentConversationId.value,
      },

      /**
       * =========================
       * 来源
       * =========================
       */
      (sources) => {
        const target =
          messages.value.find(
            item =>
              item.id === assistantId,
          )

        if (!target) {
          return
        }

        target.sources =
          sources

        scrollToBottom()
      },

      /**
       * =========================
       * AI 内容
       * =========================
       */
      (content) => {
        const target =
          messages.value.find(
            item =>
              item.id === assistantId,
          )

        if (!target) {
          return
        }

        target.content += content

        scrollToBottom()
      },

      /**
       * =========================
       * 完成
       * =========================
       */
      () => {
        loading.value = false

        currentAssistantId.value =
          null

        abortController.value =
          null

        scrollToBottom()
      },

      controller.signal,
    )
  } catch (error) {
    /**
     * =========================
     * 用户主动停止
     * =========================
     */
    if (
      error instanceof DOMException &&
      error.name === 'AbortError'
    ) {
      return
    }

    console.error(
      '聊天请求失败:',
      error,
    )

    const target =
      messages.value.find(
        item =>
          item.id === assistantId,
      )

    if (
      target &&
      !target.content
    ) {
      target.content =
        '抱歉，请求失败，请稍后重试。'
    }

    message.error(
      'AI 请求失败',
    )
  } finally {
    loading.value = false

    currentAssistantId.value =
      null

    abortController.value =
      null
  }
}

/**
 * =========================
 * 停止生成
 * =========================
 */
const stopGeneration = () => {
  if (!abortController.value) {
    return
  }

  abortController.value.abort()

  abortController.value = null

  loading.value = false

  currentAssistantId.value =
    null

  message.info(
    '已停止生成',
  )
}

/**
 * =========================
 * 重新生成
 * =========================
 */
const regenerate = async (
  index: number,
) => {
  if (loading.value) {
    return
  }

  const assistant =
    messages.value[index]

  if (
    !assistant ||
    assistant.role !== 'assistant'
  ) {
    return
  }

  /**
   * 找到上一条用户消息
   */
  let userMessage:
    MessageItem | undefined

  for (
    let i = index - 1;
    i >= 0;
    i--
  ) {
    if (
      messages.value[i].role ===
      'user'
    ) {
      userMessage =
        messages.value[i]

      break
    }
  }

  if (!userMessage) {
    return
  }

  /**
   * 删除旧 AI 消息
   */
  messages.value.splice(
    index,
    1,
  )

  /**
   * 重新发送
   */
  await sendMessage(
    userMessage.content,
  )
}

/**
 * =========================
 * 复制回答
 * =========================
 */
const copyMessage = async (
  content: string,
) => {
  try {
    await navigator.clipboard.writeText(
      content,
    )

    message.success(
      '已复制',
    )
  } catch {
    message.error(
      '复制失败',
    )
  }
}

/**
 * =========================
 * Enter 发送
 * =========================
 */
const handleInputKeydown = (
  event: KeyboardEvent,
) => {
  /**
   * Shift + Enter
   * 换行
   */
  if (
    event.key === 'Enter' &&
    event.shiftKey
  ) {
    return
  }

  /**
   * Enter
   * 发送
   */
  if (
    event.key === 'Enter'
  ) {
    event.preventDefault()

    if (canSend.value) {
      sendMessage()
    }
  }
}


/**
 * =========================
 * 获取历史会话
 * =========================
 */

const loadConversations = async () => {
  try{
    conversations.value = await getConversations()
  }catch (error) {
    console.log("获取会话失败:",error)
  }
}

/**
 * =========================
 * 清空聊天
 * =========================
 */
const clearChat = () => {
  if (loading.value) {
    stopGeneration()
  }

  messages.value = []

  showBackToBottom.value =
    false

  message.success(
    '已清空对话',
  )
}



/**
 * =========================
 * 新建对话
 * =========================
 */
const createNewConversation = async () => {
    if (loading.value) {
      stopGeneration()
    }

    try {
      const conversation =
        await createConversation()

      conversations.value.unshift(
        conversation,
      )

      currentConversationId.value =
        conversation.id

      messages.value = []

      showBackToBottom.value =
        false

      message.success(
        '已创建新对话',
      )
    } catch (error) {
      console.error(
        '创建会话失败:',
        error,
      )

      message.error(
        '创建对话失败',
      )
    }
}


/**
 * =========================
 * 切换会话
 * =========================
 */
 
const switchConversation = async (conversationId:number) => {
  if(loading.value) stopGeneration()
  try{
    const conversationMessages = await getConversationMessages(
      conversationId
    ) 
    currentConversationId.value = conversationId

    messages.value = conversationMessages.map((item:ChatMessage)=>({
      id:item.id,
      role:item.role,
      content:item.content,
      sources:[],

      }),
    )
    await scrollToBottom(false,)

  }catch(error){
     console.error(
        '加载会话失败:',
        error,
      )

      // 弹出失败提示。
      message.error(
        '加载会话失败',
      )
  }
}



onMounted(()=>{
  loadConversations()
})
</script>

<template>
  <a-layout class="chat-page">
    <!-- =========================
         左侧
         ========================= -->
    <a-layout-sider
      :width="240"
      class="chat-sider"
    >
      <div class="sider-content">
        <div class="brand">
          <RobotOutlined />

          <span>
            AI 知识助手
          </span>
        </div>

        <a-button
          type="primary"
          block
          class="new-chat-button"
          @click="createNewConversation"
        >
          新建对话
        </a-button>

        <a-divider />

        <div class="sider-title">
          历史对话
        </div>

        <a-list
          v-if="conversations.length"
          size="small"
          class="conversation-list"
          :data-source="conversations"
        >
          <template #renderItem="{ item }">
            <a-list-item
              class="conversation-item"
              :class="{
                'conversation-item-active':
                  currentConversationId === item.id,
              }"
              @click="
                switchConversation(item.id)
              "
            >
              <div class="conversation-title">
                {{ item.title }}
              </div>
            </a-list-item>
          </template>
        </a-list>

        <a-empty
          v-else
          description="暂无历史对话"
          class="conversation-empty"
        />

        <a-divider />

        <div class="sider-title">
          当前知识库
        </div>

        <a-card
          size="small"
          :bordered="false"
          class="knowledge-card"
          hoverable
          @click="router.push('/knowledge')"
        >
          <a-space>
            <FileTextOutlined />

            <span>
              我的知识库
            </span>
          </a-space>
        </a-card>

        <div class="sider-tip">
          AI 会优先根据你的知识库内容回答问题。
        </div>
      </div>
    </a-layout-sider>

    <!-- =========================
         主区域
         ========================= -->
    <a-layout>
      <!-- Header -->
      <a-layout-header
        class="chat-header"
      >
        <div>
          <div class="header-title">
            知识库问答
          </div>

          <div class="header-subtitle">
            基于你的个人知识库进行 AI 问答
          </div>
        </div>

        <a-button
          type="text"
          :disabled="
            loading ||
            !messages.length
          "
          @click="clearChat"
        >
          清空对话
        </a-button>
      </a-layout-header>

      <!-- Content -->
      <a-layout-content
        class="chat-content"
      >
        <!--
          真正的滚动容器

          这里必须使用原生 div，
          不能直接给 a-layout-content 绑定 ref。
        -->
        <div
          ref="chatContainer"
          class="chat-scroll-container"
          @scroll="handleScroll"
        >
          <div
            class="message-container"
          >
            <!-- 空状态 -->
            <a-empty
              v-if="!messages.length"
              description="开始向你的知识库提问吧"
              class="empty-chat"
            >
              <template #image>
                <RobotOutlined
                  class="empty-icon"
                />
              </template>
            </a-empty>

            <!-- 消息 -->
            <div
              v-for="(
                item,
                index
              ) in messages"
              :key="item.id"
              class="message-row"
              :class="{
                'user-row':
                  item.role === 'user',

                'assistant-row':
                  item.role === 'assistant',
              }"
            >
              <!-- 用户头像 -->
              <a-avatar
                v-if="
                  item.role === 'user'
                "
                class="avatar user-avatar"
              >
                <template #icon>
                  <UserOutlined />
                </template>
              </a-avatar>

              <!-- 消息主体 -->
              <div
                class="message-main"
                :class="{
                  'user-main':
                    item.role === 'user',
                }"
              >
                <!-- 用户消息 -->
                <a-card
                  v-if="
                    item.role === 'user'
                  "
                  size="small"
                  class="user-message"
                  :bordered="false"
                >
                  <div
                    class="user-content"
                  >
                    {{ item.content }}
                  </div>
                </a-card>

                <!-- AI 消息 -->
                <a-card
                  v-else
                  size="small"
                  class="assistant-message"
                  :bordered="false"
                >
                  <div
                    class="assistant-content markdown-body"
                    v-html="
                      renderMarkdown(
                        item.content,
                      )
                    "
                  ></div>

                  <!-- 正在生成 -->
                  <a-spin
                    v-if="
                      loading &&
                      currentAssistantId ===
                        item.id &&
                      !item.content
                    "
                    size="small"
                    class="generating"
                  />

                  <!-- AI 操作 -->
                  <a-space
                    v-if="
                      item.content
                    "
                    class="message-actions"
                  >
                    <a-button
                      type="text"
                      size="small"
                      @click="
                        copyMessage(
                          item.content,
                        )
                      "
                    >
                      <template #icon>
                        <CopyOutlined />
                      </template>

                      复制
                    </a-button>

                    <a-button
                      type="text"
                      size="small"
                      :disabled="loading"
                      @click="
                        regenerate(index)
                      "
                    >
                      <template #icon>
                        <ReloadOutlined />
                      </template>

                      重新生成
                    </a-button>
                  </a-space>

                  <!-- =================
                       RAG 来源
                       ================= -->
                  <div
                    v-if="
                      item.sources &&
                      item.sources.length
                    "
                    class="source-wrapper"
                  >
                    <a-divider />

                    <div
                      class="source-title"
                    >
                      <FileTextOutlined />

                      <span>
                        参考来源
                      </span>

                      <a-tag
                        color="blue"
                      >
                        {{
                          item.sources.length
                        }}
                        个片段
                      </a-tag>
                    </div>

                    <a-collapse
                      ghost
                      class="source-collapse"
                    >
                      <a-collapse-panel
                        v-for="(
                          source,
                          sourceIndex
                        ) in item.sources"
                        :key="
                          source.document_id +
                          '-' +
                          sourceIndex
                        "
                        :header="
                          `知识片段 ${
                            sourceIndex + 1
                          }`
                        "
                      >
                        <a-card
                          size="small"
                          :bordered="false"
                          class="source-card"
                        >
                          <a-space
                            direction="vertical"
                            style="width: 100%"
                          >
                            <a-tag
                              color="blue"
                            >
                              {{ source.filename }}
                            </a-tag>
                            <span class="source-score">相关度{{ ((1 - source.distance) * 100).toFixed(1) }}%</span>

                            <div
                              class="source-content"
                            >
                              {{
                                source.content
                              }}
                            </div>
                          </a-space>
                        </a-card>
                      </a-collapse-panel>
                    </a-collapse>
                  </div>
                </a-card>
              </div>

              <!-- AI 头像 -->
              <a-avatar
                v-if="
                  item.role ===
                  'assistant'
                "
                class="avatar assistant-avatar"
              >
                <template #icon>
                  <RobotOutlined />
                </template>
              </a-avatar>
            </div>

            <!-- 停止生成 -->
            <div
              v-if="loading"
              class="stop-wrapper"
            >
              <a-button
                danger
                @click="
                  stopGeneration
                "
              >
                <template #icon>
                  <StopOutlined />
                </template>

                停止生成
              </a-button>
            </div>
          </div>

          <!-- 回到底部 -->
          <a-button
            v-if="
              showBackToBottom
            "
            class="back-bottom-button"
            shape="circle"
            @click="
              scrollToBottom()
            "
          >
            <template #icon>
              <ArrowDownOutlined />
            </template>
          </a-button>
        </div>
      </a-layout-content>

      <!-- =========================
           输入区域
           ========================= -->
      <a-layout-footer
        class="chat-footer"
      >
        <div class="input-wrapper">
          <a-textarea
            v-model:value="inputValue"
            :auto-size="{
              minRows: 2,
              maxRows: 6,
            }"
            :maxlength="5000"
            show-count
            placeholder="输入你的问题，Enter 发送，Shift + Enter 换行"
            :disabled="loading"
            @keydown="
              handleInputKeydown
            "
          />

          <div class="input-bottom">
            <span
              class="input-tip"
            >
              AI 会基于当前知识库进行检索
            </span>

            <a-button
              type="primary"
              :disabled="!canSend"
              @click="sendMessage()"
            >
              <template #icon>
                <SendOutlined />
              </template>

              发送
            </a-button>
          </div>
        </div>
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<style scoped>
.chat-page {
  height: 100vh;
  overflow: hidden;
}

/* =========================
   左侧
   ========================= */

.chat-sider {
  background: #fff !important;
  border-right: 1px solid #f0f0f0;
}

.sider-content {
  padding: 20px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 16px;
  font-weight: 600;
}

.new-chat-button {
  height: 40px;
}

.sider-title {
  margin-bottom: 10px;
  color: #999;
  font-size: 13px;
}

.knowledge-card {
  cursor: pointer;
  background: #f5f5f5;
}

.sider-tip {
  margin-top: 16px;
  color: #999;
  font-size: 12px;
  line-height: 1.6;
}

/* =========================
   Header
   ========================= */

.chat-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;

  line-height: normal;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 22px;
}

.header-subtitle {
  margin-top: 3px;
  color: #999;
  font-size: 12px;
  line-height: 18px;
}
/* =========================
   内容区域
   ========================= */

.chat-content {
  position: relative;
  background: #fafafa;
}

/*
 * 真正的滚动容器
 *
 * 注意：
 * chatContainer ref 指向这里的原生 div。
 */
.chat-scroll-container {
  position: relative;
  height: 100%;
  overflow-y: auto;
}

.message-container {
  width: min(900px, calc(100% - 48px));
  margin: 0 auto;
  padding: 32px 0 20px;
}

/* =========================
   空状态
   ========================= */

.empty-chat {
  margin-top: 150px;
}

.empty-icon {
  font-size: 48px;
}

/* =========================
   消息
   ========================= */

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
}

.user-row {
  justify-content: flex-end;
}

.assistant-row {
  justify-content: flex-start;
}

.avatar {
  flex-shrink: 0;
}

.user-avatar {
  background: #1677ff;
}

.assistant-avatar {
  background: #722ed1;
}

.message-main {
  max-width: calc(100% - 50px);
}

.user-main {
  display: flex;
  justify-content: flex-end;
}

.user-message {
  background: #e6f4ff;
}

.user-content {
  white-space: pre-wrap;
  line-height: 1.7;
}

.assistant-message {
  width: 100%;
  background: #fff;
  box-shadow: 0 1px 2px rgb(0 0 0 / 4%);
}

.assistant-content {
  min-height: 24px;
  line-height: 1.8;
}

.generating {
  margin-top: 8px;
}

/* =========================
   AI 操作
   ========================= */

.message-actions {
  margin-top: 12px;
}

.message-actions :deep(.ant-btn) {
  color: #999;
}

.message-actions :deep(.ant-btn:hover) {
  color: #1677ff;
}

/* =========================
   Markdown
   ========================= */

.markdown-body :deep(p) {
  margin: 0 0 12px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
}

.markdown-body :deep(li) {
  margin-bottom: 6px;
}

.markdown-body :deep(pre) {
  overflow-x: auto;
  margin: 12px 0;
  padding: 14px;
  border-radius: 8px;
}

.markdown-body :deep(code) {
  font-family:
    'SFMono-Regular',
    Consolas,
    'Liberation Mono',
    monospace;
}

.markdown-body :deep(:not(pre) > code) {
  padding: 2px 5px;
  border-radius: 4px;
  background: #f5f5f5;
}

.markdown-body :deep(blockquote) {
  margin: 12px 0;
  padding-left: 12px;
  border-left: 3px solid #d9d9d9;
  color: #666;
}

/* =========================
   来源
   ========================= */

.source-wrapper {
  margin-top: 8px;
}

.source-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  color: #666;
  font-size: 13px;
  font-weight: 500;
}

.source-collapse {
  margin-top: 4px;
}

.source-card {
  background: #f7f8fa;
}

.source-score{
  color:#999;
  font-size:12px;
}

.source-content {
  color: #666;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
}

/* =========================
   停止
   ========================= */

.stop-wrapper {
  display: flex;
  justify-content: center;
  margin: 8px 0 20px;
}

/* =========================
   回到底部
   ========================= */

.back-bottom-button {
  position: sticky;
  bottom: 20px;
  display: block;
  margin: 0 auto;
  box-shadow: 0 2px 8px rgb(0 0 0 / 12%);
}

/* =========================
   输入框
   ========================= */

.chat-footer {
  padding: 16px 24px 20px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}

.input-wrapper {
  width: min(900px, 100%);
  margin: 0 auto;
}

.input-wrapper :deep(.ant-input) {
  resize: none;
}

.input-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.input-tip {
  color: #999;
  font-size: 12px;
}

/* =========================
   响应式
   ========================= */

@media (max-width: 768px) {
  .chat-sider {
    display: none;
  }

  .message-container {
    width: calc(100% - 24px);
    padding-top: 20px;
  }

  .chat-header {
    padding: 0 12px;
  }

  .chat-footer {
    padding: 12px;
  }

  .message-main {
    max-width: calc(100% - 44px);
  }

  .input-tip {
    display: none;
  }

  .input-bottom {
    justify-content: flex-end;
  }
}

.conversation-list {
  margin-bottom: 12px;
}

.conversation-item {
  display: block;
  padding: 9px 10px !important;
  border-radius: 6px;
  cursor: pointer;
  border-bottom: none !important;
}

.conversation-item:hover {
  background: #f5f5f5;
}

.conversation-item-active {
  background: #e6f4ff;
}

.conversation-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #333;
  font-size: 13px;
}

.conversation-empty {
  margin: 12px 0;
}

</style>
