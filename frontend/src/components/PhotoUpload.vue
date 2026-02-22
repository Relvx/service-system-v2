<template>
  <div>
    <label class="block text-sm font-medium text-gray-700 mb-1">{{ label }}</label>
    <div class="flex flex-wrap gap-2 mb-2">
      <div v-for="url in modelValue" :key="url" class="relative">
        <img :src="url" class="h-20 w-20 object-cover rounded-lg border border-gray-200" />
        <button
          type="button"
          @click="remove(url)"
          class="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600"
        >
          ×
        </button>
      </div>
    </div>
    <label class="cursor-pointer inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors">
      <Upload class="h-4 w-4 mr-2" />
      {{ uploading ? 'Загрузка...' : 'Загрузить фото' }}
      <input type="file" accept="image/*" class="hidden" :disabled="uploading" @change="handleFile" />
    </label>
    <p v-if="error" class="text-red-500 text-xs mt-1">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: { type: String, default: 'Фотографии' },
})
const emit = defineEmits(['update:modelValue'])

const uploading = ref(false)
const error = ref('')

const CLOUD_NAME = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME
const UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET

async function handleFile(e) {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true
  error.value = ''
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('upload_preset', UPLOAD_PRESET)
    const res = await fetch(`https://api.cloudinary.com/v1_1/${CLOUD_NAME}/image/upload`, {
      method: 'POST',
      body: form,
    })
    const data = await res.json()
    if (data.secure_url) {
      emit('update:modelValue', [...props.modelValue, data.secure_url])
    } else {
      error.value = 'Ошибка загрузки фото'
    }
  } catch {
    error.value = 'Ошибка загрузки фото'
  } finally {
    uploading.value = false
    e.target.value = ''
  }
}

function remove(url) {
  emit('update:modelValue', props.modelValue.filter((u) => u !== url))
}
</script>
