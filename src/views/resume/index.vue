<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
} from 'vue'

import {
  message,
} from 'ant-design-vue'

import {
  uploadResume,
  getResumes,
  type Resume,
} from '@/api/resumes'

import {
  useRouter,
} from 'vue-router'

import {
  getInterviews,
  updateInterviewTitle,
  deleteInterview,
} from '@/api/interviews'

import type {
  InterviewListItem,
} from '@/api/interviews'


const router = useRouter()


/**
 * =========================
 * 简历
 * =========================
 */

const resumes = ref<Resume[]>([])

const currentResume = ref<Resume | null>(null)

const uploading = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)


/**
 * 获取简历列表
 */
const loadResumes = async () => {
  try {
    resumes.value = await getResumes()

    if (resumes.value.length) {
      currentResume.value = resumes.value[0]
    }
  } catch (error) {
    console.error(error)

    message.error(
      '获取简历失败',
    )
  }
}


/**
 * 点击上传按钮
 */
const selectFile = () => {
  fileInput.value?.click()
}


/**
 * 上传简历
 */
const handleFileChange = async (
  event: Event,
) => {
  const target =
    event.target as HTMLInputElement

  const file =
    target.files?.[0]

  if (!file) {
    return
  }

  /**
   * 目前只支持 PDF
   */
  if (file.type !== 'application/pdf') {
    message.error(
      '目前只支持 PDF 文件',
    )

    target.value = ''

    return
  }

  uploading.value = true

  try {
    const result =
      await uploadResume(file)

    message.success(
      '简历上传并解析成功',
    )

    const resume =
      result.resume

    /**
     * 添加到简历列表顶部
     */
    resumes.value.unshift(resume)

    /**
     * 自动选中新上传的简历
     */
    currentResume.value =
      resume
  } catch (error) {
    console.error(error)

    message.error(
      '简历上传失败',
    )
  } finally {
    uploading.value = false

    target.value = ''
  }
}


/**
 * =========================
 * AI 面试
 * =========================
 */

/**
 * 当前用户所有面试记录
 */
const interviews =
  ref<InterviewListItem[]>([])


// 当前编辑的面试id
const editId = ref<number | null>(null)

// 编辑标题内容
const editTitle = ref<string>('')


/**
 * 加载历史面试
 */
const loadInterviews = async () => {
  try {
    const data =
      await getInterviews()

    interviews.value =
      data
  } catch (error) {
    console.error(
      '获取历史面试失败:',
      error,
    )
  }
}


/**
 * 当前简历对应的历史面试
 *
 * 比如：
 *
 * 当前简历 ID = 1
 *
 * 那么这里只显示：
 *
 * interview.resume_id === 1
 */
const currentResumeInterviews =
  computed(() => {
    if (!currentResume.value) {
      return []
    }

    return interviews.value.filter(
      interview =>
        interview.resume_id ===
        currentResume.value!.id,
    )
  })


/**
 * 开始新的 AI 面试
 */
const startInterview = () => {
  if (!currentResume.value) {
    message.warning(
      '请先上传简历',
    )

    return
  }

  if (!currentResume.value.structured_data) {
    message.warning(
      '该简历还没有完成 AI 解析',
    )

    return
  }

  router.push({
    path: '/interview',
    query: {
      resumeId:
        String(
          currentResume.value.id,
        ),
    },
  })
}


/**
 * 根据指定简历开始新的 AI 面试
 */
const startNewInterview = (
  resumeId: number,
) => {
  router.push({
    path: '/interview',
    query: {
      resumeId:
        String(resumeId),
    },
  })
}


/**
 * 查看 / 继续历史面试
 */
const openInterview = (
  interview: InterviewListItem,
) => {
  router.push({
    path: '/interview',
    query: {
      id:
        String(interview.id),
    },
  })
}


/**
 * 格式化面试时间
 */
const formatInterviewTime = (
  time: string,
) => {
  if (!time) {
    return '-'
  }

  return new Date(
    time,
  ).toLocaleString(
    'zh-CN',
    {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    },
  )
}


