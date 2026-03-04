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
            <option v-for="s in cfg.defectStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
          </select>
          <select v-model="filterPriority" @change="loadDefects" class="input">
            <option value="">Все приоритеты</option>
            <option v-for="p in cfg.priorities" :key="p.sysname" :value="p.sysname">{{ p.display_name }}</option>
          </select>
          <button @click="loadDefects" class="btn btn-primary">Обновить</button>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <DataTable v-else :columns="columns" :rows="defects" storage-key="defects_table" @row-click="selectedDefect = $event">
        <template #title="{ row }">
          <button @click="selectedDefect = row" class="text-left hover:text-primary-600 font-medium truncate block w-full">
            {{ row.title }}
          </button>
        </template>

        <template #status="{ row }">
          <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="defectStatusClass(row.status)">
            {{ cfg.defectStatusLabel(row.status) }}
          </span>
        </template>

        <template #priority="{ row }">
          <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="priorityClass(row.priority)">
            {{ cfg.priorityLabel(row.priority) }}
          </span>
        </template>

        <template #visit_date="{ row }">
          {{ formatDate(row.visit_date) }}
        </template>

        <template #created_at="{ row }">
          {{ formatDate(row.created_at) }}
        </template>

        <template #actions="{ row }">
          <button @click="selectedDefect = row" class="text-primary-600 hover:text-primary-900" title="Подробнее">
            <Eye class="w-4 h-4" />
          </button>
        </template>

        <template #empty>
          <div class="flex flex-col items-center gap-2">
            <AlertTriangle class="w-12 h-12 text-gray-300" />
            <span>Дефекты не найдены</span>
          </div>
        </template>
      </DataTable>

      <!-- Detail / Status Modal -->
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

            <div class="pt-3 border-t">
              <label class="block text-sm font-medium text-gray-700 mb-1">Изменить статус</label>
              <div class="flex gap-2">
                <select v-model="newStatus" class="input flex-1">
                  <option v-for="s in cfg.defectStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
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
import { AlertTriangle, X, Eye } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
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

const columns = [
  { key: 'title',       label: 'Дефект',       width: 220 },
  { key: 'site_title',  label: 'Объект',       width: 180 },
  { key: 'client_name', label: 'Клиент',       width: 150, defaultVisible: false },
  { key: 'status',      label: 'Статус',       width: 130 },
  { key: 'priority',    label: 'Приоритет',    width: 130 },
  { key: 'visit_date',  label: 'Дата выезда',  width: 130, defaultVisible: false },
  { key: 'created_at',  label: 'Создан',       width: 130 },
  { key: 'actions',     label: 'Действия',     width: 90, sortable: false },
]

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
