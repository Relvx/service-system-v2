<template>
  <Layout>
    <div>
      <div class="mb-4">
        <h1 class="text-xl md:text-3xl font-bold text-gray-900">Журнал действий</h1>
        <p class="text-gray-600 mt-1">Аудит-лог всех изменений в системе</p>
      </div>

      <!-- Фильтры -->
      <div class="card mb-4">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          <!-- Номер документа -->
          <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Номер документа</label>
            <div class="relative">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                v-model="filters.entity_id_search"
                type="text"
                placeholder="UUID или часть..."
                class="input pl-9 text-sm"
                @input="debouncedLoad"
              />
            </div>
          </div>

          <!-- Пользователь -->
          <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Пользователь</label>
            <div class="relative">
              <User class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                v-model="filters.user_name_search"
                type="text"
                placeholder="Имя пользователя..."
                class="input pl-9 text-sm"
                @input="debouncedLoad"
              />
            </div>
          </div>

          <!-- Тип действия -->
          <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Тип действия</label>
            <select v-model="filters.action_sysname" class="input text-sm" @change="resetAndLoad">
              <option value="">Все действия</option>
              <optgroup label="Создание">
                <option value="client_create">Создание клиента</option>
                <option value="site_create">Создание объекта</option>
                <option value="visit_create">Создание выезда</option>
                <option value="defect_create">Создание дефекта</option>
                <option value="purchase_create">Создание закупки</option>
              </optgroup>
              <optgroup label="Изменение">
                <option value="client_update">Изменение клиента</option>
                <option value="site_update">Изменение объекта</option>
                <option value="visit_update">Изменение выезда</option>
                <option value="defect_update">Изменение дефекта</option>
                <option value="purchase_update">Изменение закупки</option>
              </optgroup>
              <optgroup label="Статус">
                <option value="client_change_status">Статус клиента</option>
                <option value="visit_change_status">Статус выезда</option>
                <option value="defect_change_status">Статус дефекта</option>
                <option value="defect_approve">Согласование дефекта</option>
                <option value="purchase_change_status">Статус закупки</option>
                <option value="visit_assign">Назначение мастера</option>
                <option value="visit_complete">Завершение выезда</option>
              </optgroup>
              <optgroup label="Удаление">
                <option value="client_delete">Удаление клиента</option>
                <option value="site_delete">Удаление объекта</option>
                <option value="visit_delete">Удаление выезда</option>
              </optgroup>
            </select>
          </div>

          <!-- Тип документа -->
          <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Тип документа</label>
            <select v-model="filters.entity_type" class="input text-sm" @change="resetAndLoad">
              <option value="">Все документы</option>
              <option v-for="et in entityTypes" :key="et.sysname" :value="et.sysname">{{ et.display_name_plural }}</option>
            </select>
          </div>
        </div>

        <!-- Активные фильтры + сброс -->
        <div v-if="hasActiveFilters" class="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
          <div class="flex flex-wrap gap-2">
            <span v-if="filters.entity_id_search" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs">
              Документ: {{ filters.entity_id_search }}
              <button @click="filters.entity_id_search = ''; resetAndLoad()"><X class="w-3 h-3" /></button>
            </span>
            <span v-if="filters.user_name_search" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs">
              Пользователь: {{ filters.user_name_search }}
              <button @click="filters.user_name_search = ''; resetAndLoad()"><X class="w-3 h-3" /></button>
            </span>
            <span v-if="filters.action_sysname" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs">
              Действие: {{ actionLabel(filters.action_sysname) }}
              <button @click="filters.action_sysname = ''; resetAndLoad()"><X class="w-3 h-3" /></button>
            </span>
            <span v-if="filters.entity_type" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs">
              Раздел: {{ activeEntityLabel }}
              <button @click="filters.entity_type = ''; resetAndLoad()"><X class="w-3 h-3" /></button>
            </span>
          </div>
          <button @click="reset" class="btn text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1">
            <X class="w-4 h-4" />Сбросить все
          </button>
        </div>
      </div>

      <!-- Загрузка -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>

      <template v-else>
        <DataTable
          :columns="columns"
          :rows="logs"
          storage-key="logs-table-v1"
          :total="total"
          :page="page"
          :page-size="pageSize"
          :loading="loading"
          @row-click="openDetail"
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
          @reload="load"
        >
          <!-- Дата/Время -->
          <template #created_at="{ row }">
            <span class="text-xs text-gray-500 whitespace-nowrap">{{ formatDate(row.created_at) }}</span>
          </template>

          <!-- Действие -->
          <template #action_sysname="{ row }">
            <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="actionClass(row.action_sysname)">
              {{ actionLabel(row.action_sysname) }}
            </span>
          </template>

          <!-- Раздел -->
          <template #entity_type="{ row }">
            <span class="text-xs text-gray-600">{{ entityLabel(row.entity_type) }}</span>
          </template>

          <!-- Номер документа -->
          <template #entity_id="{ row }">
            <span class="font-mono text-xs text-gray-400 truncate block" :title="row.entity_id">{{ row.entity_id }}</span>
          </template>

          <!-- Пользователь -->
          <template #user_name="{ row }">
            <span class="text-xs text-gray-700">{{ row.user_name || '—' }}</span>
          </template>

          <!-- Детали -->
          <template #details="{ row }">
            <span v-if="row.details" class="text-xs text-gray-400 truncate block">{{ JSON.stringify(row.details) }}</span>
            <span v-else class="text-gray-300">—</span>
          </template>

          <template #empty>
            <div class="flex flex-col items-center py-8 text-gray-400">
              <ScrollText class="w-10 h-10 mb-2 text-gray-200" />
              <p>Записей не найдено</p>
            </div>
          </template>
        </DataTable>

      </template>
    </div>

    <!-- Модал деталей -->
    <div v-if="detail" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="detail = null">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-start mb-4">
          <div>
            <span class="px-2 py-0.5 rounded-full text-xs font-medium mr-2" :class="actionClass(detail.action_sysname)">
              {{ actionLabel(detail.action_sysname) }}
            </span>
            <span class="text-sm text-gray-500">{{ entityLabel(detail.entity_type) }}</span>
          </div>
          <button @click="detail = null" class="text-gray-400 hover:text-gray-600">
            <X class="w-5 h-5" />
          </button>
        </div>

        <dl class="space-y-2 text-sm">
          <div class="flex gap-2">
            <dt class="text-gray-400 w-32 shrink-0">Дата/Время</dt>
            <dd class="text-gray-900 font-medium">{{ formatDate(detail.created_at) }}</dd>
          </div>
          <div class="flex gap-2">
            <dt class="text-gray-400 w-32 shrink-0">Пользователь</dt>
            <dd class="text-gray-900">{{ detail.user_name || '—' }}</dd>
          </div>
          <div class="flex gap-2">
            <dt class="text-gray-400 w-32 shrink-0">Номер документа</dt>
            <dd class="font-mono text-xs text-gray-600 break-all">{{ detail.entity_id }}</dd>
          </div>
          <div v-if="detail.details" class="flex gap-2">
            <dt class="text-gray-400 w-32 shrink-0">Детали</dt>
            <dd class="text-gray-700">
              <pre class="bg-gray-50 rounded p-2 text-xs overflow-x-auto overflow-y-auto max-h-64 whitespace-pre-wrap break-all">{{ JSON.stringify(detail.details, null, 2) }}</pre>
            </dd>
          </div>
        </dl>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, User, X, ScrollText } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import { logsAPI, configAPI } from '../services/api.js'