/**
 * 获取面试状态文字
 */
const getInterviewStatusText = (
  status: string,
) => {
  if (status === 'finished') {
    return '已完成'
  }

  return '进行中'
}

// 修改标题函数
const startEditTitle = (
  item: any
) => {

  editId.value = item.id

  editTitle.value =
    item.title ||
    `AI 模拟面试 #${item.id}`

}

// 保存标题函数
const saveTitle = async (item: any) => {
  if (!editTitle.value.trim()) {
    message.error('标题不能为空')
    return
  }

  try {
    await updateInterviewTitle(item.id, editTitle.value)
    item.title = editTitle.value
    message.success('标题更新成功')
  } catch (error) {
    console.error(error)
    message.error('标题更新失败')
  } finally {
    editId.value = null
  }
}

// 删除面试函数
const removeInterview = async (
  item: any
) => {

  try {

    await deleteInterview(item.id)


    // 删除本地数据
    const index =
      interviews.value.findIndex(
        interview =>
          interview.id === item.id
      )


    if (index !== -1) {
      interviews.value.splice(
        index,
        1
      )
    }


    message.success(
      '面试删除成功'
    )


  } catch(error){

    console.error(
      '删除面试失败:',
      error
    )

    message.error(
      '面试删除失败'
    )
  }
}



onMounted(async () => {
  /**
   * 获取简历
   */
  await loadResumes()

  /**
   * 获取历史面试
   */
  await loadInterviews()
})
</script>


