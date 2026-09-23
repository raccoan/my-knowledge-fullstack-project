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

```css
<style scoped>
/* =========================
   Page
========================= */

.resume-page {
  height: 100%;
  min-height: 0;

  display: flex;
  flex-direction: column;

  background: #f7f8fa;
  color: #1f2329;
}

/* =========================
   Header
========================= */

.page-header {
  min-height: 64px;
  padding: 0 28px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  flex-shrink: 0;

  background: #ffffff;
  border-bottom: 1px solid #e8eaed;
}

.page-title {
  color: #1f2329;
  font-size: 16px;
  line-height: 22px;
  font-weight: 600;
}

.page-subtitle {
  margin-top: 3px;

  color: #86909c;
  font-size: 12px;
  line-height: 18px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions :deep(.ant-btn) {
  height: 34px;
  padding: 0 13px;

  border-radius: 7px;

  font-size: 12px;
}

.header-actions :deep(.ant-btn-primary) {
  box-shadow: 0 2px 6px rgb(22 119 255 / 12%);
}

.header-actions :deep(.ant-btn-primary:not(:first-child)) {
  background: #ffffff;
  color: #1677ff;
  border-color: #91bfff;
  box-shadow: none;
}

.header-actions :deep(.ant-btn-primary:not(:first-child):hover) {
  background: #f2f7ff;
}

/* =========================
   Main Content
========================= */

.resume-content {
  flex: 1;
  min-height: 0;

  display: flex;
  gap: 16px;

  padding: 20px 24px;

  overflow: hidden;
}

/* =========================
   Resume Sidebar
========================= */

.resume-sidebar {
  width: 240px;
  flex-shrink: 0;

  padding: 16px 12px;

  overflow-y: auto;

  background: #ffffff;
  border: 1px solid #edf0f3;
  border-radius: 12px;

  box-shadow: 0 2px 8px rgb(31 35 41 / 3%);
}

.resume-sidebar::-webkit-scrollbar {
  width: 5px;
}

.resume-sidebar::-webkit-scrollbar-thumb {
  border-radius: 5px;
  background: #d9dce1;
}

.resume-sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-title {
  padding: 0 8px;
  margin-bottom: 10px;

  color: #1f2329;
  font-size: 13px;
  font-weight: 600;
}

.resume-sidebar :deep(.ant-list) {
  background: transparent;
}

.resume-sidebar :deep(.ant-list-item) {
  border: none;
}

/* =========================
   Resume Item
========================= */

.resume-item {
  position: relative;

  display: block;

  padding: 10px 10px !important;
  margin-bottom: 3px;

  cursor: pointer;

  border: none !important;
  border-radius: 8px;

  transition:
    background-color 0.18s ease,
    color 0.18s ease;
}

.resume-item:hover {
  background: #f2f5f9;
}

.resume-item.active {
  background: #e8f3ff;
}

.resume-item.active::before {
  content: '';

  position: absolute;
  left: 0;
  top: 9px;
  bottom: 9px;

  width: 3px;

  background: #1677ff;
  border-radius: 0 3px 3px 0;
}

.resume-item-name {
  overflow: hidden;

  color: #4e5969;
  font-size: 12px;
  line-height: 20px;
  font-weight: 500;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.resume-item.active .resume-item-name {
  color: #1677ff;
  font-weight: 600;
}

.resume-item-time {
  margin-top: 2px;

  color: #a9aeb8;
  font-size: 10px;
  line-height: 16px;
}

/* =========================
   Resume Detail
========================= */

.resume-detail {
  flex: 1;
  min-width: 0;

  padding-right: 2px;

  overflow-y: auto;
}

.resume-detail::-webkit-scrollbar {
  width: 6px;
}

.resume-detail::-webkit-scrollbar-thumb {
  border-radius: 6px;
  background: #d9dce1;
}

.resume-detail::-webkit-scrollbar-track {
  background: transparent;
}

/* =========================
   Resume Title
========================= */

.resume-title-row {
  min-height: 72px;

  margin-bottom: 16px;
  padding: 16px 20px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  background: #ffffff;
  border: 1px solid #edf0f3;
  border-radius: 12px;

  box-shadow: 0 2px 8px rgb(31 35 41 / 3%);
}

.resume-title {
  max-width: 600px;

  margin-bottom: 6px;

  overflow: hidden;

  color: #1f2329;
  font-size: 15px;
  line-height: 22px;
  font-weight: 600;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.resume-title-row :deep(.ant-tag) {
  margin: 0;

  border-radius: 10px;

  font-size: 10px;
  line-height: 19px;
}

.resume-title-row > :deep(.ant-btn) {
  height: 34px;
  padding: 0 13px;

  flex-shrink: 0;

  border-radius: 7px;

  font-size: 12px;

  box-shadow: 0 2px 6px rgb(22 119 255 / 12%);
}

/* =========================
   Resume Sections
========================= */

.resume-sections {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.resume-sections > :deep(.ant-card) {
  overflow: hidden;

  border: 1px solid #edf0f3 !important;
  border-radius: 12px !important;

  background: #ffffff;

  box-shadow: 0 2px 8px rgb(31 35 41 / 3%);
}

.resume-sections > :deep(.ant-card) > .ant-card-head {
  min-height: 48px;
  padding: 0 18px;

  border-bottom: 1px solid #f0f1f3;
}

.resume-sections > :deep(.ant-card) > .ant-card-head .ant-card-head-title {
  padding: 14px 0;

  color: #1f2329;
  font-size: 13px;
  font-weight: 600;
}

.resume-sections > :deep(.ant-card) > .ant-card-body {
  padding: 18px;
}

/* =========================
   Basic Information
========================= */

.resume-sections :deep(.ant-descriptions) {
  overflow: hidden;

  border-radius: 8px;
}

.resume-sections :deep(.ant-descriptions-view) {
  border-color: #edf0f3;
}

.resume-sections :deep(.ant-descriptions-item-label) {
  width: 90px;

  color: #86909c;
  font-size: 12px;

  background: #fafbfc;
  border-color: #edf0f3;
}

.resume-sections :deep(.ant-descriptions-item-content) {
  color: #1f2329;
  font-size: 12px;

  background: #ffffff;
  border-color: #edf0f3;
}

/* =========================
   Tags
========================= */

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-list :deep(.ant-tag) {
  margin: 0;
  padding: 2px 9px;

  color: #4e5969;
  background: #f2f7ff;
  border-color: #d9eaff;
  border-radius: 6px;

  font-size: 11px;
  line-height: 20px;
}

/* =========================
   Education
========================= */

.resume-sections :deep(.ant-list-item) {
  padding: 12px 0;

  border-color: #f0f1f3;
}

.resume-sections :deep(.ant-list-item:last-child) {
  border-bottom: none;
}

.resume-sections :deep(.ant-list-item-meta-title) {
  margin-bottom: 3px !important;

  color: #1f2329;
  font-size: 13px;
  font-weight: 600;
}

.resume-sections :deep(.ant-list-item-meta-description) {
  color: #86909c;
  font-size: 11px;
  line-height: 18px;
}

/* =========================
   Project / Internship
========================= */

.project-card {
  margin-bottom: 10px !important;

  border: 1px solid #edf0f3 !important;
  border-radius: 9px !important;

  background: #fafbfc;

  box-shadow: none !important;
}

.project-card:last-child {
  margin-bottom: 0 !important;
}

.project-card :deep(.ant-card-head) {
  min-height: 42px !important;
  padding: 0 14px !important;

  border-bottom: 1px solid #f0f1f3 !important;
}

.project-card :deep(.ant-card-head-title) {
  padding: 11px 0 !important;

  color: #1f2329;
  font-size: 12px;
  font-weight: 600;
}

.project-card :deep(.ant-card-body) {
  padding: 14px !important;
}

.project-card p {
  margin: 0 0 12px;

  color: #4e5969;
  font-size: 12px;
  line-height: 1.8;
}

.project-block {
  margin-top: 14px;
}

.block-title {
  position: relative;

  padding-left: 9px;
  margin-bottom: 7px;

  color: #4e5969;
  font-size: 12px;
  font-weight: 600;
}

.block-title::before {
  content: '';

  position: absolute;
  left: 0;
  top: 4px;

  width: 3px;
  height: 12px;

  background: #1677ff;
  border-radius: 2px;
}

.project-block ul,
.project-card > ul {
  margin: 0;
  padding-left: 20px;

  color: #667085;
  font-size: 12px;
  line-height: 1.8;
}

.project-block li,
.project-card > ul li {
  padding-left: 2px;
}

.time {
  margin-top: 3px;

  color: #a9aeb8;
  font-size: 11px;
}

/* =========================
   Interview History
========================= */

.interview-history-card {
  margin-top: 0;
}

.interview-history-card :deep(.ant-card-extra) {
  padding: 0;
}

.interview-history-card :deep(.ant-card-extra .ant-btn) {
  height: 28px;
  padding: 0 10px;

  border-radius: 6px;

  font-size: 11px;
}

.interview-history-list {
  display: flex;
  flex-direction: column;
}

.interview-history-item {
  display: flex;
  align-items: center;
  gap: 18px;

  padding: 13px 0;

  border-bottom: 1px solid #f0f1f3;

  transition: background-color 0.18s ease;
}

.interview-history-item:last-child {
  border-bottom: none;
}

.interview-history-info {
  flex: 1;
  min-width: 0;
}

.interview-history-title {
  overflow: hidden;

  color: #1f2329;
  font-size: 12px;
  line-height: 20px;
  font-weight: 600;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.interview-history-time {
  margin-top: 2px;

  color: #a9aeb8;
  font-size: 10px;
}

.interview-history-score {
  display: flex;
  align-items: center;
  gap: 8px;

  flex-shrink: 0;
}

.score {
  color: #1677ff;
  font-size: 14px;
  font-weight: 600;
}

.interview-history-score :deep(.ant-tag) {
  margin: 0;

  border-radius: 10px;

  font-size: 10px;
}

.interview-history-action {
  display: flex;
  align-items: center;
  gap: 2px;

  flex-shrink: 0;
}

.interview-history-action :deep(.ant-btn) {
  height: 26px;
  padding: 0 5px;

  border-radius: 5px;

  font-size: 11px;
}

.interview-history-action :deep(.ant-btn-link:hover) {
  background: #f2f7ff;
}

.interview-history-action :deep(.ant-btn-dangerous:hover) {
  background: #fff2f0;
}

/* =========================
   Empty Page
========================= */

.empty-page {
  flex: 1;

  display: flex;
  align-items: center;
  justify-content: center;

  padding: 24px;
}

.empty-page :deep(.ant-empty-description) {
  color: #a9aeb8;
  font-size: 12px;
}

.empty-page :deep(.ant-btn) {
  height: 34px;
  padding: 0 14px;

  border-radius: 7px;

  font-size: 12px;

  box-shadow: 0 2px 6px rgb(22 119 255 / 12%);
}

/* =========================
   Responsive
========================= */

@media (max-width: 992px) {
  .resume-content {
    padding: 16px;
  }

  .resume-sidebar {
    width: 210px;
  }

  .resume-title-row {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .page-header {
    min-height: auto;
    padding: 12px 16px;

    align-items: flex-start;
    flex-direction: column;

    gap: 10px;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions :deep(.ant-btn) {
    flex: 1;
  }

  .resume-content {
    flex-direction: column;

    padding: 12px;

    overflow-y: auto;
  }

  .resume-sidebar {
    width: 100%;
    max-height: 170px;

    padding: 12px;
  }

  .resume-detail {
    padding-right: 0;

    overflow-y: visible;
  }

  .resume-title-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }

  .resume-title-row > :deep(.ant-btn) {
    width: 100%;
  }

  .resume-title {
    max-width: 100%;
  }

  .resume-sections > :deep(.ant-card) > .ant-card-body {
    padding: 14px;
  }

  .resume-sections :deep(.ant-descriptions) {
    overflow-x: auto;
  }

  .resume-sections :deep(.ant-descriptions-view) {
    min-width: 520px;
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
    flex-wrap: wrap;
  }

  .interview-history-action :deep(.ant-btn) {
    padding-left: 0;
  }
}
</style>
```
