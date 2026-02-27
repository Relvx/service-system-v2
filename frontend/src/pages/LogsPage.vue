<template>
  <Layout>
    <div>
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">Журнал действий</h1>
        <p class="text-gray-600 mt-1">Аудит-лог всех изменений в системе</p>
      </div>

      <!-- Фильтры и поиск -->
      <div class="card mb-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- Поиск по номеру документа -->
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Номер документа</label>
            <div class="relative">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                v-model="filters.entity_id_search"
                type="text"
                placeholder="UUID или часть..."
                class="input pl-9"
                @input="debouncedLoad"
              />
            </div>
          </div>

          <!-- Поиск по пользователю -->
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Пользователь</label>
            <div class="relative">
              <User class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                v-model="filters.user_name_search"
                type="text"
                placeholder="Имя пользователя..."
                class="input pl-9"
                @input="debouncedLoad"
              />
            </div>
          </div>

          <!-- Тип действия -->
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Тип действия</label>
            <select v-model="filters.action_sysname" class="input" @change="resetAndLoad">
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

          <!-- Сущность -->
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Раздел</label>
            <select v-model="filters.entity_type" class="input" @change="resetAndLoad">
              <option value="">Все разделы</option>
              <option value="visit">Выезды</option>
              <option value="client">Клиенты</option>
              <option value="site">Объекты</option>
              <option value="purchase">Закупки</option>
              <option value="defect">Дефекты</option>
            </select>
          </div>
        </div>

        <!-- Активные фильтры + сброс -->
        <div class="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
          <div class="flex flex-wrap gap-2">
            <span
              v-if="filters.entity_id_search"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs"
            >
              Документ: {{ filters.entity_id_search }}
              <button @click="filters.entity_id_search = ''; resetAndLoad()">
                <X class="w-3 h-3" />
              </button>
            </span>
            <span
              v-if="filters.user_name_search"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs"
            >
              Пользователь: {{ filters.user_name_search }}
              <button @click="filters.user_name_search = ''; resetAndLoad()">
                <X class="w-3 h-3" />
              </button>
            </span>
            <span
              v-if="filters.action_sysname"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs"
            >
              Действие: {{ actionLabel(filters.action_sysname) }}
              <button @click="filters.action_sysname = ''; resetAndLoad()">
                <X class="w-3 h-3" />
              </button>
            </span>
            <span
              v-if="filters.entity_type"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs"
            >
              Раздел: {{ entityLabel(filters.entity_type) }}
              <button @click="filters.entity_type = ''; resetAndLoad()">
                <X class="w-3 h-3" />
              </button>
            </span>
          </div>
          <button @click="reset" class="btn text-sm text-gray-500 hover:text-gray-700">
            Сбросить все
          </button>
        </div>
      </div>

      <!-- Загрузка -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>

      <div v-else>
        <!-- Счётчик -->
        <div class="flex items-center justify-between mb-3">
          <p class="text-sm text-gray-500">
            Показано <span class="font-medium text-gray-700">{{ logs.length }}</span> записей
            <span v-if="offset > 0"> (смещение: {{ offset }})</span>
          </p>
        </div>

        <div class="card overflow-hidden p-0">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="text-left px-4 py-3 font-medium text-gray-600 w-36">Дата/Время</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600 w-32">Действие</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600 w-24">Раздел</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600">Номер документа</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600 w-44">Пользователь</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600">Детали</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-if="!logs.length">
                <td colspan="6" class="px-4 py-12 text-center text-gray-400">
                  <div class="flex flex-col items-center gap-2">
                    <ScrollText class="w-8 h-8 text-gray-300" />
                    <span>Записей не найдено</span>
                  </div>
                </td>
              </tr>
              <tr
                v-for="log in logs"
                :key="log.id"
                class="hover:bg-gray-50 cursor-pointer"
                @click="openDetail(log)"
              >
                <td class="px-4 py-2.5 text-gray-500 text-xs whitespace-nowrap">
                  {{ formatDate(log.created_at) }}
                </td>
                <td class="px-4 py-2.5">
                  <span
                    class="px-2 py-0.5 rounded-full text-xs font-medium"
                    :class="actionClass(log.action_sysname)"
                  >
                    {{ actionLabel(log.action_sysname) }}
                  </span>
                </td>
                <td class="px-4 py-2.5 text-gray-600 text-xs">
                  {{ entityLabel(log.entity_type) }}
                </td>
                <td class="px-4 py-2.5 font-mono text-xs text-gray-400 truncate max-w-[160px]">
                  <span :title="log.entity_id">{{ log.entity_id }}</span>
                </td>
                <td class="px-4 py-2.5 text-gray-700 text-xs">
                  {{ log.user_name || '—' }}
                </td>
                <td class="px-4 py-2.5 text-gray-400 text-xs truncate max-w-[200px]">
                  <span v-if="log.details">{{ JSON.stringify(log.details) }}</span>
                  <span v-else>—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Пагинация -->
        <div class="flex justify-between items-center mt-4 text-sm text-gray-600">
          <span class="text-xs text-gray-400">Страница {{ currentPage }}</span>
          <div class="flex gap-2">
            <button
              :disabled="offset === 0"
              @click="prevPage"
              class="btn disabled:opacity-40 flex items-center gap-1"
            >
              <ChevronLeft class="w-4 h-4" /> Назад
            </button>
            <button
              :disabled="logs.length < limit"
              @click="nextPage"
              class="btn disabled:opacity-40 flex items-center gap-1"
            >
              Вперёд <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модал деталей -->
    <div v-if="detail" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="detail = null">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg">
        <div class="flex justify-between items-start mb-4">
          <div>
            <span
              class="px-2 py-0.5 rounded-full text-xs font-medium mr-2"
              :class="actionClass(detail.action_sysname)"
            >{{ actionLabel(detail.action_sysname) }}</span>
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
              <pre class="bg-gray-50 rounded p-2 text-xs overflow-auto max-h-48">{{ JSON.stringify(detail.details, null, 2) }}</pre>
            </dd>
          </div>
        </dl>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  Search, User, X, ScrollText,
  ChevronLeft, ChevronRight,
} from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { logsAPI } from '../services/api.js'

