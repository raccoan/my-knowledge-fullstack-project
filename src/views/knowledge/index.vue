<script setup lang="ts">
import {
  onMounted,
  ref,
} from 'vue'

import {
  message,
  Modal,
} from 'ant-design-vue'

import type {
  UploadProps,
} from 'ant-design-vue'

import {
  UploadOutlined,
  DeleteOutlined,
  FilePdfOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons-vue'

import {
  getFiles,
  getFileDetail,
  uploadFile,
  deleteFile,
} from '@/api/files'

import type {
  FileItem,
  FileDetail,
} from '@/api/files'

const files = ref<FileItem[]>([])
const loading = ref(false)
const uploadLoading = ref(false)
const deletingId = ref<number | null>(null)

const detailVisible = ref(false)
const detailLoading = ref(false)
const currentDetail = ref<FileDetail | null>(null)

const formatFileSize = (size: number | null) => {
  if (size === null || size === undefined) {
    return '-'
  }

  if (size < 1024) {
    return `${size} B`
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }

  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const formatDateTime = (value: string) => {
  if (!value) {
    return '-'
  }

  return new Date(value).toLocaleString('zh-CN')
}

const loadFiles = async () => {
  loading.value = true

  try {
    files.value = await getFiles()
  } catch (error) {
    message.error('获取知识库失败')
  } finally {
    loading.value = false
  }
}

const handleViewDetail = async (file: FileItem) => {
  detailVisible.value = true
  detailLoading.value = true
  currentDetail.value = null

  try {
    currentDetail.value = await getFileDetail(file.id)
  } catch (error) {
    message.error('获取文档详情失败')
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

const beforeUpload: UploadProps['beforeUpload'] = async (
  file,
) => {
  if (file.type !== 'application/pdf') {
    message.error('目前只支持 PDF 文件')
    return false
  }

  uploadLoading.value = true

  try {
    await uploadFile(file)

    message.success('上传成功')

    await loadFiles()
  } catch (error) {
    message.error('上传失败')
  } finally {
    uploadLoading.value = false
  }

  return false
}

const handleDelete = (file: FileItem) => {
  Modal.confirm({
    title: '确认删除？',
    content: `确定要删除「${file.filename}」吗？删除后无法恢复。`,
    okText: '删除',
    cancelText: '取消',
    okType: 'danger',

    async onOk() {
      deletingId.value = file.id

      try {
        await deleteFile(file.id)

        message.success('删除成功')

        await loadFiles()

        if (currentDetail.value?.id === file.id) {
          detailVisible.value = false
          currentDetail.value = null
        }
      } catch (error) {
        message.error('删除失败')
      } finally {
        deletingId.value = null
      }
    },
  })
}

onMounted(() => {
  loadFiles()
})
</script>

<template>
  <div class="knowledge-page">
    <a-card :bordered="false">
      <template #title>
        <div class="page-title">
          <div>
            <div class="title">
              我的知识库
            </div>

            <div class="description">
              上传你的 PDF 文档，让 AI 基于你的知识进行回答
            </div>
          </div>
        </div>
      </template>

      <template #extra>
        <a-space>
          <a-button
            :loading="loading"
            @click="loadFiles"
          >
            <template #icon>
              <ReloadOutlined />
            </template>

            刷新
          </a-button>

          <a-upload
            accept=".pdf,application/pdf"
            :show-upload-list="false"
            :before-upload="beforeUpload"
          >
            <a-button
              type="primary"
              :loading="uploadLoading"
            >
              <template #icon>
                <UploadOutlined />
              </template>

              上传 PDF
            </a-button>
          </a-upload>
        </a-space>
      </template>

      <a-spin :spinning="loading">
        <a-table
          :data-source="files"
          :pagination="false"
          row-key="id"
        >
          <a-table-column
            title="文件名称"
            key="filename"
          >
            <template #default="{ record }">
              <a-space>
                <FilePdfOutlined />

                <span>
                  {{ record.filename }}
                </span>
              </a-space>
            </template>
          </a-table-column>

          <a-table-column
            title="状态"
            key="status"
            width="120"
          >
            <template #default="{ record }">
              <a-tag
                v-if="record.status === 'completed'"
                color="success"
              >
                已完成
              </a-tag>

              <a-tag
                v-else-if="record.status === 'processing'"
                color="processing"
              >
                处理中
              </a-tag>

              <a-tag
                v-else
                color="error"
              >
                处理失败
              </a-tag>
            </template>
          </a-table-column>

          <a-table-column
            title="文件大小"
            key="file_size"
            width="120"
          >
            <template #default="{ record }">
              {{ formatFileSize(record.file_size) }}
            </template>
          </a-table-column>

          <a-table-column
            title="Chunk 数量"
            key="chunk_count"
            width="120"
          >
            <template #default="{ record }">
              {{ record.chunk_count }}
            </template>
          </a-table-column>

          <a-table-column
            title="上传时间"
            key="created_at"
            width="180"
          >
            <template #default="{ record }">
              {{ formatDateTime(record.created_at) }}
            </template>
          </a-table-column>

          <a-table-column
            title="操作"
            key="action"
            width="180"
          >
            <template #default="{ record }">
              <a-space>
                <a-button
                  type="link"
                  @click="handleViewDetail(record)"
                >
                  <template #icon>
                    <EyeOutlined />
                  </template>

                  查看
                </a-button>

                <a-popconfirm
                  title="确定删除这个文件吗？"
                  ok-text="删除"
                  cancel-text="取消"
                  @confirm="handleDelete(record)"
                >
                  <a-button
                    type="link"
                    danger
                    :loading="deletingId === record.id"
                  >
                    <template #icon>
                      <DeleteOutlined />
                    </template>

                    删除
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table-column>

          <template #emptyText>
            <a-empty description="知识库暂无文件" />
          </template>
        </a-table>
      </a-spin>
    </a-card>

    <!-- 文档详情 -->
    <a-drawer
      v-model:open="detailVisible"
      title="文档详情"
      :width="720"
    >
      <a-spin :spinning="detailLoading">
        <template v-if="currentDetail">
          <a-descriptions
            bordered
            :column="2"
          >
            <a-descriptions-item label="文件名称">
              {{ currentDetail.filename }}
            </a-descriptions-item>

            <a-descriptions-item label="状态">
              <a-tag color="success">
                {{ currentDetail.status }}
              </a-tag>
            </a-descriptions-item>

            <a-descriptions-item label="文件大小">
              {{ formatFileSize(currentDetail.file_size) }}
            </a-descriptions-item>

            <a-descriptions-item label="Chunk 数量">
              {{ currentDetail.chunk_count }}
            </a-descriptions-item>

            <a-descriptions-item
              label="上传时间"
              :span="2"
            >
              {{ formatDateTime(currentDetail.created_at) }}
            </a-descriptions-item>
          </a-descriptions>

          <div class="chunk-title">
            知识片段
          </div>

          <a-list
            :data-source="currentDetail.chunks"
            bordered
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <div class="chunk-item">
                  <div class="chunk-header">
                    <a-tag>
                      Chunk {{ item.chunk_index + 1 }}
                    </a-tag>

                    <span>
                      ID: {{ item.id }}
                    </span>
                  </div>

                  <div class="chunk-content">
                    {{ item.content }}
                  </div>
                </div>
              </a-list-item>
            </template>
          </a-list>
        </template>
      </a-spin>
    </a-drawer>
  </div>
</template>

<style scoped>
.knowledge-page {
  padding: 24px;
}

.page-title {
  display: flex;
  align-items: center;
}

.title {
  font-size: 20px;
  font-weight: 600;
}

.description {
  margin-top: 6px;
  color: #999;
  font-size: 14px;
}

.chunk-title {
  margin: 24px 0 12px;
  font-size: 16px;
  font-weight: 600;
}

.chunk-item {
  width: 100%;
}

.chunk-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #999;
  font-size: 12px;
}

.chunk-content {
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>