<template>
  <Layout>
    <div>
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">Журнал действий</h1>
        <p class="text-gray-600 mt-1">Аудит-лог всех изменений в системе</p>
      </div>

      <!-- Фильтры -->
      <div class="card mb-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Сущность</label>
            <select v-model="filters.entity_type" class="input" @change="load">
              <option value="">Все</option>
              <option value="visit">Выезды</option>
              <option value="client">Клиенты</option>
              <option value="site">Объекты</option>
              <option value="purchase">Закупки</option>
              <option value="defect">Дефекты</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">Действие</label>
            <select v-model="filters.action_sysname" class="input" @change="load">
              <option value="">Все</option>
              <option value="create">Создание</option>
              <option value="update">Изменение</option>
              <option value="delete">Удаление</option>
              <option value="complete">Завершение</option>
              <option value="approve">Согласование</option>
              <option value="assign">Назначение</option>
            </select>
          </div>
          <div class="md:col-span-2 flex items-end">
            <button @click="reset" class="btn text-sm">Сбросить фильтры</button>
          </div>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>

      <div v-else>
        <div class="card overflow-hidden p-0">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="text-left px-4 py-3 font-medium text-gray-600 w-40">Дата/Время</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600 w-32">Действие</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600 w-28">Сущность</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600">ID записи</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600 w-44">Пользователь</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600">Детали</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-if="!logs.length">
                <td colspan="6" class="px-4 py-8 text-center text-gray-400">Записей нет</td>
              </tr>
              <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50">
                <td class="px-4 py-2.5 text-gray-500 text-xs whitespace-nowrap">
                  {{ formatDate(log.created_at) }}
                </td>
                <td class="px-4 py-2.5">
                  <span class="px-2 py-0.5 rounded-full text-xs font-medium"
                        :class="actionClass(log.action_sysname)">
                    {{ actionLabel(log.action_sysname) }}
                  </span>
                </td>
                <td class="px-4 py-2.5 text-gray-600 text-xs">
                  {{ entityLabel(log.entity_type) }}
                </td>
                <td class="px-4 py-2.5 text-gray-400 font-mono text-xs truncate max-w-[160px]">
                  {{ log.entity_id }}
                </td>
                <td class="px-4 py-2.5 text-gray-700 text-xs">
                  {{ log.user_name || '—' }}
                </td>
                <td class="px-4 py-2.5 text-gray-500 text-xs">
                  <span v-if="log.details">{{ JSON.stringify(log.details) }}</span>
                  <span v-else>—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Пагинация -->
        <div class="flex justify-between items-center mt-4 text-sm text-gray-600">
          <span>Показано {{ logs.length }} записей (смещение: {{ offset }})</span>
          <div class="flex gap-2">
            <button :disabled="offset === 0" @click="prevPage"
                    class="btn disabled:opacity-40">← Назад</button>
            <button :disabled="logs.length < limit" @click="nextPage"
                    class="btn disabled:opacity-40">Вперёд →</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import { logsAPI } from '../services/api.js'

const logs = ref([])
const loading = ref(false)
const limit = 100
const offset = ref(0)

const filters = reactive({
  entity_type: '',
  action_sysname: '',
})

async function load() {
  loading.value = true
  try {
    const params = { limit, offset: offset.value }
    if (filters.entity_type) params.entity_type = filters.entity_type
    if (filters.action_sysname) params.action_sysname = filters.action_sysname
    const res = await logsAPI.getAll(params)
    logs.value = res.data
  } finally {
    loading.value = false
  }
}

function reset() {
  filters.entity_type = ''
  filters.action_sysname = ''
  offset.value = 0
  load()
}

function prevPage() {
  offset.value = Math.max(0, offset.value - limit)
  load()
}
function nextPage() {
  offset.value += limit
  load()
}

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU') + ' ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

const ACTION_LABELS = {
  create: 'Создание', update: 'Изменение', delete: 'Удаление',
  complete: 'Завершение', approve: 'Согласование', assign: 'Назначение',
}
const ACTION_CLASSES = {
  create:   'bg-green-100 text-green-700',
  update:   'bg-blue-100 text-blue-700',
  delete:   'bg-red-100 text-red-700',
  complete: 'bg-purple-100 text-purple-700',
  approve:  'bg-indigo-100 text-indigo-700',
  assign:   'bg-yellow-100 text-yellow-700',
}
const ENTITY_LABELS = {
  visit: 'Выезд', client: 'Клиент', site: 'Объект',
  purchase: 'Закупка', defect: 'Дефект',
}

function actionLabel(s) { return ACTION_LABELS[s] || s || '—' }
function actionClass(s) { return ACTION_CLASSES[s] || 'bg-gray-100 text-gray-600' }
function entityLabel(s) { return ENTITY_LABELS[s] || s || '—' }

onMounted(load)
</script>
