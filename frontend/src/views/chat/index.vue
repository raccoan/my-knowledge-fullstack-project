
<script setup lang="ts">
import {
  computed,
  nextTick,
  ref,
  onMounted,
  onBeforeUnmount,

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
  ProfileOutlined,
} from '@ant-design/icons-vue'

import {
  streamChat,
} from '@/api/chat'


import {
  createConversation,
  getConversationMessages,
  getConversations,
  deleteConversation,
  updateConversationTitle
} from '@/api/conversations'

import type {
  ChatSource,
} from '@/api/chat'

import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import type { Conversation,ChatMessage } from '@/api/conversations'
import { Modal } from 'ant-design-vue'
import {useUserStore} from '@/stores/user'


const userStore = useUserStore()
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
  /** 【新增】本轮被用户停止时，用于显示可重新生成的状态。 */
  interrupted?: boolean
}

/**
 * =========================
 * 状态
 * =========================
 */

const router = useRouter()
const messages = ref<MessageItem[]>([])

const conversations = ref<Conversation[]>([])

const editingConversationId = ref<number | null>(null)

  const editingTitle = ref("")

const currentConversationId = ref<number | null>(null)


const inputValue = ref('')

/** 【新增交互】空会话时提供可直接发起的任务入口。 */
const starterPrompts = [
  '总结我的知识库中最重要的内容',
  '根据我的资料生成一份学习计划',
  '帮我找出与 Vue 3 相关的知识点',
  '帮我整理一个技术面试复习方向',
]

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

/** 【新增】仅用户停留在底部时才自动跟随流式内容。 */
const shouldFollowStream = ref(true)

/**
 * 【交互优化】流式回答会高频触发内容更新；统一到下一帧滚动，
 * 避免每个字符都执行一次平滑滚动造成页面抖动。
 */
let scrollFrameId: number | null = null
let scrollTaskPending = false

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

  // 【新增】用户主动点击“回到底部”后才恢复自动跟随。
  shouldFollowStream.value = true

  container.scrollTo({
    top: container.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto',
  })

  showBackToBottom.value = false
}

/**
 * 【交互优化】一帧内只安排一次滚动。
 */
