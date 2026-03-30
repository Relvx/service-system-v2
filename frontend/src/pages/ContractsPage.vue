<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between flex-wrap gap-y-3 mb-4">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Договоры</h1>
          <p class="text-gray-600 mt-1">Показано: {{ contracts.length }} из {{ total }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-4 h-4 mr-2" />Новый договор
        </button>
      </div>

      <!-- Фильтры -->
      <div class="card mb-4">
        <div class="flex flex-wrap gap-3 items-end">
          <div class="relative flex-1 min-w-[200px]">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              v-model="filters.search"
              @input="debouncedLoad"
              placeholder="Поиск по номеру, предмету, клиенту..."
              class="input pl-9 text-sm"
            />
          </div>
          <div class="min-w-[150px]">
            <select v-model="filters.status" @change="load" class="input text-sm">
              <option value="">Все статусы</option>
              <option value="active">Активен</option>
              <option value="closed">Закрыт</option>
              <option value="cancelled">Отменён</option>
            </select>
          </div>
          <button
            v-if="hasActiveFilters"
            @click="resetFilters"
            class="btn btn-secondary text-sm flex items-center gap-1"
          >
            <X class="w-4 h-4" />Сбросить
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>

      <template v-else>
        <DataTable
          :columns="columns"
          :rows="contracts"
          storage-key="contracts-table-v1"
          :total="total"
          :page="page"
          :page-size="pageSize"
          :loading="loading"
          @row-click="onRowClick"
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
          @reload="load"
        >
          <!-- Номер -->
          <template #contract_number="{ row }">
            <div
              class="flex items-center gap-2 min-w-0 cursor-pointer"
              @click.stop="openContractQuick(row)"
            >
              <div class="w-7 h-7 bg-blue-100 rounded-md flex-shrink-0 flex items-center justify-center">
                <FileText class="w-4 h-4 text-blue-600" />
              </div>
              <div class="min-w-0">
                <div class="font-medium text-gray-900 truncate hover:text-blue-700 hover:underline">{{ row.contract_number || 'Без номера' }}</div>
                <div v-if="row.subject" class="text-xs text-gray-400 truncate">{{ row.subject }}</div>
              </div>
            </div>
          </template>

          <!-- Клиент -->
          <template #client_name="{ row }">
            <span
              v-if="row.client_name"
              class="truncate block text-gray-700 cursor-pointer hover:text-primary-600 hover:underline"
              @click.stop="row.client_id && openClientQuick(row.client_id)"
            >{{ row.client_name }}</span>
            <span v-else class="text-gray-300">—</span>
          </template>

          <!-- Дата -->
          <template #contract_date="{ row }">
            <span class="text-sm text-gray-700">{{ formatDate(row.contract_date) }}</span>
          </template>

          <!-- Сумма -->
          <template #amount="{ row }">
            <span v-if="row.amount" class="text-sm font-medium text-gray-800">{{ formatAmount(row.amount) }} ₽</span>
            <span v-else class="text-gray-300">—</span>
          </template>

          <!-- Сумма акта -->
          <template #act_amount="{ row }">
            <span v-if="row.act_amount" class="text-sm font-medium text-gray-800">{{ formatAmount(row.act_amount) }} ₽</span>
            <span v-else class="text-gray-300">—</span>
          </template>

          <!-- Объекты -->
          <template #sites_count="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="(row.sites_count || 0) > 0 ? 'text-green-700' : 'text-gray-400'"
              @click.stop="(row.sites_count || 0) > 0 && openContractQuick(row)"
            >
              <MapPin class="w-3.5 h-3.5" />{{ row.sites_count ?? 0 }}
            </span>
          </template>

          <!-- Статус -->
          <template #status="{ row }">
            <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="statusClass(row.status)">
              {{ statusLabel(row.status) }}
            </span>
          </template>

          <!-- Действия -->
          <template #actions="{ row }">
            <div class="flex items-center gap-1" @click.stop>
              <router-link
                :to="`/contracts/${row.id}`"
                class="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-primary-600"
                title="Открыть"
              >
                <Eye class="w-4 h-4" />
              </router-link>
            </div>
          </template>

          <template #empty>
            <div class="flex flex-col items-center py-8 text-gray-400">
              <FileText class="w-12 h-12 mb-3 text-gray-200" />
              <p>Договоры не найдены</p>
            </div>
          </template>
        </DataTable>

      </template>

      <!-- Quick: Договор -->
      <ContractQuickModal
        v-if="quickContract"
        :contract="quickContract"
        @close="quickContract = null"
        @open-page="router.push(`/contracts/${quickContract.id}`); quickContract = null"
        @open-client="quickContract.client_id && openClientQuick(quickContract.client_id); quickContract = null"
        @open-site="(s) => { quickContract = null; openSiteQuick(s) }"
      />

      <!-- Quick: Объект -->
      <SiteQuickModal
        v-if="quickSite"
        :site="quickSite"
        @close="quickSite = null"
        @open-page="router.push(`/sites/${quickSite.id}`); quickSite = null"
        @open-client="quickSite.client_id && openClientQuick(quickSite.client_id); quickSite = null"
      />

      <!-- Quick: Клиент -->
      <ClientQuickModal
        v-if="quickClient"
        :client="quickClient"
        @close="quickClient = null"
        @open-page="router.push(`/clients/${quickClient.id}`); quickClient = null"
      />

      <!-- Модал создания -->
      <div v-if="createModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">Новый договор</h2>
            <button @click="createModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleCreate" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Номер договора *</label>
              <input v-model="form.contract_number" class="input" :class="{ 'border-red-400': createErrors.contract_number }" placeholder="0817/2 от 17.08.2006" @input="delete createErrors.contract_number" />
              <p v-if="createErrors.contract_number" class="text-red-600 text-xs mt-1">{{ createErrors.contract_number }}</p>
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
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, FileText, X, Search, MapPin, Eye } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import ContractQuickModal from '../components/modals/ContractQuickModal.vue'
import SiteQuickModal from '../components/modals/SiteQuickModal.vue'
import ClientQuickModal from '../components/modals/ClientQuickModal.vue'
import { contractsAPI, sitesAPI, clientsAPI } from '../services/api.js'
import { useEscClose } from '../composables/useEscClose.js'

