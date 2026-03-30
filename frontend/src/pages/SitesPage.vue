<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between flex-wrap gap-y-3 mb-4">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Объекты</h1>
          <p class="text-gray-600 mt-1">Показано: {{ sites.length }} из {{ total }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Добавить объект
        </button>
      </div>

      <!-- Фильтры -->
      <div class="card mb-4">
        <button class="md:hidden w-full flex items-center justify-between text-sm font-medium text-gray-700 mb-2" @click="filtersOpen = !filtersOpen">
          <span class="flex items-center gap-2"><Filter class="w-4 h-4" />Фильтры<span v-if="hasActiveFilters" class="w-2 h-2 bg-primary-500 rounded-full inline-block"></span></span>
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="filtersOpen ? 'rotate-180' : ''" />
        </button>
        <div :class="filtersOpen ? 'flex' : 'hidden md:flex'" class="flex-wrap gap-3 items-end">
          <div class="relative flex-1 min-w-[200px]">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              v-model="filters.search"
              @input="debouncedLoad"
              type="text"
              placeholder="Поиск по названию или адресу..."
              class="input pl-9 text-sm"
            />
          </div>

          <!-- Частота обслуживания -->
          <div class="min-w-[170px]">
            <select v-model="filters.serviceFrequency" @change="loadSites" class="input text-sm">
              <option value="">Все частоты</option>
              <option v-for="f in cfg.serviceFrequencies" :key="f.sysname" :value="f.sysname">{{ f.display_name }}</option>
            </select>
          </div>

          <!-- Архивные (только admin) -->
          <label v-if="auth.hasGroup('admin_group')" class="flex items-center gap-2 cursor-pointer text-sm text-gray-600 whitespace-nowrap">
            <input type="checkbox" v-model="filters.showArchived" @change="loadSites" class="rounded" />
            Архивные
          </label>

          <button
            v-if="hasActiveFilters"
            @click="resetFilters"
            class="btn btn-secondary text-sm flex items-center gap-1"
          >
            <X class="w-4 h-4" />Сбросить
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <template v-else>
        <DataTable
          :columns="columns"
          :rows="filteredSites"
          storage-key="sites-table-v1"
          :row-class="rowClass"
          :total="total"
          :page="page"
          :page-size="pageSize"
          :loading="loading"
          @row-click="onRowClick"
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
          @reload="loadSites"
        >
          <!-- Название / адрес -->
          <template #title="{ row }">
            <div
              class="flex items-center gap-2 min-w-0 cursor-pointer"
              @click.stop="openSiteQuick(row)"
            >
              <div class="w-7 h-7 bg-green-100 rounded-md flex-shrink-0 flex items-center justify-center">
                <Building2 class="w-4 h-4 text-green-600" />
              </div>
              <div class="min-w-0">
                <div class="font-medium text-gray-900 truncate hover:text-green-700 hover:underline">{{ row.title }}</div>
                <div class="text-xs text-gray-400 truncate">{{ row.address }}</div>
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

          <!-- Контакт на месте -->
          <template #onsite_contact="{ row }">
            <span v-if="row.onsite_contact" class="truncate block text-gray-700 text-sm">{{ row.onsite_contact }}</span>
            <span v-else class="text-gray-300">—</span>
          </template>

          <!-- Частота -->
          <template #service_frequency="{ row }">
            <span v-if="row.service_frequency" class="text-sm text-gray-700">{{ cfg.serviceFrequencyLabel(row.service_frequency) }}</span>
            <span v-else class="text-gray-300">—</span>
          </template>

          <!-- Договоры -->
          <template #contracts_count="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="(row.contracts_count || 0) > 0 ? 'text-violet-700' : 'text-gray-400'"
              @click.stop="(row.contracts_count || 0) > 0 && openContractsQuick(row)"
            >
              <FileText class="w-3.5 h-3.5" />{{ row.contracts_count ?? 0 }}
            </span>
          </template>

          <!-- Выезды -->
          <template #total_visits="{ row }">
            <span
              class="inline-flex items-center gap-1 text-sm font-medium cursor-pointer hover:underline"
              :class="(row.total_visits || 0) > 0 ? 'text-green-700' : 'text-gray-400'"
              @click.stop="(row.total_visits || 0) > 0 && router.push(`/sites/${row.id}?tab=visits`)"
            >
              <CalendarCheck class="w-3.5 h-3.5" />{{ row.total_visits || 0 }}
            </span>
          </template>

          <!-- Статус -->
          <template #status="{ row }">
            <span v-if="row.is_archived" class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Архив</span>
            <span v-else class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Активен</span>
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
                v-if="row.is_archived && auth.hasGroup('admin_group')"
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
              <p>Объекты не найдены</p>
            </div>
          </template>
        </DataTable>

      </template>

      <!-- Create/Edit Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ editing ? 'Редактировать объект' : 'Добавить объект' }}</h2>
            <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
              <input v-model="form.title" class="input" :class="{ 'border-red-400': errors.title }" placeholder="Котельная №1" @input="delete errors.title" />
              <p v-if="errors.title" class="text-red-600 text-xs mt-1">{{ errors.title }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Адрес *</label>
              <div class="flex gap-2">
                <input v-model="form.address" class="input flex-1" :class="{ 'border-red-400': errors.address }" placeholder="г. Москва, ул. Ленина, д. 1" @input="delete errors.address" />
                <button type="button" :disabled="geocoding || !form.address.trim()" @click="handleGeocode"
                  class="btn btn-secondary text-sm px-3 disabled:opacity-50 whitespace-nowrap flex items-center gap-1">
                  <MapPin class="w-3.5 h-3.5" />
                  {{ geocoding ? '...' : 'Координаты' }}
                </button>
              </div>
              <p v-if="errors.address" class="text-red-600 text-xs mt-1">{{ errors.address }}</p>
              <p v-if="geocodeError" class="text-red-600 text-xs mt-1">{{ geocodeError }}</p>
            </div>
            <div class="relative">
              <label class="block text-sm font-medium text-gray-700 mb-1">Клиент</label>
              <input
                v-model="clientSearch"
                type="text"
                class="input"
                placeholder="Начните вводить название клиента..."
                @focus="clientDropdownOpen = true"
                @input="form.client_id = ''; clientDropdownOpen = true"
                @blur="setTimeout(() => clientDropdownOpen = false, 150)"
                autocomplete="off"
              />
              <div
                v-if="clientDropdownOpen && filteredClients.length"
                class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
              >
                <button
                  type="button"
                  class="w-full text-left px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 border-b border-gray-100"
                  @mousedown.prevent="form.client_id = ''; clientSearch = ''; clientDropdownOpen = false"
                >— Не выбран —</button>
                <button
                  v-for="c in filteredClients"
                  :key="c.id"
                  type="button"
                  class="w-full text-left px-3 py-2 text-sm hover:bg-primary-50 hover:text-primary-700"
                  :class="{ 'bg-primary-50 text-primary-700': form.client_id === c.id }"
                  @mousedown.prevent="form.client_id = c.id; clientSearch = c.name; clientDropdownOpen = false"
                >{{ c.name }}</button>
              </div>
              <p v-if="form.client_id" class="text-xs text-green-600 mt-1 flex items-center gap-1">
                <span>✓</span> Выбран клиент
              </p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Широта</label>
                <input v-model="form.latitude" type="number" step="any" class="input" :class="{ 'border-red-400': errors.latitude }" placeholder="55.751244" @input="delete errors.latitude" />
                <p v-if="errors.latitude" class="text-red-600 text-xs mt-1">{{ errors.latitude }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Долгота</label>
                <input v-model="form.longitude" type="number" step="any" class="input" :class="{ 'border-red-400': errors.longitude }" placeholder="37.618423" @input="delete errors.longitude" />
                <p v-if="errors.longitude" class="text-red-600 text-xs mt-1">{{ errors.longitude }}</p>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Контакт на месте</label>
              <input v-model="form.onsite_contact" class="input" placeholder="Иванов И.И., тел. 8-999-000-00-00" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Доступ</label>
              <textarea v-model="form.access_notes" class="input" rows="2" placeholder="Ключ у охранника, код домофона..." />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Частота обслуживания</label>
              <select v-model="form.service_frequency" class="input">
                <option value="">Не указано</option>
                <option v-for="f in cfg.serviceFrequencies" :key="f.sysname" :value="f.sysname">{{ f.display_name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Стоимость выездов (руб.)</label>
              <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                <div><label class="block text-xs text-gray-500 mb-1">ТО</label><input v-model="form.price_maintenance" type="number" step="any" min="0" class="input" placeholder="0" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">Ремонт</label><input v-model="form.price_repair" type="number" step="any" min="0" class="input" placeholder="0" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">Аварийный</label><input v-model="form.price_emergency" type="number" step="any" min="0" class="input" placeholder="0" /></div>
              </div>
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

      <!-- Quick: Список договоров объекта -->
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
        @open-client="quickContract.client_id && openClientQuick(quickContract.client_id); quickContract = null"
        @open-site="(s) => { quickContract = null; openSiteQuick(s) }"
      />

      <!-- Archive Confirm -->
      <div v-if="archiveConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Отправить в архив?</h2>
          <p class="text-gray-600 mb-1">Объект <strong>{{ archiveConfirm.title }}</strong> будет скрыт из основного списка.</p>
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
import { useRouter, useRoute } from 'vue-router'
import { Search, Plus, MapPin, Building2, X, Edit, Archive, ArchiveRestore, CalendarCheck, FileText, Filter, ChevronDown } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import SiteQuickModal from '../components/modals/SiteQuickModal.vue'
import ClientQuickModal from '../components/modals/ClientQuickModal.vue'
import ContractQuickModal from '../components/modals/ContractQuickModal.vue'
import ContractListModal from '../components/modals/ContractListModal.vue'
import { useConfigStore } from '../stores/config.js'
import { useAuthStore } from '../stores/auth.js'
import { sitesAPI, clientsAPI, contractsAPI } from '../services/api.js'
import { useEscClose } from '../composables/useEscClose.js'

const cfg = useConfigStore()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const sites = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const clientsList = ref([])
const loading = ref(true)

const filtersOpen = ref(false)
const modalOpen = ref(false)
const editing = ref(null)
const archiveConfirm = ref(null)
const saving = ref(false)
const form = ref({ title: '', address: '', client_id: '', latitude: '', longitude: '', onsite_contact: '', access_notes: '', service_frequency: 'monthly', price_maintenance: '', price_repair: '', price_emergency: '' })
const originalForm = ref(null)
const errors = ref({})
const clientSearch = ref('')
const clientDropdownOpen = ref(false)
const geocoding = ref(false)
const geocodeError = ref('')

// Quick modals
const quickSite = ref(null)
const quickClient = ref(null)
const quickContractsList = ref(null)
const quickContract = ref(null)

async function openSiteQuick(row) {
  try {
    const detail = await sitesAPI.getById(row.id)
    quickSite.value = detail.data
  } catch { /* ignore */ }
}

async function openClientQuick(clientId) {
  try {
    const detail = await clientsAPI.getById(clientId)
    quickClient.value = detail.data
  } catch { /* ignore */ }
}

async function openContractsQuick(row) {
  try {
    const res = await contractsAPI.getAll({ site_id: row.id, limit: 200 })
    const list = res.data?.items || []
    if (list.length === 1) {
      const detail = await contractsAPI.getById(list[0].id)
      quickContract.value = detail.data
    } else if (list.length > 1) {
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
  { isOpen: () => !!quickClient.value,        close: () => { quickClient.value = null } },
  { isOpen: () => modalOpen.value,            close: () => { modalOpen.value = false } },
  { isOpen: () => !!archiveConfirm.value,     close: () => { archiveConfirm.value = null } },
])

const filters = ref({
  search: '',
  serviceFrequency: '',
  showArchived: false,
})

const hasActiveFilters = computed(() =>
  filters.value.search || filters.value.serviceFrequency || filters.value.showArchived
)

// Клиентский фильтр по service_frequency (бэк не поддерживает этот фильтр)
const filteredSites = computed(() => {
  if (!filters.value.serviceFrequency) return sites.value
  return sites.value.filter(s => s.service_frequency === filters.value.serviceFrequency)
})

const columns = [
  { key: 'title',             label: 'Объект',          width: 280, sortable: true },
  { key: 'client_name',       label: 'Клиент',          width: 180, sortable: true },
  { key: 'onsite_contact',    label: 'Контакт на месте', width: 180, sortable: false },
  { key: 'service_frequency', label: 'Частота',         width: 150, sortable: true },
  { key: 'contracts_count',   label: 'Договоры',        width: 110, sortable: true },
  { key: 'total_visits',      label: 'Выезды',          width: 100, sortable: true },
  { key: 'status',            label: 'Статус',          width: 110, sortable: false },
  { key: 'actions',           label: '',               width: 90,  sortable: false },
]

function rowClass(row) {
  return row.is_archived ? 'opacity-60 bg-gray-50' : ''
}

function onRowClick(_row) {
  // клики обрабатываются в ячейках
}

const filteredClients = computed(() => {
  const q = clientSearch.value.toLowerCase()
  if (!q) return clientsList.value
  return clientsList.value.filter(c => c.name.toLowerCase().includes(q))
})

function buildParams() {
  const p = {
    limit: pageSize.value,
    offset: (page.value - 1) * pageSize.value,
    show_archived: filters.value.showArchived || undefined,
  }
  if (filters.value.search) p.search = filters.value.search
  return p
}

async function loadSites() {
  loading.value = true
  try {
    const res = await sitesAPI.getAll(buildParams())
    sites.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onPageChange(p) { page.value = p; loadSites() }
function onPageSizeChange(s) { pageSize.value = s; page.value = 1; loadSites() }

let searchTimer = null
function debouncedLoad() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadSites() }, 300)
}

function resetFilters() {
  filters.value = { search: '', serviceFrequency: '', showArchived: false }
  page.value = 1
  loadSites()
}

async function loadClients() {
  const res = await clientsAPI.getAll({ active_only: true, limit: 500 })
  clientsList.value = res.data.items
}

function validate() {
  const e = {}
  if (!form.value.title.trim()) e.title = 'Введите название'
  if (!form.value.address.trim()) e.address = 'Введите адрес'
  const lat = parseFloat(form.value.latitude)
  if (form.value.latitude !== '' && (isNaN(lat) || lat < -90 || lat > 90)) e.latitude = 'Широта должна быть от −90 до 90'
  const lon = parseFloat(form.value.longitude)
  if (form.value.longitude !== '' && (isNaN(lon) || lon < -180 || lon > 180)) e.longitude = 'Долгота должна быть от −180 до 180'
  errors.value = e
  return Object.keys(e).length === 0
}

function openCreate() {
  editing.value = null
  errors.value = {}
  geocodeError.value = ''
  form.value = { title: '', address: '', client_id: '', latitude: '', longitude: '', onsite_contact: '', access_notes: '', service_frequency: 'monthly', price_maintenance: '', price_repair: '', price_emergency: '' }
  clientSearch.value = ''
  clientDropdownOpen.value = false
  modalOpen.value = true
}

function openEdit(s) {
  editing.value = s
  errors.value = {}
  geocodeError.value = ''
  form.value = { title: s.title, address: s.address, client_id: s.client_id || '', latitude: s.latitude || '', longitude: s.longitude || '', onsite_contact: s.onsite_contact || '', access_notes: s.access_notes || '', service_frequency: s.service_frequency || 'monthly', price_maintenance: s.price_maintenance || '', price_repair: s.price_repair || '', price_emergency: s.price_emergency || '' }
  originalForm.value = { ...form.value }
  clientSearch.value = s.client_name || ''
  clientDropdownOpen.value = false
  modalOpen.value = true
}

async function handleGeocode() {
  if (!form.value.address.trim()) return
  geocoding.value = true
  geocodeError.value = ''
  try {
    const res = await sitesAPI.geocodeAddress(form.value.address)
    form.value.latitude = res.data.latitude
    form.value.longitude = res.data.longitude
  } catch {
    geocodeError.value = 'Не удалось определить координаты. Проверьте адрес.'
  } finally {
    geocoding.value = false
  }
}

async function handleSave() {
  if (!validate()) return
  saving.value = true
  try {
    const payload = { ...form.value, client_id: form.value.client_id || null, latitude: form.value.latitude || null, longitude: form.value.longitude || null, price_maintenance: form.value.price_maintenance || null, price_repair: form.value.price_repair || null, price_emergency: form.value.price_emergency || null }
    if (editing.value) {
      if (JSON.stringify(form.value) === JSON.stringify(originalForm.value)) {
        modalOpen.value = false
        return
      }
      await sitesAPI.update(editing.value.id, payload)
    } else {
      await sitesAPI.create(payload)
    }
    modalOpen.value = false
    errors.value = {}
    await loadSites()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleArchive() {
  try {
    await sitesAPI.archive(archiveConfirm.value.id)
    archiveConfirm.value = null
    await loadSites()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleUnarchive(s) {
  try {
    await sitesAPI.unarchive(s.id)
    await loadSites()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(async () => {
  await Promise.all([loadSites(), loadClients()])
  if (route.query.create === '1') openCreate()
})
</script>
