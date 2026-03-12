<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Задачи</h1>
          <p class="text-gray-600 mt-1">{{ tasks.length }} задач</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Создать задачу
        </button>
      </div>

      <!-- Filter tabs -->
      <div class="flex gap-2 mb-6">
        <button
          v-for="f in filters" :key="f.key"
          @click="activeFilter = f.key; loadTasks()"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="activeFilter === f.key ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'"
        >{{ f.label }}</button>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <div v-else-if="tasks.length === 0" class="text-center py-16 card">
        <CheckSquare class="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p class="text-gray-500">Задач нет</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="task in tasks" :key="task.id"
          class="card flex items-start gap-4 transition-opacity"
          :class="{ 'opacity-60': task.is_done }"
        >
          <!-- Done checkbox -->
          <button
            @click="toggleDone(task)"
            class="mt-0.5 flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors"
            :class="task.is_done ? 'bg-green-500 border-green-500 text-white' : 'border-gray-300 hover:border-primary-400'"
          >
            <Check v-if="task.is_done" class="w-3 h-3" />
          </button>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <p class="font-medium text-gray-900" :class="{ 'line-through text-gray-400': task.is_done }">{{ task.title }}</p>
            <p v-if="task.description" class="text-sm text-gray-500 mt-0.5 line-clamp-2">{{ task.description }}</p>
            <div class="flex items-center gap-4 mt-1.5 text-xs text-gray-400">
              <span v-if="task.deadline" :class="isOverdue(task) ? 'text-red-500 font-medium' : ''">
                <CalendarIcon class="w-3.5 h-3.5 inline mr-1" />{{ formatDate(task.deadline) }}
                <span v-if="isOverdue(task)"> — просрочено</span>
              </span>
              <span v-if="task.created_by_name">{{ task.created_by_name }}</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1 flex-shrink-0">
            <button @click="openFiles(task)" title="Файлы" class="p-1.5 text-gray-400 hover:text-primary-600 rounded">
              <Paperclip class="w-4 h-4" />
            </button>
            <button @click="openEdit(task)" title="Редактировать" class="p-1.5 text-gray-400 hover:text-primary-600 rounded">
              <Pencil class="w-4 h-4" />
            </button>
            <button @click="deleteConfirm = task" title="Удалить" class="p-1.5 text-gray-400 hover:text-red-600 rounded">
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- Create / Edit Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ editing ? 'Редактировать задачу' : 'Создать задачу' }}</h2>
            <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
              <input
                v-model="form.title"
                class="input"
                :class="{ 'border-red-400': errors.title }"
                placeholder="Что нужно сделать?"
                @input="delete errors.title"
              />
              <p v-if="errors.title" class="text-red-600 text-xs mt-1">{{ errors.title }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Описание</label>
              <textarea v-model="form.description" class="input" rows="3" placeholder="Подробности..." />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Дедлайн</label>
              <input v-model="form.deadline" type="date" class="input" />
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="modalOpen = false" class="btn btn-secondary">Отмена</button>
              <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
                {{ saving ? 'Сохранение...' : (editing ? 'Сохранить' : 'Создать') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Files Modal -->
      <div v-if="filesTask" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 flex flex-col max-h-[90vh]">
          <div class="flex items-center justify-between p-6 border-b flex-shrink-0">
            <h2 class="text-xl font-semibold text-gray-900">Файлы — {{ filesTask.title }}</h2>
            <button @click="filesTask = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <div class="p-6 overflow-y-auto flex-1">
            <AttachmentsTab entity-type="task" :entity-id="filesTask.id" />
          </div>
        </div>
      </div>

      <!-- Delete Confirm -->
      <div v-if="deleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Удалить задачу?</h2>
          <p class="text-gray-600 mb-6">«{{ deleteConfirm.title }}» будет удалена безвозвратно.</p>
          <div class="flex justify-end gap-3">
            <button @click="deleteConfirm = null" class="btn btn-secondary">Отмена</button>
            <button @click="handleDelete" class="btn bg-red-600 text-white hover:bg-red-700">Удалить</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, X, Check, CheckSquare, Pencil, Trash2, Paperclip, Calendar as CalendarIcon } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import AttachmentsTab from '../components/AttachmentsTab.vue'
import { tasksAPI } from '../services/api.js'

const tasks = ref([])
const loading = ref(true)
const activeFilter = ref('')
const modalOpen = ref(false)
const editing = ref(null)
const saving = ref(false)
const deleteConfirm = ref(null)
const filesTask = ref(null)
const form = ref({ title: '', description: '', deadline: '' })
const errors = ref({})

const filters = [
  { key: '',       label: 'Все' },
  { key: 'active', label: 'Активные' },
  { key: 'done',   label: 'Выполненные' },
]

async function loadTasks() {
  loading.value = true
  try {
    const params = activeFilter.value ? { filter: activeFilter.value } : {}
    const res = await tasksAPI.getAll(params)
    tasks.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = { title: '', description: '', deadline: '' }
  errors.value = {}
  modalOpen.value = true
}

function openEdit(task) {
  editing.value = task
  form.value = {
    title: task.title,
    description: task.description || '',
    deadline: task.deadline || '',
  }
  errors.value = {}
  modalOpen.value = true
}

function openFiles(task) {
  filesTask.value = task
}

async function handleSave() {
  if (!form.value.title.trim()) {
    errors.value = { title: 'Введите название' }
    return
  }
  saving.value = true
  try {
    const payload = {
      title: form.value.title.trim(),
      description: form.value.description || null,
      deadline: form.value.deadline || null,
    }
    if (editing.value) {
      await tasksAPI.update(editing.value.id, payload)
    } else {
      await tasksAPI.create(payload)
    }
    modalOpen.value = false
    await loadTasks()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function toggleDone(task) {
  try {
    await tasksAPI.update(task.id, { is_done: !task.is_done })
    await loadTasks()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleDelete() {
  try {
    await tasksAPI.delete(deleteConfirm.value.id)
    deleteConfirm.value = null
    await loadTasks()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

function isOverdue(task) {
  if (!task.deadline || task.is_done) return false
  return new Date(task.deadline + 'T00:00:00') < new Date(new Date().toDateString())
}

function formatDate(d) {
  return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—'
}

onMounted(loadTasks)
</script>