const router = useRouter()
const contracts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loading = ref(true)
const createModalOpen = ref(false)
const saving = ref(false)
const form = ref({ contract_number: '', contract_date: '', subject: '', amount: '', act_amount: '', notes: '' })
const createErrors = ref({})

// Quick modals
const quickContract = ref(null)
const quickSite = ref(null)
const quickClient = ref(null)

async function openContractQuick(row) {
  try {
    const detail = await contractsAPI.getById(row.id)
    quickContract.value = detail.data
  } catch { /* ignore */ }
}

async function openSiteQuick(site) {
  try {
    const detail = await sitesAPI.getById(site.id)
    quickSite.value = detail.data
  } catch { /* ignore */ }
}

async function openClientQuick(clientId) {
  try {
    const detail = await clientsAPI.getById(clientId)
    quickClient.value = detail.data
  } catch { /* ignore */ }
}

useEscClose([
  { isOpen: () => !!quickSite.value,     close: () => { quickSite.value = null } },
  { isOpen: () => !!quickClient.value,   close: () => { quickClient.value = null } },
  { isOpen: () => !!quickContract.value, close: () => { quickContract.value = null } },
  { isOpen: () => createModalOpen.value, close: () => { createModalOpen.value = false } },
])

const filters = ref({ search: '', status: '' })
const hasActiveFilters = computed(() => filters.value.search || filters.value.status)

const columns = [
  { key: 'contract_number', label: 'Договор',    width: 260, sortable: true },
  { key: 'client_name',     label: 'Клиент',     width: 200, sortable: true },
  { key: 'contract_date',   label: 'Дата',       width: 120, sortable: true },
  { key: 'amount',          label: 'Сумма',      width: 140, sortable: true },
  { key: 'act_amount',      label: 'Сумма акта', width: 140, sortable: true, defaultVisible: false },
  { key: 'sites_count',     label: 'Объекты',    width: 100, sortable: true },
  { key: 'status',          label: 'Статус',     width: 110, sortable: false },
  { key: 'actions',         label: '',           width: 60,  sortable: false },
]

function onRowClick(_row) {
  // клики обрабатываются в ячейках
}

function buildParams() {
  const p = {
    limit: pageSize.value,
    offset: (page.value - 1) * pageSize.value,
  }
  if (filters.value.search) p.search = filters.value.search
  if (filters.value.status) p.status = filters.value.status
  return p
}

let searchTimer = null
function debouncedLoad() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; load() }, 300)
}

async function load() {
  loading.value = true
  try {
    const res = await contractsAPI.getAll(buildParams())
    contracts.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onPageChange(p) { page.value = p; load() }
function onPageSizeChange(s) { pageSize.value = s; page.value = 1; load() }

function resetFilters() {
  filters.value = { search: '', status: '' }
  page.value = 1
  load()
}

function openCreate() {
  form.value = { contract_number: '', contract_date: '', subject: '', amount: '', act_amount: '', notes: '' }
  createErrors.value = {}
  createModalOpen.value = true
}

async function handleCreate() {
  const e = {}
  if (!form.value.contract_number.trim()) e.contract_number = 'Введите номер договора'
  createErrors.value = e
  if (Object.keys(e).length) return
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