<template>
  <div class="resume-page">

    <!-- =========================
         顶部
    ========================== -->

    <div class="page-header">

      <div>
        <div class="page-title">
          我的简历
        </div>

        <div class="page-subtitle">
          上传简历后，AI 会自动提取你的项目、技能和经历
        </div>
      </div>


      <div class="header-actions">

        <!-- 隐藏文件选择框 -->
        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          hidden
          @change="handleFileChange"
        />


        <!-- 上传简历 -->
        <a-button
          type="primary"
          :loading="uploading"
          @click="selectFile"
        >
          上传简历
        </a-button>


        <!-- 开始 AI 面试 -->
        <a-button
          type="primary"
          :disabled="!currentResume"
          @click="startInterview"
        >
          开始 AI 面试
        </a-button>

      </div>

    </div>


    <!-- =========================
         有简历
    ========================== -->

    <div
      v-if="currentResume"
      class="resume-content"
    >

      <!-- =========================
           左侧简历列表
      ========================== -->

      <div class="resume-sidebar">

        <div class="sidebar-title">
          我的简历
        </div>


        <a-list
          size="small"
          :data-source="resumes"
        >

          <template #renderItem="{ item }">

            <a-list-item
              class="resume-item"
              :class="{
                active:
                  currentResume?.id ===
                  item.id,
              }"
              @click="
                currentResume = item
              "
            >

              <div class="resume-item-name">
                {{ item.filename }}
              </div>


              <div class="resume-item-time">
                {{
                  new Date(
                    item.created_at,
                  ).toLocaleDateString()
                }}
              </div>

            </a-list-item>

          </template>

        </a-list>

      </div>


      <!-- =========================
           右侧简历详情
      ========================== -->

      <div class="resume-detail">

        <!-- 简历标题 -->
        <div class="resume-title-row">

          <div>

            <div class="resume-title">
              {{ currentResume.filename }}
            </div>

            <a-tag color="green">
              AI 已解析
            </a-tag>

          </div>


          <a-button
            type="primary"
            @click="startInterview"
          >
            根据此简历开始面试
          </a-button>

        </div>


        <!-- =========================
             简历结构化内容
        ========================== -->

        <div
          v-if="
            currentResume.structured_data
          "
          class="resume-sections"
        >

          <!-- =========================
               基本信息
          ========================== -->

          <a-card
            title="基本信息"
            :bordered="false"
          >

            <a-descriptions
              :column="2"
              bordered
            >

              <a-descriptions-item label="姓名">
                {{
                  currentResume
                    .structured_data
                    .basic_info
                    .name
                }}
              </a-descriptions-item>


              <a-descriptions-item label="电话">
                {{
                  currentResume
                    .structured_data
                    .basic_info
                    .phone
                }}
              </a-descriptions-item>


              <a-descriptions-item label="邮箱">
                {{
                  currentResume
                    .structured_data
                    .basic_info
                    .email
                }}
              </a-descriptions-item>


              <a-descriptions-item label="所在地">
                {{
                  currentResume
                    .structured_data
                    .basic_info
                    .location
                }}
              </a-descriptions-item>

            </a-descriptions>

          </a-card>


          <!-- =========================
               技能
          ========================== -->

          <a-card
            title="技能"
            :bordered="false"
          >

            <div class="tag-list">

              <a-tag
                v-for="
                  skill in currentResume
                    .structured_data
                    .skills
                "
                :key="skill"
              >
                {{ skill }}
              </a-tag>

            </div>

          </a-card>


          <!-- =========================
               教育经历
          ========================== -->

          <a-card
            title="教育经历"
            :bordered="false"
          >

            <a-list
              :data-source="
                currentResume
                  .structured_data
                  .education
              "
            >

              <template #renderItem="{ item }">

                <a-list-item>

                  <a-list-item-meta>

                    <template #title>
                      {{ item.school }}
                    </template>


                    <template #description>

                      {{ item.major }}

                      ·

                      {{ item.degree }}

                      ·

                      {{ item.start_date }}

                      -

                      {{ item.end_date }}

                    </template>

                  </a-list-item-meta>

                </a-list-item>

              </template>

            </a-list>

          </a-card>


          <!-- =========================
               项目经历
          ========================== -->

          <a-card
            title="项目经历"
            :bordered="false"
          >

            <a-card
              v-for="
                project in currentResume
                  .structured_data
                  .projects
              "
              :key="project.name"
              class="project-card"
            >

              <template #title>
                {{ project.name }}
              </template>


              <p>
                {{ project.description }}
              </p>


              <!-- 技术栈 -->
              <div class="tag-list">

                <a-tag
                  v-for="
                    technology in project
                      .technologies
                  "
                  :key="technology"
                >
                  {{ technology }}
                </a-tag>

              </div>


              <!-- 项目职责 -->
              <div
                v-if="
                  project
                    .responsibilities
                    .length
                "
                class="project-block"
              >

                <div class="block-title">
                  项目职责
                </div>


                <ul>

                  <li
                    v-for="
                      item in project
                        .responsibilities
                    "
                    :key="item"
                  >
                    {{ item }}
                  </li>

                </ul>

              </div>


              <!-- 项目亮点 -->
              <div
                v-if="
                  project
                    .highlights
                    .length
                "
                class="project-block"
              >

                <div class="block-title">
                  项目亮点
                </div>


                <ul>

                  <li
                    v-for="
                      item in project
                        .highlights
                    "
                    :key="item"
                  >
                    {{ item }}
                  </li>

                </ul>

              </div>

            </a-card>

          </a-card>


          <!-- =========================
               实习经历
          ========================== -->

          <a-card
            title="实习经历"
            :bordered="false"
          >

            <a-card
              v-for="
                internship in currentResume
                  .structured_data
                  .internships
              "
              :key="
                internship.company +
                internship.position
              "
              class="project-card"
            >

              <template #title>
                {{ internship.company }}
              </template>


              <div>
                {{ internship.position }}
              </div>


              <div class="time">

                {{ internship.start_date }}

                -

                {{ internship.end_date }}

              </div>


              <ul>

                <li
                  v-for="
                    item in internship
                      .responsibilities
                  "
                  :key="item"
                >
                  {{ item }}
                </li>

              </ul>

            </a-card>

          </a-card>


          <!-- =========================
               自我评价
          ========================== -->

          <a-card
            v-if="
              currentResume
                .structured_data
                .self_evaluation
            "
            title="自我评价"
            :bordered="false"
          >

            <p>
              {{
                currentResume
                  .structured_data
                  .self_evaluation
              }}
            </p>

          </a-card>


          <!-- =========================
               历史面试
          ========================== -->

          <a-card
            title="历史面试"
            :bordered="false"
            class="interview-history-card"
          >

            <!-- 右上角：开始新面试 -->
            <template #extra>

              <a-button
                type="primary"
                size="small"
                @click="
                  startNewInterview(
                    currentResume.id,
                  )
                "
              >
                开始新面试
              </a-button>

            </template>


            <!-- 没有历史面试 -->
            <a-empty
              v-if="
                currentResumeInterviews.length === 0
              "
              description="这份简历还没有面试记录"
            />


            <!-- 有历史面试 -->
            <div
              v-else
              class="interview-history-list"
            >

              <div
                v-for="
                  interview in currentResumeInterviews
                "
                :key="interview.id"
                class="interview-history-item"
              >

                <!-- 左侧信息 -->
                <div
                  class="interview-history-info"
                >


                  <!-- 编辑标题 -->
                  <template
                    v-if="editId === interview.id"
                  >

                    <a-input
                      v-model:value="editTitle"
                      size="small"
                      style="width:200px"
                      @pressEnter="
                        saveTitle(interview)
                      "
                    />


                    <a-button
                      type="link"
                      size="small"
                      @click="
                        saveTitle(interview)
                      "
                    >
                      保存
                    </a-button>


                    <a-button
                      type="link"
                      size="small"
                      danger
                      @click="
                        editId = null
                      "
                    >
                      取消
                    </a-button>


                  </template>



                  <!-- 正常显示标题 -->
                  <template
                    v-else
                  >

                    <div
                      class="interview-history-title"
                    >

                      {{ 
                        interview.title ||
                        `AI模拟面试 #${interview.id}`
                      }}


                    </div>


                  </template>



                  <div
                    class="interview-history-time"
                  >

                    {{
                      formatInterviewTime(
                        interview.created_at,
                      )
                    }}

                  </div>


                </div>


                <!-- 中间状态 / 分数 -->
                <div
                  class="interview-history-score"
                >

                  <!-- 已完成 -->
                  <template
                    v-if="
                      interview.status ===
                      'finished'
                    "
                  >

                    <span class="score">
                      {{ interview.total_score }}
                      分
                    </span>

                    <a-tag color="success">
                      {{
                        getInterviewStatusText(
                          interview.status,
                        )
                      }}
                    </a-tag>

                  </template>


                  <!-- 进行中 -->
                  <template v-else>

                    <a-tag
                      color="processing"
                    >
                      {{
                        getInterviewStatusText(
                          interview.status,
                        )
                      }}
                    </a-tag>

                  </template>

                </div>


                <!-- 右侧按钮 -->
                <div
                  class="interview-history-action"
                >


                  <!-- 修改标题 -->
                  <a-button
                    size="small"
                    type="link"
                    @click="
                      startEditTitle(interview)
                    "
                  >
                    修改标题
                  </a-button>



                  <!-- 打开面试 -->
                  <a-button
                    size="small"
                    type="link"
                    @click="
                      openInterview(interview)
                    "
                  >

                    {{
                      interview.status === 'ongoing'
                        ? '继续面试'
                        : '查看记录'
                    }}

                  </a-button>



                  <!-- 删除 -->
                  <a-popconfirm
                    title="确定删除这次面试吗？"
                    ok-text="删除"
                    cancel-text="取消"
                    @confirm="
                      removeInterview(interview)
                    "
                  >

                    <a-button
                      size="small"
                      type="link"
                      danger
                    >
                      删除
                    </a-button>


                  </a-popconfirm>


                </div>

              </div>

            </div>

          </a-card>

        </div>

      </div>

    </div>


    <!-- =========================
         没有简历
    ========================== -->

    <div
      v-else
      class="empty-page"
    >

      <a-empty
        description="还没有上传简历"
      >

        <a-button
          type="primary"
          :loading="uploading"
          @click="selectFile"
        >
          上传 PDF 简历
        </a-button>

      </a-empty>

    </div>

  </div>