import { useEscClose } from '../composables/useEscClose.js'

const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(100)
const entityTypes = ref([])
const loading = ref(false)
const detail = ref(null)

useEscClose([
  { isOpen: () => !!detail.value, close: () => { detail.value = null } },
])

const filters = reactive({
  entity_id_search: '',
  user_name_search: '',
  action_sysname: '',
  entity_type: '',
})

const hasActiveFilters = computed(() =>
  filters.entity_id_search || filters.user_name_search ||
  filters.action_sysname || filters.entity_type
)

const columns = [
  { key: 'created_at',     label: 'Дата/Время',      width: 150, sortable: false },
  { key: 'action_sysname', label: 'Действие',        width: 180, sortable: false },
  { key: 'entity_type',    label: 'Раздел',          width: 120, sortable: false },
  { key: 'entity_id',      label: 'Документ',        width: 170, sortable: false },
  { key: 'user_name',      label: 'Пользователь',   width: 160, sortable: false },
  { key: 'details',        label: 'Детали',          width: 220, sortable: false, defaultVisible: false },
]

async function load() {
  loading.value = true
  try {
    const params = {
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    }
    if (filters.entity_type)      params.entity_type      = filters.entity_type
    if (filters.action_sysname)   params.action_sysname   = filters.action_sysname
    if (filters.entity_id_search) params.entity_id_search = filters.entity_id_search
    if (filters.user_name_search) params.user_name_search = filters.user_name_search
    const res = await logsAPI.getAll(params)
    logs.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function resetAndLoad() {
  page.value = 1
  load()
}

function reset() {
  filters.entity_id_search = ''
  filters.user_name_search = ''
  filters.action_sysname = ''
  filters.entity_type = ''
  page.value = 1
  load()
}

function onPageChange(p) { page.value = p; load() }
function onPageSizeChange(s) { pageSize.value = s; page.value = 1; load() }

let debounceTimer = null
function debouncedLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => resetAndLoad(), 400)
}

