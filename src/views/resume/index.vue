<script setup lang="ts">
import {
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


const router = useRouter()

const resumes = ref<Resume[]>([])

const currentResume = ref<Resume | null>(null)

const uploading = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)


const loadResumes = async () => {
  try {
    resumes.value = await getResumes()

    if (resumes.value.length) {
      currentResume.value = resumes.value[0]
    }
  } catch (error) {
    console.error(error)
    message.error('获取简历失败')
  }
}


const selectFile = () => {
  fileInput.value?.click()
}


const handleFileChange = async (
  event: Event,
) => {
  const target =
    event.target as HTMLInputElement

  const file = target.files?.[0]

  if (!file) {
    return
  }

  if (file.type !== 'application/pdf') {
    message.error('目前只支持 PDF 文件')

    target.value = ''

    return
  }

  uploading.value = true

  try {
    const result = await uploadResume(file)

    message.success(
      '简历上传并解析成功',
    )

    const resume = result.resume

    resumes.value.unshift(resume)

    currentResume.value = resume
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
        currentResume.value.id,
    },
  })
}


onMounted(() => {
  loadResumes()
})
</script>


<template>
  <div class="resume-page">

    <!-- 顶部 -->
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

        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          hidden
          @change="handleFileChange"
        />

        <a-button
          type="primary"
          :loading="uploading"
          @click="selectFile"
        >
          上传简历
        </a-button>

        <a-button
          :disabled="!currentResume?.structured_data"
          @click="startInterview"
        >
          开始 AI 面试
        </a-button>

      </div>

    </div>


    <div
      v-if="currentResume"
      class="resume-content"
    >

      <!-- 左侧简历列表 -->
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
                  currentResume?.id === item.id,
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


      <!-- 右侧 -->
      <div class="resume-detail">

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


        <div
          v-if="
            currentResume.structured_data
          "
          class="resume-sections"
        >

          <!-- 基本信息 -->
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


          <!-- 技能 -->
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


          <!-- 教育 -->
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


          <!-- 项目 -->
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

              <div class="tag-list">

                <a-tag
                  v-for="
                    technology in project.technologies
                  "
                  :key="technology"
                >
                  {{ technology }}
                </a-tag>

              </div>

              <div
                v-if="
                  project.responsibilities.length
                "
                class="project-block"
              >

                <div class="block-title">
                  项目职责
                </div>

                <ul>
                  <li
                    v-for="
                      item in project.responsibilities
                    "
                    :key="item"
                  >
                    {{ item }}
                  </li>
                </ul>

              </div>

              <div
                v-if="
                  project.highlights.length
                "
                class="project-block"
              >

                <div class="block-title">
                  项目亮点
                </div>

                <ul>
                  <li
                    v-for="
                      item in project.highlights
                    "
                    :key="item"
                  >
                    {{ item }}
                  </li>
                </ul>

              </div>

            </a-card>

          </a-card>


          <!-- 实习 -->
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
                    item in internship.responsibilities
                  "
                  :key="item"
                >
                  {{ item }}
                </li>
              </ul>

            </a-card>

          </a-card>


          <!-- 自我评价 -->
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

        </div>

      </div>

    </div>


    <!-- 没有简历 -->
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
.resume-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

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

.resume-content {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

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

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

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

.empty-page {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>