const logs = ref([])
const loading = ref(false)
const limit = 100
const offset = ref(0)
const detail = ref(null)

const filters = reactive({
  entity_id_search: '',
  user_name_search: '',
  action_sysname: '',
  entity_type: '',
})

const currentPage = computed(() => Math.floor(offset.value / limit) + 1)

async function load() {
  loading.value = true
  try {
    const params = { limit, offset: offset.value }
    if (filters.entity_type)      params.entity_type       = filters.entity_type
    if (filters.action_sysname)   params.action_sysname    = filters.action_sysname
    if (filters.entity_id_search) params.entity_id_search  = filters.entity_id_search
    if (filters.user_name_search) params.user_name_search  = filters.user_name_search
    const res = await logsAPI.getAll(params)
    logs.value = res.data
  } finally {
    loading.value = false
  }
}

function resetAndLoad() {
  offset.value = 0
  load()
}

function reset() {
  filters.entity_id_search = ''
  filters.user_name_search = ''
  filters.action_sysname = ''
  filters.entity_type = ''
  offset.value = 0
  load()
}

let debounceTimer = null
function debouncedLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => resetAndLoad(), 400)
}

function prevPage() {
  offset.value = Math.max(0, offset.value - limit)
  load()
}
function nextPage() {
  offset.value += limit
  load()
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
  // legacy
  create: 'Создание', update: 'Изменение', delete: 'Удаление',
  complete: 'Завершение', approve: 'Согласование', assign: 'Назначение',
  // clients
  client_create: 'Создание клиента', client_update: 'Изменение клиента',
  client_delete: 'Удаление клиента', client_change_status: 'Статус клиента',
  // sites
  site_create: 'Создание объекта', site_update: 'Изменение объекта',
  site_delete: 'Удаление объекта',
  // visits
  visit_create: 'Создание выезда', visit_update: 'Изменение выезда',
  visit_delete: 'Удаление выезда', visit_complete: 'Завершение выезда',
  visit_assign: 'Назначение мастера', visit_change_status: 'Статус выезда',
  // defects
  defect_create: 'Создание дефекта', defect_update: 'Изменение дефекта',
  defect_change_status: 'Статус дефекта', defect_approve: 'Согласование дефекта',
  // purchases
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
const ENTITY_LABELS = {
  visit:    'Выезд',
  client:   'Клиент',
  site:     'Объект',
  purchase: 'Закупка',
  defect:   'Дефект',
}

function actionLabel(s) { return ACTION_LABELS[s] || s || '—' }
function actionClass(s)  { return ACTION_CLASSES[_actionGroup(s)] || ACTION_CLASSES.other }
function entityLabel(s)  { return ENTITY_LABELS[s] || s || '—' }

onMounted(load)
</script>
