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
} from '@ant-design/icons-vue'

import {
  getFiles,
  uploadFile,
  deleteFile,
} from '@/api/files'

import type {
  FileItem,
} from '@/api/files'


const files = ref<FileItem[]>([])

const loading = ref(false)

const uploadLoading = ref(false)

const deletingId = ref<number | null>(null)


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
            title="文件类型"
            key="type"
            width="150"
          >
            <template #default>
              <a-tag color="red">
                PDF
              </a-tag>
            </template>
          </a-table-column>


          <a-table-column
            title="文件 ID"
            key="id"
            width="120"
          >
            <template #default="{ record }">
              {{ record.id }}
            </template>
          </a-table-column>


          <a-table-column
            title="操作"
            key="action"
            width="120"
          >
            <template #default="{ record }">
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
            </template>
          </a-table-column>


          <template #emptyText>
            <a-empty
              description="知识库暂无文件"
            />
          </template>
        </a-table>
      </a-spin>
    </a-card>
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
</style>