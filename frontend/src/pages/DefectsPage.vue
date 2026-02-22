<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Дефекты</h1>
          <p class="text-gray-600 mt-1">Всего: {{ defects.length }}</p>
        </div>
      </div>

      <!-- Filters -->
      <div class="card mb-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select v-model="filterStatus" @change="loadDefects" class="input">
            <option value="">Все статусы</option>
            <option v-for="s in cfg.defectStatuses" :key="s.code" :value="s.code">{{ s.display_name }}</option>
          </select>
          <select v-model="filterPriority" @change="loadDefects" class="input">
            <option value="">Все приоритеты</option>
            <option v-for="p in cfg.priorities" :key="p.code" :value="p.code">{{ p.display_name }}</option>
          </select>
          <button @click="loadDefects" class="btn btn-primary">Обновить</button>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <div v-else class="space-y-4">
        <div v-for="d in defects" :key="d.id" class="card hover:shadow-md transition-shadow cursor-pointer" @click="selectedDefect = d">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <AlertTriangle class="w-5 h-5 text-orange-500" />
                <h3 class="font-semibold text-gray-900">{{ d.title }}</h3>
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="defectStatusClass(d.status)">
                  {{ cfg.defectStatusLabel(d.status) }}
                </span>
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="priorityClass(d.priority)">
                  {{ cfg.priorityLabel(d.priority) }}
                </span>
              </div>
              <div class="text-sm text-gray-600 space-y-1">
                <div v-if="d.site_title" class="flex items-center"><Building2 class="w-4 h-4 mr-2" />{{ d.site_title }}</div>
                <div v-if="d.client_name" class="flex items-center"><Users class="w-4 h-4 mr-2" />{{ d.client_name }}</div>
                <div v-if="d.visit_date" class="flex items-center"><Calendar class="w-4 h-4 mr-2" />{{ formatDate(d.visit_date) }}</div>
              </div>
              <p v-if="d.description" class="mt-2 text-sm text-gray-600">{{ d.description }}</p>
            </div>
            <div class="ml-4 text-sm text-gray-500">{{ formatDate(d.created_at) }}</div>
          </div>
        </div>

        <div v-if="defects.length === 0" class="text-center py-12 card">
          <AlertTriangle class="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900">Дефекты не найдены</h3>
        </div>
      </div>

      <!-- Detail / Approve Modal -->
      <div v-if="selectedDefect" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ selectedDefect.title }}</h2>
            <button @click="selectedDefect = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <div class="p-6 space-y-3 text-sm">
            <div class="flex gap-2 mb-4">
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="defectStatusClass(selectedDefect.status)">{{ cfg.defectStatusLabel(selectedDefect.status) }}</span>
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="priorityClass(selectedDefect.priority)">{{ cfg.priorityLabel(selectedDefect.priority) }}</span>
            </div>
            <div v-if="selectedDefect.site_title"><p class="text-gray-500">Объект</p><p class="text-gray-900">{{ selectedDefect.site_title }}</p></div>
            <div v-if="selectedDefect.client_name"><p class="text-gray-500">Клиент</p><p class="text-gray-900">{{ selectedDefect.client_name }}</p></div>
            <div v-if="selectedDefect.visit_date"><p class="text-gray-500">Дата выезда</p><p class="text-gray-900">{{ formatDate(selectedDefect.visit_date) }}</p></div>
            <div v-if="selectedDefect.description"><p class="text-gray-500">Описание</p><p class="text-gray-900">{{ selectedDefect.description }}</p></div>
            <div><p class="text-gray-500">Тип действия</p><p class="text-gray-900">{{ cfg.defectActionLabel(selectedDefect.action_type) }}</p></div>
            <div v-if="selectedDefect.suggested_parts"><p class="text-gray-500">Необходимые запчасти</p><p class="text-gray-900">{{ selectedDefect.suggested_parts }}</p></div>

            <!-- Status change -->
            <div class="pt-3 border-t">
              <label class="block text-sm font-medium text-gray-700 mb-1">Изменить статус</label>
              <div class="flex gap-2">
                <select v-model="newStatus" class="input flex-1">
                  <option v-for="s in cfg.defectStatuses" :key="s.code" :value="s.code">{{ s.display_name }}</option>
                </select>
                <button @click="updateStatus" :disabled="saving" class="btn btn-primary disabled:opacity-50 whitespace-nowrap">
                  {{ saving ? '...' : 'Применить' }}
                </button>
              </div>
            </div>
          </div>
          <div class="p-6 border-t flex justify-end">
            <button @click="selectedDefect = null" class="btn btn-primary">Закрыть</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { AlertTriangle, X, Building2, Users, Calendar } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { useConfigStore } from '../stores/config.js'
import { defectsAPI } from '../services/api.js'

const cfg = useConfigStore()
const defects = ref([])
const loading = ref(true)
const filterStatus = ref('')
const filterPriority = ref('')
const selectedDefect = ref(null)
const newStatus = ref('')
const saving = ref(false)

watch(selectedDefect, (d) => { if (d) newStatus.value = d.status })

async function loadDefects() {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterPriority.value) params.priority = filterPriority.value
    const res = await defectsAPI.getAll(params)
    defects.value = res.data
  } finally {
    loading.value = false
  }
}

async function updateStatus() {
  saving.value = true
  try {
    const res = await defectsAPI.update(selectedDefect.value.id, { status: newStatus.value })
    selectedDefect.value = res.data
    // Update in list
    const idx = defects.value.findIndex((d) => d.id === res.data.id)
    if (idx >= 0) defects.value[idx] = res.data
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function defectStatusClass(s) {
  const m = { open: 'bg-red-100 text-red-700', approved: 'bg-blue-100 text-blue-700', in_progress: 'bg-yellow-100 text-yellow-700', fixed: 'bg-green-100 text-green-700' }
  return m[s] || 'bg-gray-100 text-gray-700'
}
function priorityClass(p) {
  const m = { low: 'bg-gray-100 text-gray-600', medium: 'bg-yellow-100 text-yellow-700', high: 'bg-orange-100 text-orange-700', urgent: 'bg-red-100 text-red-700' }
  return m[p] || 'bg-gray-100 text-gray-700'
}
function formatDate(d) { if (!d) return '—'; return new Date(d.includes('T') ? d : d + 'T00:00:00').toLocaleDateString('ru-RU') }

onMounted(loadDefects)
</script>
