<template>
  <div>
    <!-- Upload button -->
    <div class="flex justify-end mb-4">
      <label class="cursor-pointer btn btn-primary flex items-center">
        <Upload class="w-4 h-4 mr-2" />
        {{ uploading ? 'Загрузка...' : 'Загрузить файл' }}
        <input
          type="file"
          accept="image/*,.pdf,.doc,.docx,.xls,.xlsx"
          class="hidden"
          :disabled="uploading"
          @change="handleFile"
        />
      </label>
    </div>

    <p v-if="uploadError" class="text-red-500 text-sm mb-3">{{ uploadError }}</p>

    <!-- Empty state -->
    <div v-if="!loading && attachments.length === 0" class="text-center py-12 card">
      <Paperclip class="w-12 h-12 text-gray-300 mx-auto mb-3" />
      <p class="text-gray-500">Файлы не прикреплены</p>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
    </div>

    <!-- File grid -->
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      <div
        v-for="att in attachments"
        :key="att.id"
        class="group relative border border-gray-200 rounded-lg overflow-hidden bg-white hover:shadow-md transition-shadow"
      >
        <!-- Image preview -->
        <a :href="att.file_url" target="_blank" class="block">
          <img
            v-if="isImage(att.file_url)"
            :src="att.file_url"
            class="w-full h-32 object-cover"
            :alt="att.file_name || 'Фото'"
          />
          <!-- Document icon -->
          <div v-else class="w-full h-32 flex flex-col items-center justify-center bg-gray-50">
            <FileText class="w-10 h-10 text-gray-400 mb-1" />
            <span class="text-xs text-gray-500 px-2 text-center truncate w-full">
              {{ att.file_name || fileExt(att.file_url) }}
            </span>
          </div>
        </a>

        <!-- File name + date -->
        <div class="p-2">
          <p class="text-xs text-gray-700 truncate">{{ att.file_name || fileExt(att.file_url) }}</p>
          <p class="text-xs text-gray-400">{{ formatDate(att.created_at) }}</p>
        </div>

        <!-- Delete button -->
        <button
          @click="confirmDelete(att)"
          class="absolute top-1 right-1 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
          title="Удалить"
        >
          <X class="w-3 h-3" />
        </button>
      </div>
    </div>

    <!-- Delete confirm dialog -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">Удалить файл?</h3>
        <p class="text-gray-600 text-sm mb-6">{{ deleteTarget.file_name || 'Файл' }} будет удалён безвозвратно.</p>
        <div class="flex justify-end gap-3">
          <button @click="deleteTarget = null" class="btn btn-secondary">Отмена</button>
          <button @click="handleDelete" class="btn bg-red-600 text-white hover:bg-red-700">Удалить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Upload, Paperclip, FileText, X } from 'lucide-vue-next'
import { attachmentsAPI } from '../services/api.js'

const props = defineProps({
  entityType: { type: String, required: true }, // 'client' | 'site'
  entityId: { type: [Number, String], required: true },
})

const attachments = ref([])
const loading = ref(true)
const uploading = ref(false)
const uploadError = ref('')
const deleteTarget = ref(null)

const CLOUD_NAME = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME
const UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET

async function loadAttachments() {
  loading.value = true
  try {
    const res =
      props.entityType === 'client'
        ? await attachmentsAPI.getByClient(props.entityId)
        : await attachmentsAPI.getBySite(props.entityId)
    attachments.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleFile(e) {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true
  uploadError.value = ''
  try {
    const isImg = file.type.startsWith('image/')
    const resourceType = isImg ? 'image' : 'raw'
    const form = new FormData()
    form.append('file', file)
    form.append('upload_preset', UPLOAD_PRESET)

    const res = await fetch(
      `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/${resourceType}/upload`,
      { method: 'POST', body: form }
    )
    const data = await res.json()
    if (!data.secure_url) throw new Error('Cloudinary error')

    await attachmentsAPI.upload({
      [props.entityType === 'client' ? 'client_id' : 'site_id']: Number(props.entityId),
      kind: isImg ? 'photo' : 'document',
      file_url: data.secure_url,
      file_name: file.name,
    })
    await loadAttachments()
  } catch {
    uploadError.value = 'Ошибка загрузки файла'
  } finally {
    uploading.value = false
    e.target.value = ''
  }
}

function confirmDelete(att) {
  deleteTarget.value = att
}

async function handleDelete() {
  try {
    await attachmentsAPI.delete(deleteTarget.value.id)
    deleteTarget.value = null
    await loadAttachments()
  } catch {
    deleteTarget.value = null
  }
}

function isImage(url) {
  return /\.(jpg|jpeg|png|gif|webp|svg)(\?|$)/i.test(url)
}

function fileExt(url) {
  const match = url.match(/\.([a-z0-9]+)(\?|$)/i)
  return match ? match[1].toUpperCase() + '-файл' : 'Файл'
}

function formatDate(dt) {
  return dt ? new Date(dt).toLocaleDateString('ru-RU') : ''
}

onMounted(loadAttachments)
</script>
