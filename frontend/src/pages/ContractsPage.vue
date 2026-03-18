<template>
  <Layout>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl md:text-3xl font-bold text-gray-900">Договоры</h1>
      <button @click="openCreate" class="btn btn-primary flex items-center">
        <Plus class="w-4 h-4 mr-2" />Новый договор
      </button>
    </div>

    <!-- Фильтры -->
    <div class="card mb-6 flex flex-wrap gap-3">
      <input
        v-model="search"
        placeholder="Поиск по номеру или предмету..."
        class="input flex-1 min-w-48"
        @input="load"
      />
      <select v-model="filterStatus" @change="load" class="input w-40">
        <option value="">Все статусы</option>
        <option value="active">Активен</option>
        <option value="closed">Закрыт</option>
        <option value="cancelled">Отменён</option>
      </select>
    </div>

    <!-- Список -->
    <div v-if="loading" class="flex justify-center py-16">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
    </div>

    <div v-else-if="contracts.length === 0" class="text-center py-16 card">
      <FileText class="w-12 h-12 text-gray-300 mx-auto mb-3" />
      <p class="text-gray-500">Договоры не найдены</p>
    </div>

    <div v-else class="space-y-3">
      <router-link
        v-for="c in contracts" :key="c.id"
        :to="`/contracts/${c.id}`"
        class="card hover:shadow-md transition-shadow block"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-start gap-3">
            <div class="w-9 h-9 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
              <FileText class="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <div class="flex items-center gap-2 flex-wrap">
                <p class="font-semibold text-gray-900">{{ c.contract_number || 'Без номера' }}</p>
                <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="statusClass(c.status)">
                  {{ statusLabel(c.status) }}
                </span>
              </div>
              <p v-if="c.client_name" class="text-sm text-gray-600 mt-0.5">{{ c.client_name }}</p>
              <p v-if="c.subject" class="text-sm text-gray-500 mt-0.5">{{ c.subject }}</p>
            </div>
          </div>
          <div class="text-right text-sm text-gray-500 flex-shrink-0 ml-4">
            <p v-if="c.contract_date">{{ formatDate(c.contract_date) }}</p>
            <p v-if="c.amount" class="font-medium text-gray-700 mt-1">{{ formatAmount(c.amount) }} ₽</p>
          </div>
        </div>
      </router-link>
    </div>

    <!-- Модал создания -->
    <div v-if="createModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div class="flex items-center justify-between p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">Новый договор</h2>
          <button @click="createModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleCreate" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Номер договора</label>
            <input v-model="form.contract_number" class="input" placeholder="0817/2 от 17.08.2006" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Дата договора</label>
            <input v-model="form.contract_date" type="date" class="input" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Предмет договора</label>
            <input v-model="form.subject" class="input" placeholder="ТО газового оборудования" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Сумма договора</label>
              <input v-model="form.amount" type="number" step="0.01" class="input" placeholder="50000" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Сумма акта</label>
              <input v-model="form.act_amount" type="number" step="0.01" class="input" placeholder="50000" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
            <textarea v-model="form.notes" class="input" rows="2" />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="createModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
              {{ saving ? 'Сохранение...' : 'Создать' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, FileText, X } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { contractsAPI } from '../services/api.js'

const contracts = ref([])
const loading = ref(true)
const search = ref('')
const filterStatus = ref('')
const createModalOpen = ref(false)
const saving = ref(false)
const form = ref({ contract_number: '', contract_date: '', subject: '', amount: '', act_amount: '', notes: '' })

async function load() {
  loading.value = true
  try {
    const params = {}
    if (search.value) params.search = search.value
    if (filterStatus.value) params.status = filterStatus.value
    const res = await contractsAPI.getAll(params)
    contracts.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { contract_number: '', contract_date: '', subject: '', amount: '', act_amount: '', notes: '' }
  createModalOpen.value = true
}

async function handleCreate() {
  saving.value = true
  try {
    const payload = { ...form.value }
    if (!payload.contract_date) delete payload.contract_date
    if (!payload.amount) delete payload.amount
    if (!payload.act_amount) delete payload.act_amount
    await contractsAPI.create(payload)
    createModalOpen.value = false
    await load()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function statusClass(s) {
  const m = { active: 'bg-green-100 text-green-700', closed: 'bg-gray-200 text-gray-600', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-600'
}
function statusLabel(s) {
  const m = { active: 'Активен', closed: 'Закрыт', cancelled: 'Отменён' }
  return m[s] || s
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }
function formatAmount(v) { return Number(v).toLocaleString('ru-RU') }

onMounted(load)
</script>