</template>


<style scoped>
/* =========================
   页面
========================= */

.resume-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}


/* =========================
   顶部
========================= */

.page-header {
  min-height: 72px;
  padding: 0 24px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.page-subtitle {
  margin-top: 4px;
  color: #999;
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 12px;
}


/* =========================
   简历主体
========================= */

.resume-content {
  flex: 1;
  min-height: 0;

  display: flex;
  gap: 16px;

  padding: 16px;

  overflow: hidden;
}


/* =========================
   左侧简历列表
========================= */

.resume-sidebar {
  width: 240px;
  flex-shrink: 0;

  padding: 16px;

  background: #fff;
  border-radius: 10px;

  overflow-y: auto;
}

.sidebar-title {
  margin-bottom: 12px;
  font-weight: 600;
}

.resume-item {
  display: block;
  padding: 12px !important;

  cursor: pointer;

  border-radius: 6px;
}

.resume-item:hover {
  background: #f5f5f5;
}

.resume-item.active {
  background: #e6f4ff;
}

.resume-item-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resume-item-time {
  margin-top: 4px;
  color: #999;
  font-size: 12px;
}


/* =========================
   右侧简历
========================= */

.resume-detail {
  flex: 1;
  min-width: 0;

  overflow-y: auto;
}

.resume-title-row {
  margin-bottom: 16px;
  padding: 20px 24px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  background: #fff;
  border-radius: 10px;
}

.resume-title {
  margin-bottom: 8px;

  font-size: 18px;
  font-weight: 600;
}

.resume-sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
}


