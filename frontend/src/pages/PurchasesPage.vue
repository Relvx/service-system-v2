<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Закупки</h1>
          <p class="text-gray-600 mt-1">Показано: {{ purchases.length }} из {{ total }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Добавить закупку
        </button>
      </div>

      <!-- Filters -->
      <div class="card mb-4">
        <div class="flex flex-wrap gap-3 items-end">
          <!-- Статус -->
          <div class="min-w-[160px]">
            <label class="block text-xs text-gray-400 mb-1">Статус</label>
            <select v-model="filterStatus" @change="loadPurchases" class="input text-sm">
              <option value="">Все статусы</option>
              <option v-for="s in cfg.purchaseStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
            </select>
          </div>
          <!-- Объект -->
          <div class="min-w-[200px] flex-1 max-w-xs">
            <label class="block text-xs text-gray-400 mb-1">Объект</label>
            <select v-model="filterSiteId" @change="loadPurchases" class="input text-sm">
              <option value="">Все объекты</option>
              <option v-for="s in activeSites" :key="s.id" :value="s.id">{{ s.title }}</option>
            </select>
          </div>
          <!-- Архивные -->
          <label v-if="auth.hasGroup('admin_group')" class="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none whitespace-nowrap pb-1">
            <input type="checkbox" v-model="showArchived" @change="loadPurchases" class="rounded" />
            Архивные
          </label>
          <!-- Сброс -->
          <button
            v-if="filterStatus || filterSiteId || showArchived"
            @click="resetPurchaseFilters"
            class="btn btn-secondary text-sm flex items-center gap-1 pb-1"
          >
            <X class="w-4 h-4" />Сбросить
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <DataTable
        v-else
        :columns="columns"
        :rows="purchases"
        storage-key="purchases_table"
        :row-class="purchaseRowClass"
        @row-click="openDetail"
      >
        <template #status="{ row }">
          <div class="flex items-center gap-2" @click.stop>
            <select
              :value="row._newStatus"
              @change="updateStatus(row, $event.target.value)"
              class="input text-sm py-1.5 flex-1"
              :disabled="row.is_archived"
            >
              <option v-for="s in cfg.purchaseStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
            </select>
          </div>
        </template>

        <template #due_date="{ row }">
          {{ formatDate(row.due_date) }}
        </template>

        <template #actions="{ row }">
          <div class="flex items-center gap-1">
            <span v-if="row.is_archived" class="text-xs text-gray-400 italic">Архив</span>
            <template v-else>
              <button
                v-if="row.status === 'installed'"
                @click="archivePurchase(row)"
                class="text-xs text-orange-600 hover:text-orange-800 font-medium px-2 py-1 rounded hover:bg-orange-50"
                title="Перенести в архив"
              >
                В архив
              </button>
            </template>
            <button
              v-if="row.is_archived && auth.hasGroup('admin_group')"
              @click="unarchivePurchase(row)"
              class="text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1 rounded hover:bg-blue-50"
            >
              Восстановить
            </button>
          </div>
        </template>

        <template #empty>
          <div class="flex flex-col items-center gap-2">
            <ShoppingCart class="w-12 h-12 text-gray-300" />
            <span>Закупки не найдены</span>
          </div>
        </template>
      </DataTable>

      <!-- Infinite scroll sentinel -->
      <div ref="sentinelRef" class="h-4 mt-2"></div>
      <div v-if="loadingMore" class="flex justify-center py-4">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>

      <!-- Detail / Edit Modal -->
      <div v-if="detailPurchase" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">{{ detailPurchase.item }}</h2>
              <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full mt-1" :class="statusBadgeClass(detailPurchase.status)">
                {{ cfg.purchaseStatusLabel(detailPurchase.status) }}
              </span>
            </div>
            <button @click="detailPurchase = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleEditSave" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Наименование *</label>
              <input
                v-model="editForm.item"
                class="input"
                :class="{ 'border-red-400': editErrors.item }"
                :disabled="detailPurchase.is_archived"
                @input="delete editErrors.item"
              />
              <p v-if="editErrors.item" class="text-red-600 text-xs mt-1">{{ editErrors.item }}</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Кол-во *</label>
                <input
                  v-model="editForm.qty"
                  type="number" step="0.01" min="0.01"
                  class="input"
                  :class="{ 'border-red-400': editErrors.qty }"
                  :disabled="detailPurchase.is_archived"
                  @input="delete editErrors.qty"
                />
                <p v-if="editErrors.qty" class="text-red-600 text-xs mt-1">{{ editErrors.qty }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Срок</label>
                <input v-model="editForm.due_date" type="date" class="input" :disabled="detailPurchase.is_archived" />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Статус</label>
              <select v-model="editForm.status" class="input" :disabled="detailPurchase.is_archived">
                <option v-for="s in cfg.purchaseStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Объект</label>
              <select v-model="editForm.site_id" class="input" :disabled="detailPurchase.is_archived" @change="editForm.defect_id = null">
                <option :value="null">— не выбран —</option>
                <option v-for="s in sites" :key="s.id" :value="s.id">{{ s.title }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Дефект</label>
              <select v-model="editForm.defect_id" class="input" :disabled="detailPurchase.is_archived">
                <option :value="null">— не связан —</option>
                <option
                  v-for="d in editFilteredDefects"
                  :key="d.id"
                  :value="d.id"
                >{{ d.title }}{{ d.site_title ? ` (${d.site_title})` : '' }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
              <textarea v-model="editForm.notes" class="input" rows="2" :disabled="detailPurchase.is_archived" />
            </div>
            <div class="flex justify-end gap-3 pt-4">
              <button type="button" @click="detailPurchase = null" class="btn btn-secondary">Отмена</button>
              <button
                v-if="!detailPurchase.is_archived"
                type="submit"
                :disabled="editSaving"
                class="btn btn-primary disabled:opacity-50"
              >
                {{ editSaving ? 'Сохранение...' : 'Сохранить' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Create Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">Добавить закупку</h2>
            <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Наименование *</label>
              <input
                v-model="form.item"
                class="input"
                :class="{ 'border-red-400': errors.item }"
                placeholder="Насос циркуляционный Grundfos"
                @input="delete errors.item"
              />
              <p v-if="errors.item" class="text-red-600 text-xs mt-1">{{ errors.item }}</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Кол-во *</label>
                <input
                  v-model="form.qty"
                  type="number"
                  step="0.01"
                  min="0.01"
                  class="input"
                  :class="{ 'border-red-400': errors.qty }"
                  @input="delete errors.qty"
                />
                <p v-if="errors.qty" class="text-red-600 text-xs mt-1">{{ errors.qty }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Срок</label>
                <input v-model="form.due_date" type="date" class="input" />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Объект</label>
              <select v-model="form.site_id" class="input" @change="form.defect_id = null">
                <option :value="null">— не выбран —</option>
                <option v-for="s in sites" :key="s.id" :value="s.id">{{ s.title }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Дефект</label>
              <select v-model="form.defect_id" class="input">
                <option :value="null">— не связан —</option>
                <option
                  v-for="d in filteredDefects"
                  :key="d.id"
                  :value="d.id"
                >{{ d.title }}{{ d.site_title ? ` (${d.site_title})` : '' }}</option>
              </select>
              <p class="text-xs text-gray-400 mt-1">Фильтруется по выбранному объекту</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
              <textarea v-model="form.notes" class="input" rows="2" />
            </div>
            <div class="flex justify-end gap-3 pt-4">
              <button type="button" @click="modalOpen = false" class="btn btn-secondary">Отмена</button>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Plus, ShoppingCart, X } from 'lucide-vue-next'

import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import { useConfigStore } from '../stores/config.js'
import { useAuthStore } from '../stores/auth.js'
import { purchasesAPI, sitesAPI, defectsAPI } from '../services/api.js'
import { useEscClose } from '../composables/useEscClose.js'

const cfg = useConfigStore()
const auth = useAuthStore()

const purchases = ref([])
const total = ref(0)
const loadingMore = ref(false)
const LIMIT = 50
const sentinelRef = ref(null)
let observer = null
const sites = ref([])
const defects = ref([])
const loading = ref(true)
const filterStatus = ref('')
const filterSiteId = ref('')
const showArchived = ref(false)
const modalOpen = ref(false)
const saving = ref(false)
const form = ref({ item: '', qty: 1, due_date: '', notes: '', site_id: null, defect_id: null })
const errors = ref({})

const detailPurchase = ref(null)
const editForm = ref({})
const originalEditForm = ref(null)
const editErrors = ref({})
const editSaving = ref(false)

useEscClose([
  { isOpen: () => modalOpen.value,           close: () => { modalOpen.value = false } },
  { isOpen: () => !!detailPurchase.value,    close: () => { detailPurchase.value = null } },
])

// Только не-архивные объекты для фильтра
const activeSites = computed(() => sites.value.filter(s => !s.is_archived))

function resetPurchaseFilters() {
  filterStatus.value = ''
  filterSiteId.value = ''
  showArchived.value = false
  loadPurchases()
}

const columns = [
  { key: 'item',         label: 'Наименование', width: 220 },
  { key: 'qty',          label: 'Кол-во',       width: 80 },
  { key: 'status',       label: 'Статус',       width: 180, sortable: false },
  { key: 'site_title',   label: 'Объект',       width: 170 },
  { key: 'defect_title', label: 'Дефект',       width: 150, defaultVisible: false },
  { key: 'due_date',     label: 'Срок',         width: 110 },
  { key: 'notes',        label: 'Заметки',      width: 200, defaultVisible: false },
  { key: 'actions',      label: '',             width: 110, sortable: false },
]

// Дефекты, отфильтрованные по выбранному объекту в форме
const filteredDefects = computed(() => {
  if (!form.value.site_id) return defects.value
  return defects.value.filter(d => d.site_id === form.value.site_id)
})

const editFilteredDefects = computed(() => {
  if (!editForm.value.site_id) return defects.value
  return defects.value.filter(d => d.site_id === editForm.value.site_id)
})

function purchaseRowClass(row) {
  if (row.is_archived) return 'opacity-50'
  const m = {
    draft:     'bg-gray-50',
    approved:  'bg-blue-50',
    ordered:   'bg-yellow-50',
    received:  'bg-cyan-50',
    installed: 'bg-orange-50',
    closed:    'bg-green-50',
  }
  return m[row.status] || ''
}

function statusBadgeClass(s) {
  const m = {
    draft:     'bg-gray-100 text-gray-700',
    approved:  'bg-blue-100 text-blue-700',
    ordered:   'bg-yellow-100 text-yellow-800',
    received:  'bg-cyan-100 text-cyan-800',
    installed: 'bg-orange-100 text-orange-700',
    closed:    'bg-green-100 text-green-700',
  }
  return m[s] || 'bg-gray-100 text-gray-700'
}

function openDetail(row) {
  detailPurchase.value = row
  editForm.value = {
    item:      row.item,
    qty:       row.qty,
    due_date:  row.due_date || '',
    notes:     row.notes || '',
    site_id:   row.site_id || null,
    defect_id: row.defect_id || null,
    status:    row.status,
  }
  originalEditForm.value = { ...editForm.value }
  editErrors.value = {}
}

function validateEdit() {
  const e = {}
  if (!editForm.value.item.trim()) e.item = 'Укажите наименование'
  const qty = parseFloat(editForm.value.qty)
  if (!qty || qty <= 0) e.qty = 'Количество должно быть больше 0'
  editErrors.value = e
  return Object.keys(e).length === 0
}

async function handleEditSave() {
  if (!validateEdit()) return
  editSaving.value = true
  try {
    const payload = {
      item:      editForm.value.item.trim(),
      qty:       parseFloat(editForm.value.qty) || 1,
      due_date:  editForm.value.due_date || null,
      notes:     editForm.value.notes || null,
      site_id:   editForm.value.site_id || null,
      defect_id: editForm.value.defect_id || null,
      status:    editForm.value.status,
    }
    if (JSON.stringify(editForm.value) === JSON.stringify(originalEditForm.value)) {
      detailPurchase.value = null
      return
    }
    const res = await purchasesAPI.update(detailPurchase.value.id, payload)
    const idx = purchases.value.findIndex(x => x.id === detailPurchase.value.id)
    if (idx >= 0) purchases.value[idx] = { ...res.data, _newStatus: res.data.status }
    detailPurchase.value = null
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    editSaving.value = false
  }
}

function buildPurchaseParams() {
  const params = {}
  if (filterStatus.value) params.status = filterStatus.value
  if (filterSiteId.value) params.site_id = filterSiteId.value
  if (showArchived.value) params.show_archived = true
  return params
}

async function loadPurchases() {
  loading.value = true
  try {
    const res = await purchasesAPI.getAll({ ...buildPurchaseParams(), limit: LIMIT, offset: 0 })
    purchases.value = res.data.items.map((p) => ({ ...p, _newStatus: p.status }))
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || purchases.value.length >= total.value) return
  loadingMore.value = true
  try {
    const res = await purchasesAPI.getAll({ ...buildPurchaseParams(), limit: LIMIT, offset: purchases.value.length })
    purchases.value.push(...res.data.items.map((p) => ({ ...p, _newStatus: p.status })))
    total.value = res.data.total
  } finally {
    loadingMore.value = false
  }
}

function setupObserver() {
  if (observer) observer.disconnect()
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) loadMore()
  }, { threshold: 0.1 })
  if (sentinelRef.value) observer.observe(sentinelRef.value)
}

async function loadSites() {
  const res = await sitesAPI.getAll({ limit: 500 })
  sites.value = res.data.items
}

async function loadDefects() {
  const res = await defectsAPI.getAll({ limit: 500 })
  defects.value = res.data.items
}

async function updateStatus(p, newStatus) {
  try {
    const res = await purchasesAPI.update(p.id, { status: newStatus })
    const idx = purchases.value.findIndex((x) => x.id === p.id)
    if (idx >= 0) purchases.value[idx] = { ...res.data, _newStatus: res.data.status }
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function archivePurchase(p) {
  try {
    await purchasesAPI.archive(p.id)
    await loadPurchases()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function unarchivePurchase(p) {
  try {
    await purchasesAPI.unarchive(p.id)
    await loadPurchases()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

function validate() {
  const e = {}
  if (!form.value.item.trim()) e.item = 'Укажите наименование'
  const qty = parseFloat(form.value.qty)
  if (!qty || qty <= 0) e.qty = 'Количество должно быть больше 0'
  errors.value = e
  return Object.keys(e).length === 0
}

function openCreate() {
  form.value = { item: '', qty: 1, due_date: '', notes: '', site_id: null, defect_id: null }
  errors.value = {}
  modalOpen.value = true
}

async function handleSave() {
  if (!validate()) return
  saving.value = true
  try {
    const payload = {
      item: form.value.item.trim(),
      qty: parseFloat(form.value.qty) || 1,
      due_date: form.value.due_date || null,
      notes: form.value.notes || null,
      site_id: form.value.site_id || null,
      defect_id: form.value.defect_id || null,
    }
    await purchasesAPI.create(payload)
    modalOpen.value = false
    await loadPurchases()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }

onMounted(async () => {
  await Promise.all([loadPurchases(), loadSites(), loadDefects()])
  setupObserver()
})
onUnmounted(() => { if (observer) observer.disconnect() })
</script>
