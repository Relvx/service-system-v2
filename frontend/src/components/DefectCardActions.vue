<template>
  <section class="pt-3 border-t space-y-3">
    <div v-if="canManage" class="flex items-center justify-between">
      <h3 class="font-semibold text-gray-800">Редактирование</h3>
      <button v-if="!editing" class="btn btn-secondary text-xs" @click="startEdit">Редактировать дефект</button>
    </div>
    <form v-if="editing" class="space-y-3 bg-gray-50 rounded-lg p-4" @submit.prevent="saveEdit">
      <label class="block">Название<input v-model="form.title" class="input mt-1" required /></label>
      <label class="block">Описание<textarea v-model="form.description" class="input mt-1" rows="4" /></label>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label>Приоритет<select v-model="form.priority" class="input mt-1"><option v-for="p in cfg.priorities" :key="p.sysname" :value="p.sysname">{{ p.display_name }}</option></select></label>
        <label>Тип действия<select v-model="form.action_type" class="input mt-1"><option v-for="a in cfg.defectActionTypes" :key="a.sysname" :value="a.sysname">{{ a.display_name }}</option></select></label>
      </div>
      <label class="block">Необходимые запчасти<textarea v-model="form.suggested_parts" class="input mt-1" rows="2" /></label>
      <p v-if="editError" role="alert" class="text-red-600">{{ editError }}</p>
      <div class="flex justify-end gap-2">
        <button type="button" class="btn btn-secondary" :disabled="saving" @click="editing = false">Отмена</button>
        <button class="btn btn-primary" :disabled="saving">{{ saving ? 'Сохранение…' : 'Сохранить изменения' }}</button>
      </div>
    </form>
    <div class="pt-3 border-t space-y-3">
      <h3 class="font-semibold text-gray-800">Комментарии</h3>
      <p v-if="loading" class="text-gray-400">Загрузка комментариев…</p>
      <p v-else-if="!comments.length && !loadError" class="text-gray-400">Комментариев пока нет</p>
      <div v-for="comment in comments" :key="comment.id" class="bg-gray-50 rounded-lg p-3">
        <div class="flex flex-wrap justify-between gap-1 text-xs text-gray-500 mb-2">
          <span class="font-medium text-gray-700">{{ comment.author_name }}</span>
          <span>{{ new Date(comment.created_at).toLocaleString('ru-RU') }}</span>
        </div>
        <p class="whitespace-pre-wrap break-words">{{ comment.text }}</p>
      </div>
      <p v-if="loadError" role="alert" class="text-red-600">{{ loadError }} <button class="underline" @click="loadComments(defect.id)">Повторить</button></p>
      <form v-if="canManage" class="space-y-2" @submit.prevent="postComment">
        <label class="block">Новый комментарий<textarea v-model="commentText" class="input mt-1" rows="3" maxlength="10000" placeholder="Например: согласовано с клиентом, ожидаем запчасти" required /></label>
        <p v-if="commentError" role="alert" class="text-red-600">{{ commentError }}</p>
        <button class="btn btn-primary" :disabled="posting || loading || !!loadError || !commentText.trim()">{{ posting ? 'Добавление…' : 'Добавить комментарий' }}</button>
      </form>
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useConfigStore } from '../stores/config.js'
import { defectsAPI } from '../services/api.js'
const props = defineProps({ defect: { type: Object, required: true }, canManage: Boolean })
const emit = defineEmits(['updated'])
const cfg = useConfigStore()
const editing = ref(false)
const form = ref({})
const saving = ref(false)
const editError = ref('')
const comments = ref([])
const loading = ref(false)
const loadError = ref('')
const commentText = ref('')
const commentError = ref('')
const posting = ref(false)
let generation = 0
watch(() => props.defect.id, (id) => {
  generation++
  editing.value = false
  editError.value = ''
  comments.value = []
  commentText.value = ''
  commentError.value = ''
  loadComments(id)
}, { immediate: true })
function startEdit() {
  const d = props.defect
  form.value = { title: d.title, description: d.description || '', priority: d.priority, action_type: d.action_type, suggested_parts: d.suggested_parts || '' }
  editError.value = ''
  editing.value = true
}
async function saveEdit() {
  if (!form.value.title.trim()) { editError.value = 'Введите название'; return }
  const id = props.defect.id
  saving.value = true
  editError.value = ''
  try {
    const { data } = await defectsAPI.update(id, { ...form.value, title: form.value.title.trim(), description: form.value.description.trim() || null, suggested_parts: form.value.suggested_parts.trim() || null })
    if (props.defect.id === id) { emit('updated', data); editing.value = false }
  } catch { if (props.defect.id === id) editError.value = 'Не удалось сохранить изменения. Попробуйте ещё раз.' }
  finally { saving.value = false }
}
async function loadComments(id) {
  const current = generation
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await defectsAPI.getComments(id)
    if (current === generation) comments.value = data
  } catch { if (current === generation) loadError.value = 'Не удалось загрузить комментарии.' }
  finally { if (current === generation) loading.value = false }
}
async function postComment() {
  const text = commentText.value.trim()
  if (!text || posting.value) return
  const id = props.defect.id
  posting.value = true
  commentError.value = ''
  try {
    const { data } = await defectsAPI.addComment(id, text)
    if (props.defect.id === id) {
      comments.value.push(data)
      commentText.value = ''
    }
  } catch { if (props.defect.id === id) commentError.value = 'Не удалось добавить комментарий. Попробуйте ещё раз.' }
  finally { posting.value = false }
}
</script>
