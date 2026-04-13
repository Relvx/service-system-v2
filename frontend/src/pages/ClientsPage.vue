<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between flex-wrap gap-y-3 mb-4">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Клиенты</h1>
          <p class="text-gray-600 mt-1">Всего: {{ total }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Добавить клиента
        </button>
      </div>

      <!-- Фильтры -->
      <div class="card mb-4">
        <!-- Мобильная шапка фильтров -->
        <button class="md:hidden w-full flex items-center justify-between text-sm font-medium text-gray-700 mb-2" @click="filtersOpen = !filtersOpen">
          <span class="flex items-center gap-2"><Filter class="w-4 h-4" />Фильтры<span v-if="hasActiveFilters" class="w-2 h-2 bg-primary-500 rounded-full inline-block"></span></span>
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="filtersOpen ? 'rotate-180' : ''" />
        </button>
        <div class="flex-wrap gap-3 items-end" :class="filtersOpen ? 'flex' : 'hidden md:flex'">

          <!-- Поиск -->
          <div class="relative flex-1 min-w-[200px]">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              v-model="filters.search"
              @input="debouncedLoad"
              type="text"
              placeholder="Поиск по названию, ИНН, контакту..."
              class="input pl-9 text-sm"
            />
          </div>

          <!-- Статус -->
          <div class="min-w-[150px]">
            <select v-model="filters.status" @change="loadClients" class="input text-sm">
              <option value="">Все статусы</option>
              <option value="active">Активные</option>
              <option value="inactive">Неактивные</option>
            </select>
          </div>

          <!-- Архивные (admin + office) -->
          <label v-if="auth.hasGroup('admin_group') || auth.hasGroup('office_group')" class="flex items-center gap-2 cursor-pointer text-sm text-gray-600 whitespace-nowrap">
            <input type="checkbox" v-model="filters.showArchived" @change="loadClients" class="rounded" />
            Архивные
          </label>

          <!-- Сброс фильтров -->
          <button
            v-if="hasActiveFilters"
            @click="resetFilters"
            class="btn btn-secondary text-sm flex items-center gap-1"
          >
            <X class="w-4 h-4" />Сбросить
          </button>
        </div>
      </div>

      <!-- Таблица -->
      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <template v-else>
        <DataTable
          :columns="columns"
          :rows="clients"
          storage-key="clients-table-v1"
          :row-class="rowClass"
          :total="total"
          :page="page"
          :page-size="pageSize"
          :loading="loading"
          @row-click="onRowClick"
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
          @reload="loadClients"
        >
          <!-- Название -->
          <template #name="{ row }">
            <div
              class="flex items-center gap-2 min-w-0 cursor-pointer"
              @click.stop="openClientQuick(row)"
            >
              <div class="w-7 h-7 bg-primary-100 rounded-md flex-shrink-0 flex items-center justify-center">
                <Building2 class="w-4 h-4 text-primary-600" />
              </div>
              <div class="min-w-0">
                <div class="font-medium text-gray-900 truncate hover:text-primary-600 hover:underline">{{ row.name }}</div>
                <div v-if="row.inn" class="text-xs text-gray-400 truncate">ИНН: {{ row.inn }}</div>
              </div>
            </div>
          </template>

          <!-- Контакт -->
          <template #contacts="{ row }">
            <span class="text-gray-300">—</span>
          </template>

          <!-- Объекты -->
          <template #sites_count="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="row.sites_count > 0 ? 'text-blue-700' : 'text-gray-400'"
              @click.stop="row.sites_count > 0 && openSitesQuick(row)"
            >
              <MapPin class="w-3.5 h-3.5" />{{ row.sites_count ?? 0 }}
            </span>
          </template>

          <!-- Договоры -->
          <template #contracts_count="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="row.contracts_count > 0 ? 'text-violet-700' : 'text-gray-400'"
              @click.stop="row.contracts_count > 0 && openContractsQuick(row)"
            >
              <FileText class="w-3.5 h-3.5" />{{ row.contracts_count ?? 0 }}
            </span>
          </template>

          <!-- Выезды -->
          <template #visits_count="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="row.visits_count > 0 ? 'text-green-700' : 'text-gray-400'"
              @click.stop="row.visits_count > 0 && router.push(`/clients/${row.id}?tab=visits`)"
            >
              <CalendarCheck class="w-3.5 h-3.5" />{{ row.visits_count ?? 0 }}
            </span>
          </template>

          <!-- Статус -->
          <template #status="{ row }">
            <span v-if="row.is_archived" class="badge bg-gray-100 text-gray-500 text-xs px-2 py-0.5 rounded-full">Архив</span>
            <span v-else-if="row.is_active" class="badge bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">Активен</span>
            <span v-else class="badge bg-yellow-100 text-yellow-700 text-xs px-2 py-0.5 rounded-full">Неактивен</span>
          </template>

          <!-- Действия -->
          <template #actions="{ row }">
            <div class="flex items-center gap-1" @click.stop>
              <button
                v-if="!row.is_archived"
                @click="openEdit(row)"
                class="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700"
                title="Редактировать"
              >
                <Edit class="w-4 h-4" />
              </button>
              <button
                v-if="!row.is_archived"
                @click="archiveConfirm = row"
                class="p-1.5 rounded hover:bg-amber-50 text-gray-400 hover:text-amber-600"
                title="В архив"
              >
                <Archive class="w-4 h-4" />
              </button>
              <button
                v-if="row.is_archived && (auth.hasGroup('admin_group') || auth.hasGroup('office_group'))"
                @click="handleUnarchive(row)"
                class="p-1.5 rounded hover:bg-green-50 text-gray-400 hover:text-green-600"
                title="Восстановить"
              >
                <ArchiveRestore class="w-4 h-4" />
              </button>
            </div>
          </template>

          <template #empty>
            <div class="flex flex-col items-center py-8 text-gray-400">
              <Building2 class="w-12 h-12 mb-3 text-gray-200" />
              <p>Клиенты не найдены</p>
            </div>
          </template>
        </DataTable>

      </template>

      <!-- Create / Edit Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-4 md:p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">
              {{ editing ? 'Редактировать клиента' : 'Добавить клиента' }}
            </h2>
            <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-4 md:p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
              <input v-model="form.name" class="input" :class="{ 'border-red-400': errors.name }" placeholder='ООО "Название"' @input="delete errors.name" />
              <p v-if="errors.name" class="text-red-600 text-xs mt-1">{{ errors.name }}</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">ИНН</label>
                <input v-model="form.inn" class="input" :class="{ 'border-red-400': errors.inn }" placeholder="1234567890" @input="delete errors.inn" />
                <p v-if="errors.inn" class="text-red-600 text-xs mt-1">{{ errors.inn }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">КПП</label>
                <input v-model="form.kpp" class="input" :class="{ 'border-red-400': errors.kpp }" placeholder="123456789" @input="delete errors.kpp" />
                <p v-if="errors.kpp" class="text-red-600 text-xs mt-1">{{ errors.kpp }}</p>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
              <textarea v-model="form.notes" class="input" rows="3" placeholder="Дополнительная информация..." />
            </div>
            <div class="flex justify-end gap-3 pt-4">
              <button type="button" @click="modalOpen = false" class="btn btn-secondary">Отмена</button>
              <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
                {{ saving ? 'Сохранение...' : (editing ? 'Сохранить' : 'Создать') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Quick: Клиент -->
      <ClientQuickModal
        v-if="quickClient"
        :client="quickClient"
        @close="quickClient = null"
        @open-page="router.push(`/clients/${quickClient.id}`); quickClient = null"
      />

      <!-- Quick: Список объектов клиента -->
      <SiteListModal
        v-if="quickSitesList"
        :sites="quickSitesList"
        @close="quickSitesList = null"
        @select="onSiteSelect"
      />

      <!-- Quick: Объект -->
      <SiteQuickModal
        v-if="quickSite"
        :site="quickSite"
        @close="quickSite = null"
        @open-page="router.push(`/sites/${quickSite.id}`); quickSite = null"
        @open-client="quickSite.client_id && router.push(`/clients/${quickSite.client_id}`); quickSite = null"
      />

      <!-- Quick: Список договоров клиента -->
      <ContractListModal
        v-if="quickContractsList"
        :contracts="quickContractsList"
        @close="quickContractsList = null"
        @select="onContractSelect"
      />

      <!-- Quick: Договор -->
      <ContractQuickModal
        v-if="quickContract"
        :contract="quickContract"
        @close="quickContract = null"
        @open-page="router.push(`/contracts/${quickContract.id}`); quickContract = null"
        @open-client="quickContract.client_id && router.push(`/clients/${quickContract.client_id}`); quickContract = null"
        @open-site="(s) => { quickContract = null; onSiteSelect(s) }"
      />

      <!-- Archive Confirm -->
      <div v-if="archiveConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-4 md:p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Отправить в архив?</h2>
          <p class="text-gray-600 mb-1">Клиент <strong>{{ archiveConfirm.name }}</strong> будет скрыт из основного списка.</p>
          <p class="text-sm text-gray-500 mb-6">Все данные и история выездов сохранятся.</p>
          <div class="flex justify-end gap-3">
            <button @click="archiveConfirm = null" class="btn btn-secondary">Отмена</button>
            <button @click="handleArchive" class="btn bg-amber-600 text-white hover:bg-amber-700">В архив</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, Plus, Building2, Edit, Archive, ArchiveRestore, X,
  MapPin, FileText, CalendarCheck, Filter, ChevronDown,
} from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import ClientQuickModal from '../components/modals/ClientQuickModal.vue'
import SiteQuickModal from '../components/modals/SiteQuickModal.vue'
import SiteListModal from '../components/modals/SiteListModal.vue'
import ContractQuickModal from '../components/modals/ContractQuickModal.vue'
import ContractListModal from '../components/modals/ContractListModal.vue'
import { clientsAPI, sitesAPI, contractsAPI } from '../services/api.js'
import { useAuthStore } from '../stores/auth.js'
import { useEscClose } from '../composables/useEscClose.js'

const router = useRouter()
const auth = useAuthStore()

const clients = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loading = ref(true)
const filtersOpen = ref(false)
const modalOpen = ref(false)
const editing = ref(null)
const archiveConfirm = ref(null)
const saving = ref(false)
const form = ref({ name: '', inn: '', kpp: '', notes: '' })
const originalForm = ref(null)
const errors = ref({})

// Quick modals
const quickClient = ref(null)
const quickSitesList = ref(null)
const quickSite = ref(null)
const quickContractsList = ref(null)
const quickContract = ref(null)

async function openClientQuick(row) {
  quickClient.value = row
}

async function openSitesQuick(row) {
  if (row.sites_count === 1) {
    // 1 объект — сразу открываем модалку объекта
    try {
      const res = await sitesAPI.getAll({ client_id: row.id, limit: 1 })
      const site = res.data.items?.[0]
      if (site) {
        const detail = await sitesAPI.getById(site.id)
        quickSite.value = detail.data
      }
    } catch { /* ignore */ }
  } else {
    // несколько — список
    try {
      const res = await sitesAPI.getAll({ client_id: row.id, limit: 200 })
      quickSitesList.value = res.data.items || []
    } catch { /* ignore */ }
  }
}

async function onSiteSelect(site) {
  quickSitesList.value = null
  try {
    const detail = await sitesAPI.getById(site.id)
    quickSite.value = detail.data
  } catch { /* ignore */ }
}

async function openContractsQuick(row) {
  try {
    const res = await contractsAPI.getByClient(row.id)
    const list = Array.isArray(res.data) ? res.data : (res.data?.items || [])
    if (list.length === 1) {
      const detail = await contractsAPI.getById(list[0].id)
      quickContract.value = detail.data
    } else {
      quickContractsList.value = list
    }
  } catch { /* ignore */ }
}

async function onContractSelect(contract) {
  quickContractsList.value = null
  try {
    const detail = await contractsAPI.getById(contract.id)
    quickContract.value = detail.data
  } catch { /* ignore */ }
}

useEscClose([
  { isOpen: () => !!quickContract.value,      close: () => { quickContract.value = null } },
  { isOpen: () => !!quickContractsList.value, close: () => { quickContractsList.value = null } },
  { isOpen: () => !!quickSite.value,          close: () => { quickSite.value = null } },
  { isOpen: () => !!quickSitesList.value,     close: () => { quickSitesList.value = null } },
  { isOpen: () => !!quickClient.value,        close: () => { quickClient.value = null } },
  { isOpen: () => modalOpen.value,            close: () => { modalOpen.value = false } },
  { isOpen: () => !!archiveConfirm.value,     close: () => { archiveConfirm.value = null } },
])

const filters = ref({
  search: '',
  status: '',      // '' | 'active' | 'inactive'
  showArchived: false,
})

const hasActiveFilters = computed(() =>
  filters.value.search || filters.value.status || filters.value.showArchived
)

const columns = [
  { key: 'name',            label: 'Клиент',      width: 280, sortable: true },
  { key: 'contacts',        label: 'Контакт',     width: 180, sortable: false },
  { key: 'sites_count',     label: 'Объекты',     width: 100, sortable: true },
  { key: 'contracts_count', label: 'Договоры',    width: 110, sortable: true },
  { key: 'visits_count',    label: 'Выезды',      width: 100, sortable: true },
  { key: 'status',          label: 'Статус',      width: 120, sortable: false },
  { key: 'actions',         label: '',            width: 90,  sortable: false },
]

function rowClass(row) {
  return row.is_archived ? 'opacity-60 bg-gray-50' : ''
}

function onRowClick(_row) {
  // клики обрабатываются в ячейках через openClientQuick / openSitesQuick / openContractsQuick
}

function buildParams() {
  const p = {
    limit: pageSize.value,
    offset: (page.value - 1) * pageSize.value,
    show_archived: filters.value.showArchived || undefined,
  }
  if (filters.value.search) p.search = filters.value.search
  if (filters.value.status === 'active') p.active_only = true
  if (filters.value.status === 'inactive') p.inactive_only = true
  return p
}

async function loadClients() {
  loading.value = true
  try {
    const res = await clientsAPI.getAll(buildParams())
    clients.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onPageChange(p) {
  page.value = p
  loadClients()
}

function onPageSizeChange(s) {
  pageSize.value = s
  page.value = 1
  loadClients()
}

let searchTimer = null
function debouncedLoad() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadClients() }, 300)
}

function resetFilters() {
  filters.value = { search: '', status: '', showArchived: false }
  page.value = 1
  loadClients()
}

function validate() {
  const e = {}
  if (!form.value.name.trim()) e.name = 'Введите название'
  if (form.value.inn && !/^\d{10}(\d{2})?$/.test(form.value.inn)) e.inn = 'ИНН должен содержать 10 или 12 цифр'
  if (form.value.kpp && !/^\d{9}$/.test(form.value.kpp)) e.kpp = 'КПП должен содержать 9 цифр'
  errors.value = e
  return Object.keys(e).length === 0
}

function openCreate() {
  editing.value = null
  errors.value = {}
  form.value = { name: '', inn: '', kpp: '', notes: '' }
  modalOpen.value = true
}

function openEdit(c) {
  editing.value = c
  errors.value = {}
  form.value = { name: c.name, inn: c.inn || '', kpp: c.kpp || '', notes: c.notes || '' }
  originalForm.value = { ...form.value }
  modalOpen.value = true
}

async function handleSave() {
  if (!validate()) return
  saving.value = true
  try {
    if (editing.value) {
      if (JSON.stringify(form.value) === JSON.stringify(originalForm.value)) {
        modalOpen.value = false
        return
      }
      await clientsAPI.update(editing.value.id, form.value)
    } else {
      await clientsAPI.create(form.value)
    }
    modalOpen.value = false
    errors.value = {}
    await loadClients()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleArchive() {
  try {
    await clientsAPI.archive(archiveConfirm.value.id)
    archiveConfirm.value = null
    await loadClients()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleUnarchive(c) {
  try {
    await clientsAPI.unarchive(c.id)
    await loadClients()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(loadClients)
</script>