/* =========================
   标签
========================= */

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}


/* =========================
   项目
========================= */

.project-card {
  margin-bottom: 12px;
}

.project-block {
  margin-top: 16px;
}

.block-title {
  margin-bottom: 8px;
  font-weight: 600;
}

.time {
  margin-top: 4px;
  color: #999;
}


/* =========================
   历史面试
========================= */

.interview-history-card {
  margin-top: 0;
  border-radius: 10px;
}

.interview-history-list {
  display: flex;
  flex-direction: column;
}

.interview-history-item {
  display: flex;
  align-items: center;
  gap: 20px;

  padding: 16px 0;

  border-bottom: 1px solid #f0f0f0;
}

.interview-history-item:last-child {
  border-bottom: none;
}


/* 历史面试左侧 */

.interview-history-info {
  flex: 1;
  min-width: 0;
}

.interview-history-title {
  color: #262626;
  font-size: 14px;
  font-weight: 600;
}

.interview-history-time {
  margin-top: 5px;
  color: #8c8c8c;
  font-size: 12px;
}


/* 分数 */

.interview-history-score {
  display: flex;
  align-items: center;
  gap: 10px;
}

.score {
  color: #1677ff;
  font-size: 16px;
  font-weight: 600;
}


/* 操作 */

.interview-history-action {
  flex-shrink: 0;
}


/* =========================
   空状态
========================= */

.empty-page {
  flex: 1;

  display: flex;
  align-items: center;
  justify-content: center;
}


/* =========================
   响应式
========================= */

@media (max-width: 992px) {
  .resume-content {
    padding: 12px;
  }

  .resume-sidebar {
    width: 200px;
  }
}


@media (max-width: 768px) {

  .page-header {
    min-height: auto;
    padding: 12px 16px;

    align-items: flex-start;
    flex-direction: column;

    gap: 12px;
  }


  .header-actions {
    width: 100%;
  }


  .header-actions .ant-btn {
    flex: 1;
  }


  .resume-content {
    flex-direction: column;
    overflow-y: auto;
  }


  .resume-sidebar {
    width: 100%;
    max-height: 180px;
  }


  .resume-detail {
    overflow-y: visible;
  }


  .resume-title-row {
    padding: 16px;

    align-items: flex-start;
    flex-direction: column;

    gap: 12px;
  }


  .resume-title-row .ant-btn {
    width: 100%;
  }


  .interview-history-item {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }


  .interview-history-score {
    width: 100%;
  }


  .interview-history-action {
    width: 100%;
  }


  .interview-history-action .ant-btn {
    padding-left: 0;
  }

}
</style>