const scheduleScrollToBottom = (
) => {
  // 【核心修复】用户正在上滑阅读时，绝不抢夺滚动位置。
  if (!shouldFollowStream.value || scrollTaskPending) {
    return
  }

  scrollTaskPending = true
  scrollFrameId = window.requestAnimationFrame(
    async () => {
      scrollFrameId = null

      await nextTick()

      const container = chatContainer.value
      if (container && shouldFollowStream.value) {
        // 流式过程中使用 auto，避免浏览器反复叠加 smooth 动画造成抖动。
        container.scrollTop = container.scrollHeight
        showBackToBottom.value = false
      }

      scrollTaskPending = false
    },
  )
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

  const isNearBottom = distance <= 96

  // 【核心修复】用户离开底部即暂停自动滚动；回到底部后自动恢复。
  shouldFollowStream.value = isNearBottom
  showBackToBottom.value = !isNearBottom
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

  /**
   * =========================
   * 确保存在当前会话
   * =========================
   *
   * null 和 undefined 都视为没有会话
   */
  if (!currentConversationId.value) {
    try {
      const conversation =
        await createConversation()

      console.log(
        '创建会话返回值:',
        conversation,
      )

      conversations.value.unshift(
        conversation,
      )

      currentConversationId.value =
        conversation.id

      console.log(
        '设置后的会话 ID:',
        currentConversationId.value,
      )
    } catch (error) {
      console.error(
        '创建会话失败:',
        error,
      )

      message.error(
        '创建对话失败',
      )

      return
    }
  }

  /**
   * =========================
   * 再次确认会话 ID
   * =========================
   */
  const conversationId =
    currentConversationId.value

  if (!conversationId) {
    message.error(
      '当前对话不存在，请重新创建对话',
    )

    return
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

  await scrollToBottom(false)

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
   * =========================
   */
  const controller =
    new AbortController()

  abortController.value =
    controller

  try {
    console.log(
      '发送聊天请求:',
      {
        question: text,
        conversation_id:
          conversationId,
      },
    )

    /**
     * =========================
     * SSE
     * =========================
     */
await streamChat(
  {
    question: text,
    conversation_id:
      currentConversationId.value,
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
          item.id ===
          assistantId,
      )

    if (!target) {
      return
    }

    target.sources =
      sources

    scheduleScrollToBottom()
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
          item.id ===
          assistantId,
      )

    if (!target) {
      return
    }

    target.content +=
      content

    scheduleScrollToBottom()
  },

  /**
   * =========================
   * AI 自动生成标题
   * =========================
   */
  (title) => {
    const conversation =
      conversations.value.find(
        item =>
          item.id ===
          currentConversationId.value,
      )

    if (!conversation) {
      return
    }

    conversation.title =
      title
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

    // 仅仍停留在底部时才滚动，避免回答结束时把用户拉离阅读位置。
    if (shouldFollowStream.value) {
      void scrollToBottom(false)
    }
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
      // 【新增】立即给本地页面明确反馈；后端 finally 也会保存该提示。
      const target = messages.value.find(
        item => item.id === assistantId,
      )
      if (target) {
        target.interrupted = true
        if (!target.content) {
          target.content = '本次回答已停止，可点击“重新生成”再次尝试。'
        }
      }
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

  const interruptedId = currentAssistantId.value

  abortController.value.abort()

  // 【新增】不让用户只看到一条空回答，明确说明可再次生成。
  const target = messages.value.find(
    item => item.id === interruptedId,
  )
  if (target) {
    target.interrupted = true
    if (!target.content) {
      target.content = '本次回答已停止，可点击“重新生成”再次尝试。'
    }
  }

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

const startEditConversation = (
    item:Conversation
)=>{

    editingConversationId.value =
        item.id

    editingTitle.value =
        item.title
}

const saveConversationTitle = async(
    item:Conversation
)=>{


    if(!editingTitle.value.trim()){
        message.warning(
            "标题不能为空"
        )

        return
    }


    await updateConversationTitle(
        item.id,
        editingTitle.value
    )


    item.title =
        editingTitle.value


    editingConversationId.value =
        null


    message.success(
        "修改成功"
    )
}


const removeConversation = async(
    item:Conversation
)=>{


    await deleteConversation(
        item.id
    )


    conversations.value =
        conversations.value.filter(
            c=>c.id!==item.id
        )


    if(
        currentConversationId.value
        === item.id
    ){

        currentConversationId.value =
            null

        messages.value=[]
    }


    message.success(
        "删除成功"
    )
}



/**
 * =========================
 * 清空聊天
 * =========================
 */
// const clearChat = () => {
//   if (loading.value) {
//     stopGeneration()
//   }

//   messages.value = []

//   showBackToBottom.value =
//     false

//   message.success(
//     '已清空对话',
//   )
// }



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

// 登出函数
const handleLogout = () => {
  Modal.confirm({
    title:"退出登录",
    content:"确定要退出当前账号吗？",
    okText:"退出",
    cancelText:"取消",

    async onOk() {
      try{
        userStore.logout()
        router.push('/login')
        message.success("已退出登录")
      }catch(error){
        console.error("退出登录失败:",error)
        message.error("退出登录失败")
      }
    },
  })
}


onMounted(()=>{
  loadConversations()
})

const sendStarterPrompt = (prompt: string) => {
  void sendMessage(prompt)
}

/**
 * 【交互优化】离开聊天页时终止未完成的流式请求并释放动画帧，
 * 防止页面切换后仍更新旧页面状态。
 */
onBeforeUnmount(() => {
  abortController.value?.abort()

  if (scrollFrameId !== null) {
    window.cancelAnimationFrame(scrollFrameId)
    scrollFrameId = null
  }
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


              <template
                v-if="
                editingConversationId !== item.id
                "
              >

                <span>
                  {{ item.title }}
                </span>


                <span class="conversation-actions">

                  <a-button
                    type="text"
                    size="small"
                    @click.stop="
                    startEditConversation(item)
                    "
                  >
                    编辑
                  </a-button>


                  <a-button
                    danger
                    type="text"
                    size="small"
                    @click.stop="
                    removeConversation(item)
                    "
                  >
                    删除
                  </a-button>


                </span>

              </template>



              <template v-else>


                <a-input
                  v-model:value="
                    editingTitle
                  "
                  size="small"
                  @pressEnter="
                    saveConversationTitle(item)
                  "
                />


              </template>


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
          功能中心
        </div>

        <!-- 我的知识库 -->
        <a-card
          size="small"
          :bordered="false"
          class="feature-card knowledge-card"
          hoverable
          @click="router.push('/knowledge')"
        >
          <a-space>
            <FileTextOutlined />

            <span>
              我的知识库
            </span>
          </a-space>

          <div class="feature-description">
            管理你的学习资料和知识文档
          </div>
        </a-card>

        <!-- 我的简历 -->
        <a-card
          size="small"
          :bordered="false"
          class="feature-card resume-card"
          hoverable
        @click="router.push('/resume')"
        >
          <a-space>
            <ProfileOutlined />

            <span>
              我的简历
            </span>
          </a-space>

          <div class="feature-description">
            AI 解析项目、技能和实习经历
          </div>
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

        <a-dropdown placement="bottomRight">
          <div class="user-menu">
            <span class="username">
              {{ userStore.user?.username || '用户' }}
            </span>

            <span class="arrow">
              ▼
            </span>
          </div>

          <template #overlay>
            <a-menu>
              <a-menu-item key="user" disabled>
                当前用户：
                {{ userStore.user?.username || '用户' }}
              </a-menu-item>

              <a-menu-divider />

              <a-menu-item
                key="logout"
                @click="handleLogout"
              >
                退出登录
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

        <!-- <a-button
          type="text"
          :disabled="
            loading ||
            !messages.length
          "
          @click="clearChat"
        >
          清空对话
        </a-button> -->
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
            <!-- 空状态：从静态空页面改为可直接开始的任务入口。 -->
            <div
              v-if="!messages.length"
              class="empty-chat"
            >
              <div class="empty-mark">✦</div>
              <h1>今天想学习什么？</h1>
              <p>从你的知识库、简历和项目资料中开始一段对话。</p>

              <div class="starter-grid">
                <button
                  v-for="prompt in starterPrompts"
                  :key="prompt"
                  type="button"
                  class="starter-card"
                  @click="sendStarterPrompt(prompt)"
                >
                  <span>{{ prompt }}</span>
                  <ArrowUpOutlined />
                </button>
              </div>
            </div>

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

                  <!-- 【微交互】让流式等待过程有持续反馈，而不是静态空白。 -->
                  <div
                    v-if="
                      loading &&
                      currentAssistantId === item.id
                    "
                    class="stream-status"
                    aria-live="polite"
                  >
                    <span class="stream-dots">
                      <i></i><i></i><i></i>
                    </span>
                    AI 正在生成回答
                  </div>

                  <!-- 【新增】中断后保留当前内容，并给出明确的恢复操作。 -->
                  <div
                    v-if="item.interrupted"
                    class="interrupted-hint"
                  >
                    <span>回答已停止</span>
                    <a-button
                      type="link"
                      size="small"
                      @click="regenerate(index)"
                    >
                      重新生成
                    </a-button>
                  </div>

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
/* =========================
   页面整体
   ========================= */

.chat-page {
  height: 100vh;
  overflow: hidden;
  background: #f7f8fa;
}

/* =========================
   左侧 Sidebar
   ========================= */

.chat-sider {
  background: #ffffff !important;
  border-right: 1px solid #e8eaed;
}

.sider-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px 14px;
  overflow-y: auto;
}

/* 品牌 */

.brand {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 2px 6px 20px;
  color: #1f2329;
  font-size: 16px;
  font-weight: 600;
}

.brand :deep(.anticon) {
  color: #1677ff;
  font-size: 19px;
}

/* 新建对话 */

.new-chat-button {
  height: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgb(22 119 255 / 12%);
}

/* 分割线 */

.chat-sider :deep(.ant-divider) {
  margin: 16px 0;
  border-color: #f0f1f3;
}

/* Sidebar 标题 */

.sider-title {
  margin: 0 6px 8px;
  color: #86909c;
  font-size: 12px;
  font-weight: 500;
}

/* =========================
   历史会话
   ========================= */

.conversation-list {
  margin-bottom: 0;
  overflow-y: auto;
}

.conversation-item {
  display: block;
  padding: 9px 10px !important;
  border: none !important;
  border-radius: 8px;
  cursor: pointer;
  transition:
    background-color 0.18s ease,
    color 0.18s ease;
}

.conversation-item:hover {
  background: #f2f5f9;
}

.conversation-item-active {
  background: #e8f3ff;
}

.conversation-item-active:hover {
  background: #e8f3ff;
}

.conversation-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  color: #4e5969;
  font-size: 13px;
  line-height: 20px;
}

.conversation-title > span:first-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-title .ant-input {
  border-radius: 6px;
}

.conversation-actions {
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
  gap: 2px;
  margin-left: 6px;
  opacity: 0;
  transition: opacity 0.18s ease;
}

.conversation-item:hover .conversation-actions,
.conversation-item-active .conversation-actions {
  opacity: 1;
}

.conversation-actions :deep(.ant-btn) {
  height: 24px;
  padding: 0 5px;
  color: #86909c;
  font-size: 12px;
}

.conversation-actions :deep(.ant-btn:hover) {
  color: #1677ff;
  background: rgb(22 119 255 / 6%);
}

.conversation-actions :deep(.ant-btn-dangerous:hover) {
  color: #ff4d4f;
  background: rgb(255 77 79 / 6%);
}

.conversation-empty {
  margin: 16px 0;
}

/* =========================
   功能中心
   ========================= */

.feature-card {
  margin-bottom: 8px;
  overflow: hidden;
  border: 1px solid transparent;
  border-radius: 9px;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease,
    transform 0.18s ease;
}

.feature-card :deep(.ant-card-body) {
  padding: 12px;
}

.feature-card:hover {
  transform: translateY(-1px);
  border-color: #d9e8fb;
  background: #f8fbff;
}

.feature-card .ant-space {
  color: #1f2329;
  font-size: 13px;
  font-weight: 500;
}

.feature-card :deep(.anticon) {
  color: #1677ff;
  font-size: 16px;
}

.knowledge-card,
.resume-card,
.interview-card {
  background: #f7f8fa;
}

.feature-description {
  margin-top: 2px;
  color: #86909c;
  font-size: 11px;
  line-height: 1.55;
}

/* Sidebar 提示 */

.sider-tip {
  margin: auto 4px 0;
  padding: 10px 2px 0;
  color: #a9aeb8;
  font-size: 11px;
  line-height: 1.6;
}

/* =========================
   Header
   ========================= */

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 28px;
  background: #ffffff;
  border-bottom: 1px solid #e8eaed;
  line-height: normal;
}

.header-title {
  color: #1f2329;
  font-size: 16px;
  font-weight: 600;
  line-height: 22px;
}

.header-subtitle {
  margin-top: 3px;
  color: #86909c;
  font-size: 12px;
  line-height: 18px;
}

.chat-header :deep(.ant-btn) {
  color: #86909c;
  border-radius: 6px;
}

.chat-header :deep(.ant-btn:hover) {
  color: #1677ff;
  background: #f2f7ff;
}

/* =========================
   内容区域
   ========================= */

.chat-content {
  position: relative;
  background: #f7f8fa;
}

.chat-scroll-container {
  position: relative;
  height: 100%;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.chat-scroll-container::-webkit-scrollbar {
  width: 6px;
}

.chat-scroll-container::-webkit-scrollbar-thumb {
  border-radius: 6px;
  background: #d9dce1;
}

.chat-scroll-container::-webkit-scrollbar-track {
  background: transparent;
}

.message-container {
  width: min(900px, calc(100% - 48px));
  margin: 0 auto;
  padding: 32px 0 24px;
}

/* =========================
   空状态
   ========================= */

.empty-chat {
  margin-top: 150px;
}

.empty-icon {
  color: #91bfff;
  font-size: 48px;
}

/* =========================
   消息
   ========================= */

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
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
  width: 32px;
  height: 32px;
}

.user-avatar {
  background: #1677ff;
  box-shadow: 0 2px 6px rgb(22 119 255 / 18%);
}

.assistant-avatar {
  background: #5b6ee1;
  box-shadow: 0 2px 6px rgb(91 110 225 / 16%);
}

.message-main {
  max-width: calc(100% - 44px);
}

.user-main {
  display: flex;
  justify-content: flex-end;
  max-width: min(72%, calc(100% - 44px));
}

/* =========================
   用户消息
   ========================= */

.user-message {
  border: none;
  border-radius: 12px;
  background: #1677ff;
  box-shadow: 0 2px 6px rgb(22 119 255 / 10%);
}

.user-message :deep(.ant-card-body) {
  padding: 10px 14px;
}

.user-content {
  color: #ffffff;
  white-space: pre-wrap;
  line-height: 1.7;
}

/* =========================
   AI 消息
   ========================= */

.assistant-message {
  width: 100%;
  border: 1px solid #edf0f3;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 2px 8px rgb(31 35 41 / 3%);
}

.assistant-message :deep(.ant-card-body) {
  padding: 16px 18px;
}

.assistant-content {
  min-height: 24px;
  color: #1f2329;
  line-height: 1.8;
}

.generating {
  margin-top: 8px;
}

/* =========================
   Streaming Feedback
========================= */

.stream-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;

  margin-top: 10px;

  color: #86909c;
  font-size: 12px;
  line-height: 18px;

  animation: status-fade-in 0.2s ease both;
}

.interrupted-hint {
  display: flex;
  align-items: center;
  gap: 4px;

  margin-top: 10px;
  color: #8a8a8a;
  font-size: 12px;
}

.interrupted-hint :deep(.ant-btn-link) {
  height: auto;
  padding: 0 2px;
  color: #5b5ce2;
}

.stream-dots {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.stream-dots i {
  display: block;
  width: 4px;
  height: 4px;

  border-radius: 50%;
  background: #5b8ff9;

  animation: stream-dot 1s ease-in-out infinite;
}

.stream-dots i:nth-child(2) {
  animation-delay: 0.14s;
}

.stream-dots i:nth-child(3) {
  animation-delay: 0.28s;
}

@keyframes stream-dot {
  0%,
  60%,
  100% {
    opacity: 0.35;
    transform: translateY(0);
  }

  30% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

@keyframes status-fade-in {
  from {
    opacity: 0;
    transform: translateY(2px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .stream-status,
  .stream-dots i {
    animation: none;
  }
}

/* =========================
   AI 操作
   ========================= */

.message-actions {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #f2f3f5;
}

.message-actions :deep(.ant-btn) {
  height: 28px;
  padding: 0 8px;
  color: #86909c;
  border-radius: 6px;
  font-size: 12px;
}

.message-actions :deep(.ant-btn:hover) {
  color: #1677ff;
  background: #f2f7ff;
}

/* =========================
   Markdown
   ========================= */

.markdown-body {
  color: #1f2329;
}

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
  border: 1px solid #e8eaed;
  border-radius: 8px;
  background: #f7f8fa;
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
  background: #f2f3f5;
  color: #d4380d;
  font-size: 0.9em;
}

.markdown-body :deep(blockquote) {
  margin: 12px 0;
  padding: 8px 12px;
  border-left: 3px solid #91bfff;
  border-radius: 0 6px 6px 0;
  background: #f7faff;
  color: #667085;
}

/* =========================
   RAG 来源
   ========================= */

.source-wrapper {
  margin-top: 12px;
}

.source-wrapper :deep(.ant-divider) {
  margin: 14px 0 12px;
  border-color: #f0f1f3;
}

.source-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  color: #667085;
  font-size: 12px;
  font-weight: 500;
}

.source-title :deep(.anticon) {
  color: #1677ff;
}

.source-title :deep(.ant-tag) {
  margin-left: 2px;
  border-radius: 10px;
  font-size: 11px;
}

.source-collapse {
  margin-top: 4px;
}

.source-collapse :deep(.ant-collapse-header) {
  padding: 8px 4px !important;
  color: #667085 !important;
  font-size: 12px;
}

.source-card {
  border-radius: 8px;
  background: #f7f8fa;
}

.source-card :deep(.ant-card-body) {
  padding: 10px;
}

.source-score {
  color: #a9aeb8;
  font-size: 11px;
}

.source-content {
  color: #667085;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
}

/* =========================
   停止生成
   ========================= */

.stop-wrapper {
  display: flex;
  justify-content: center;
  margin: 8px 0 20px;
}

.stop-wrapper :deep(.ant-btn) {
  border-radius: 8px;
}

/* =========================
   回到底部
   ========================= */

.back-bottom-button {
  position: sticky;
  bottom: 20px;
  display: block;
  margin: 0 auto;
  border: 1px solid #e8eaed;
  background: #ffffff;
  box-shadow: 0 4px 12px rgb(31 35 41 / 10%);
}

.back-bottom-button:hover {
  color: #1677ff;
  border-color: #91bfff;
}

/* =========================
   输入区域
   ========================= */

.chat-footer {
  padding: 14px 24px 18px;
  background: #ffffff;
  border-top: 1px solid #e8eaed;
}

.input-wrapper {
  width: min(900px, 100%);
  margin: 0 auto;
  padding: 10px 12px 10px;
  border: 1px solid #d9dce1;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 4px 16px rgb(31 35 41 / 5%);
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.input-wrapper:focus-within {
  border-color: #91bfff;
  box-shadow:
    0 0 0 3px rgb(22 119 255 / 7%),
    0 4px 16px rgb(31 35 41 / 5%);
}

.input-wrapper :deep(.ant-input) {
  resize: none;
  padding: 4px 2px;
  border: none;
  box-shadow: none !important;
}

.input-wrapper :deep(.ant-input::placeholder) {
  color: #b2b7c2;
}

.input-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid #f5f6f7;
}

.input-tip {
  color: #a9aeb8;
  font-size: 11px;
}

.input-bottom :deep(.ant-btn) {
  min-width: 72px;
  height: 32px;
  border-radius: 7px;
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
    padding: 10px 12px 12px;
  }

  .message-main {
    max-width: calc(100% - 44px);
  }

  .user-main {
    max-width: calc(100% - 44px);
  }

  .input-tip {
    display: none;
  }

  .input-bottom {
    justify-content: flex-end;
  }
}
.user-menu {
  display: flex;
  align-items: center;
  gap: 6px;

  padding: 6px 10px;

  border-radius: 8px;

  cursor: pointer;

  transition: background 0.2s;
}

.user-menu:hover {
  background: #f5f7fa;
}

.username {
  max-width: 140px;

  overflow: hidden;

  text-overflow: ellipsis;

  white-space: nowrap;

  color: #1f2329;

  font-size: 13px;

  font-weight: 500;
}

.arrow {
  color: #86909c;
  font-size: 10px;
}
/* =========================
   Refined Chat Surface
========================= */

.chat-page {
  background: transparent;
}

.chat-sider {
  margin: 12px 0 12px 12px;
  overflow: hidden;
  border: 1px solid rgb(232 232 239 / 88%);
  border-radius: 18px;
  background: rgb(255 255 255 / 74%);
  box-shadow: 0 10px 30px rgb(30 30 58 / 4%);
  backdrop-filter: blur(16px);
}

.chat-header {
  margin: 12px 12px 0;
  border: 1px solid rgb(232 232 239 / 88%);
  border-radius: 18px;
  background: rgb(255 255 255 / 74%);
  box-shadow: 0 8px 24px rgb(30 30 58 / 3%);
  backdrop-filter: blur(16px);
}

.chat-content {
  margin: 0 12px 12px;
  border-radius: 18px;
  background: transparent;
}

.brand {
  letter-spacing: -0.3px;
}

.conversation-item {
  border: 1px solid transparent !important;
}

.conversation-item:hover {
  border-color: #e6e6fb !important;
  background: #f8f8ff;
  transform: translateX(2px);
}

.conversation-item-active,
.conversation-item-active:hover {
  border-color: #dfdfff !important;
  background: linear-gradient(135deg, #f0f0ff, #f7f7ff);
}

.feature-card {
  border-color: #ededf3;
  background: rgb(255 255 255 / 74%);
}

.feature-card:hover {
  border-color: #dcdcff;
  background: #fafaff;
  box-shadow: 0 10px 20px rgb(91 92 226 / 8%);
  transform: translateY(-2px);
}

.assistant-message {
  border: 1px solid #e9e9f0;
  box-shadow: 0 10px 28px rgb(30 30 58 / 4%);
}

.candidate-message .answer-content,
.user-message {
  background: linear-gradient(135deg, #5b5ce2, #7474eb);
}

.assistant-message:hover {
  border-color: #ddddef;
}

.input-wrapper {
  border-color: #e6e6ef;
  box-shadow: 0 8px 24px rgb(30 30 58 / 5%);
}

.input-wrapper:focus-within {
  border-color: #b8b8f2;
  box-shadow: 0 0 0 4px rgb(91 92 226 / 8%), 0 10px 26px rgb(30 30 58 / 6%);
}

@media (max-width: 768px) {
  .chat-sider {
    margin: 0;
    border: 0;
    border-radius: 0;
  }

  .chat-header,
  .chat-content {
    margin-right: 0;
    margin-left: 0;
    border-radius: 0;
    border-right: 0;
    border-left: 0;
  }
}
/* =========================================================
   Conversational workspace style
   借鉴现代对话应用的“低装饰、强聚焦”体验，不使用品牌资产。
========================================================= */

.chat-page {
  min-height: 100vh;
  background: #ffffff;
}

.chat-sider {
  margin: 0;
  border: 0;
  border-right: 1px solid #ececec;
  border-radius: 0;
  background: #f9f9f9 !important;
  box-shadow: none;
  backdrop-filter: none;
}

.sider-content {
  padding: 12px 10px;
}

.brand {
  gap: 9px;
  height: 38px;
  padding: 0 10px;
  color: #171717;
  font-size: 14px;
  font-weight: 600;
}

.brand :deep(.anticon) {
  display: grid;
  width: 26px;
  height: 26px;
  place-items: center;
  border-radius: 7px;
  color: #ffffff;
  background: #171717;
  font-size: 14px;
}

.new-chat-button {
  height: 38px !important;
  margin: 10px 0 14px;
  border-color: #e3e3e3 !important;
  border-radius: 9px !important;
  color: #242424 !important;
  background: #ffffff !important;
  box-shadow: none !important;
  font-size: 13px;
  font-weight: 500;
}

.new-chat-button::before {
  content: '+';
  margin-right: 7px;
  font-size: 17px;
  font-weight: 300;
  vertical-align: -1px;
}

.new-chat-button:hover {
  border-color: #d6d6d6 !important;
  background: #f3f3f3 !important;
}

.chat-sider :deep(.ant-divider) {
  margin: 8px 4px 14px;
  border-color: #e8e8e8;
}

.sider-title {
  padding: 0 10px 8px;
  color: #777777;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.conversation-item,
.conversation-item-active,
.conversation-item-active:hover {
  border: 0 !important;
  border-radius: 7px;
  background: transparent;
  box-shadow: none;
  transform: none;
}

.conversation-item:hover,
.conversation-item-active,
.conversation-item-active:hover {
  background: #ececec;
}

.conversation-title {
  font-size: 13px;
}

.feature-card {
  margin-bottom: 3px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  box-shadow: none;
}

.feature-card:hover {
  border: 0;
  background: #ececec;
  box-shadow: none;
  transform: none;
}

.feature-card :deep(.ant-card-body) {
  padding: 9px 10px;
}

.feature-card .ant-space {
  color: #393939;
  font-size: 13px;
  font-weight: 500;
}

.feature-card :deep(.anticon) {
  color: #575757;
  font-size: 15px;
}

.feature-description,
.sider-tip {
  color: #8a8a8a;
  font-size: 11px;
}

.chat-header {
  height: 56px;
  margin: 0;
  padding: 0 24px;
  border: 0;
  border-bottom: 1px solid #f0f0f0;
  border-radius: 0;
  background: #ffffff;
  box-shadow: none;
  backdrop-filter: none;
}

.header-title {
  color: #202020;
  font-size: 14px;
  font-weight: 600;
}

.header-subtitle {
  display: none;
}

.user-menu {
  padding: 6px 8px;
  border-radius: 7px;
}

.user-menu:hover {
  background: #f4f4f4;
}

.chat-content {
  margin: 0;
  border-radius: 0;
  background: #ffffff;
}

.message-container {
  width: min(820px, calc(100% - 40px));
  padding: 38px 0 24px;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: min(54vh, 460px);
  margin: 0;
  padding: 30px 0;
}

.empty-mark {
  display: grid;
  width: 34px;
  height: 34px;
  margin-bottom: 18px;
  place-items: center;
  border-radius: 10px;
  color: #ffffff;
  background: #202020;
  font-size: 18px;
}

.empty-chat h1 {
  margin: 0;
  color: #202020;
  font-size: clamp(26px, 3vw, 34px);
  font-weight: 600;
  letter-spacing: -0.04em;
}

.empty-chat p {
  margin: 10px 0 26px;
  color: #777777;
  font-size: 14px;
}

.starter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  width: min(640px, 100%);
  gap: 10px;
}

.starter-card {
  display: flex;
  min-height: 72px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 15px;
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  color: #373737;
  background: #ffffff;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
  transition: border-color 0.16s ease, background-color 0.16s ease, transform 0.16s ease;
}

.starter-card :deep(.anticon) {
  flex: 0 0 auto;
  color: #949494;
}

.starter-card:hover {
  border-color: #cfcfcf;
  background: #f8f8f8;
  transform: translateY(-1px);
}

.starter-card:active {
  transform: translateY(0) scale(0.99);
}

.message-row {
  gap: 12px;
  margin-bottom: 28px;
}

.avatar {
  width: 28px;
  height: 28px;
}

.assistant-avatar {
  color: #ffffff;
  background: #202020;
  box-shadow: none;
}

.user-avatar {
  color: #ffffff;
  background: #777777;
  box-shadow: none;
}

.message-main {
  max-width: calc(100% - 40px);
}

.assistant-message,
.assistant-message:hover {
  border: 0;
  background: transparent;
  box-shadow: none;
}

.assistant-message :deep(.ant-card-body) {
  padding: 2px 0;
}

.assistant-content {
  color: #252525;
  font-size: 15px;
  line-height: 1.85;
}

.user-message,
.candidate-message .answer-content {
  border: 0;
  border-radius: 18px;
  background: #f2f2f2;
  box-shadow: none;
}

.user-message :deep(.ant-card-body) {
  padding: 10px 14px;
}

.user-content {
  color: #2c2c2c;
  font-size: 14px;
  line-height: 1.65;
}

.message-actions {
  opacity: 0;
  transition: opacity 0.16s ease;
}

.message-row:hover .message-actions {
  opacity: 1;
}

.chat-footer {
  padding: 12px 24px 18px;
  background: #ffffff;
}

.input-wrapper {
  width: min(780px, 100%);
  padding: 10px 12px 8px;
  border: 1px solid #dedede;
  border-radius: 22px;
  background: #ffffff;
  box-shadow: 0 4px 18px rgb(0 0 0 / 7%);
}

.input-wrapper:focus-within {
  border-color: #c9c9c9;
  box-shadow: 0 5px 20px rgb(0 0 0 / 10%);
}

.input-bottom {
  padding-top: 7px;
  border-top: 0;
}

.input-tip {
  color: #969696;
}

.input-bottom :deep(.ant-btn-primary) {
  display: grid;
  width: 32px;
  min-width: 32px;
  height: 32px;
  padding: 0;
  place-items: center;
  border-radius: 50%;
  background: #202020;
  box-shadow: none;
}

.input-bottom :deep(.ant-btn-primary:hover) {
  background: #373737;
  box-shadow: none;
}

.input-bottom :deep(.ant-btn-primary:not(:disabled) .anticon) {
  margin: 0;
}

.input-bottom :deep(.ant-btn-primary) {
  font-size: 0;
}

.input-bottom :deep(.ant-btn-primary .anticon) {
  font-size: 14px;
}

@media (max-width: 768px) {
  .chat-header {
    padding: 0 16px;
  }

  .message-container {
    width: min(100% - 24px, 820px);
    padding-top: 24px;
  }

  .empty-chat {
    min-height: 48vh;
  }

  .starter-grid {
    grid-template-columns: 1fr;
  }

  .chat-footer {
    padding: 10px 12px 14px;
  }

  .input-wrapper {
    border-radius: 18px;
  }
}
</style>