function openDetail(log) {
  detail.value = log
}

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU') + ' ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

const ACTION_LABELS = {
  create: 'Создание', update: 'Изменение', delete: 'Удаление',
  complete: 'Завершение', approve: 'Согласование', assign: 'Назначение',
  client_create: 'Создание клиента', client_update: 'Изменение клиента',
  client_delete: 'Удаление клиента', client_change_status: 'Статус клиента',
  site_create: 'Создание объекта', site_update: 'Изменение объекта',
  site_delete: 'Удаление объекта',
  visit_create: 'Создание выезда', visit_update: 'Изменение выезда',
  visit_delete: 'Удаление выезда', visit_complete: 'Завершение выезда',
  visit_assign: 'Назначение мастера', visit_change_status: 'Статус выезда',
  defect_create: 'Создание дефекта', defect_update: 'Изменение дефекта',
  defect_change_status: 'Статус дефекта', defect_approve: 'Согласование дефекта',
  purchase_create: 'Создание закупки', purchase_update: 'Изменение закупки',
  purchase_change_status: 'Статус закупки',
}

function _actionGroup(s) {
  if (!s) return 'other'
  if (s.endsWith('_create') || s === 'create') return 'create'
  if (s.endsWith('_delete') || s === 'delete') return 'delete'
  if (s.endsWith('_complete') || s === 'complete') return 'complete'
  if (s.endsWith('_approve') || s === 'approve') return 'approve'
  if (s.endsWith('_assign') || s === 'assign') return 'assign'
  if (s.endsWith('_change_status')) return 'status'
  return 'update'
}

const ACTION_CLASSES = {
  create:   'bg-green-100 text-green-700',
  update:   'bg-blue-100 text-blue-700',
  delete:   'bg-red-100 text-red-700',
  complete: 'bg-purple-100 text-purple-700',
  approve:  'bg-indigo-100 text-indigo-700',
  assign:   'bg-yellow-100 text-yellow-700',
  status:   'bg-orange-100 text-orange-700',
  other:    'bg-gray-100 text-gray-600',
}

const entityLabelMap = computed(() => {
  const m = {}
  for (const et of entityTypes.value) m[et.sysname] = et.display_name
  return m
})

function actionLabel(s) { return ACTION_LABELS[s] || s || '—' }
function actionClass(s)  { return ACTION_CLASSES[_actionGroup(s)] || ACTION_CLASSES.other }
function entityLabel(s)  { return entityLabelMap.value[s] || s || '—' }

const activeEntityLabel = computed(() =>
  filters.entity_type ? (entityLabelMap.value[filters.entity_type] || filters.entity_type) : ''
)

onMounted(async () => {
  const [, etRes] = await Promise.all([load(), configAPI.getEntityTypes()])
  entityTypes.value = etRes.data
})
</script>
