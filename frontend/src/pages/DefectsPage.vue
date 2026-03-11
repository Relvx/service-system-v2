<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Дефекты</h1>
          <p class="text-gray-600 mt-1">Всего: {{ defects.length }}</p>
        </div>
        <button
          v-if="canManage"
          @click="openCreateModal"
          class="btn btn-primary flex items-center gap-2"
        >
          <Plus class="w-4 h-4" /> Создать дефект
        </button>
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

      <DataTable v-else :columns="columns" :rows="defects" storage-key="defects_table" @row-click="openDetail($event)">
        <template #title="{ row }">
          <button @click="openDetail(row)" class="text-left hover:text-primary-600 font-medium truncate block w-full">
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

        <template #visit_date="{ row }">{{ formatDate(row.visit_date) }}</template>
        <template #created_at="{ row }">{{ formatDate(row.created_at) }}</template>

        <template #actions="{ row }">
          <button @click="openDetail(row)" class="text-primary-600 hover:text-primary-900" title="Подробнее">
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

      <!-- ─── Create Defect Modal ────────────────────────────────────────── -->
      <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">Новый дефект</h2>
            <button @click="showCreateModal = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Объект <span class="text-red-500">*</span></label>
              <select v-model="createForm.site_id" class="input" :class="{ 'border-red-500': createErrors.site_id }">
                <option :value="null">— Выберите объект —</option>
                <option v-for="s in sites" :key="s.id" :value="s.id">{{ s.title }}</option>
              </select>
              <p v-if="createErrors.site_id" class="text-red-500 text-xs mt-1">{{ createErrors.site_id }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Название <span class="text-red-500">*</span></label>
              <input v-model="createForm.title" type="text" class="input" :class="{ 'border-red-500': createErrors.title }" placeholder="Краткое описание проблемы" />
              <p v-if="createErrors.title" class="text-red-500 text-xs mt-1">{{ createErrors.title }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Описание</label>
              <textarea v-model="createForm.description" class="input" rows="3" placeholder="Подробное описание дефекта"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Приоритет</label>
                <select v-model="createForm.priority" class="input">
                  <option v-for="p in cfg.priorities" :key="p.sysname" :value="p.sysname">{{ p.display_name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Тип действия</label>
                <select v-model="createForm.action_type" class="input">
                  <option v-for="a in cfg.defectActionTypes" :key="a.sysname" :value="a.sysname">{{ a.display_name }}</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Необходимые запчасти</label>
              <textarea v-model="createForm.suggested_parts" class="input" rows="2" placeholder="Список запчастей и материалов"></textarea>
            </div>
          </div>
          <div class="p-6 border-t flex justify-end gap-3">
            <button @click="showCreateModal = false" class="btn btn-secondary">Отмена</button>
            <button @click="submitCreate" :disabled="saving" class="btn btn-primary disabled:opacity-50">
              {{ saving ? 'Сохранение...' : 'Создать' }}
            </button>
          </div>
        </div>
      </div>

      <!-- ─── Detail Modal ───────────────────────────────────────────────── -->
      <div v-if="selectedDefect" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ selectedDefect.title }}</h2>
            <button @click="closeDetail" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>

          <div class="p-6 space-y-4 text-sm">
            <!-- Badges -->
            <div class="flex gap-2">
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="defectStatusClass(selectedDefect.status)">{{ cfg.defectStatusLabel(selectedDefect.status) }}</span>
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="priorityClass(selectedDefect.priority)">{{ cfg.priorityLabel(selectedDefect.priority) }}</span>
            </div>

            <!-- Info -->
            <div class="grid grid-cols-2 gap-3">
              <div v-if="selectedDefect.site_title"><p class="text-gray-500">Объект</p><p class="font-medium">{{ selectedDefect.site_title }}</p></div>
              <div v-if="selectedDefect.client_name"><p class="text-gray-500">Клиент</p><p class="font-medium">{{ selectedDefect.client_name }}</p></div>
              <div v-if="selectedDefect.visit_date"><p class="text-gray-500">Дата выезда</p><p class="font-medium">{{ formatDate(selectedDefect.visit_date) }}</p></div>
              <div><p class="text-gray-500">Тип действия</p><p class="font-medium">{{ cfg.defectActionLabel(selectedDefect.action_type) }}</p></div>
            </div>
            <div v-if="selectedDefect.description"><p class="text-gray-500">Описание</p><p class="text-gray-900">{{ selectedDefect.description }}</p></div>
            <div v-if="selectedDefect.suggested_parts"><p class="text-gray-500">Необходимые запчасти</p><p class="text-gray-900">{{ selectedDefect.suggested_parts }}</p></div>

            <!-- Change status -->
            <div v-if="canManage" class="pt-3 border-t">
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

            <!-- ─── Photos ───────────────────────────────────────────── -->
            <div class="pt-3 border-t">
              <div class="flex items-center justify-between mb-3">
                <h3 class="font-semibold text-gray-800 flex items-center gap-2">
                  <ImageIcon class="w-4 h-4 text-gray-500" />Фотографии
                  <span v-if="defectPhotos.length" class="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">{{ defectPhotos.length }}</span>
                </h3>
                <label class="cursor-pointer btn btn-secondary text-xs flex items-center gap-1">
                  <Upload class="w-3 h-3" />
                  {{ uploadingPhoto ? 'Загрузка...' : 'Добавить фото' }}
                  <input type="file" accept="image/*,.pdf" class="hidden" :disabled="uploadingPhoto" @change="handlePhotoUpload" />
                </label>
              </div>
              <p v-if="uploadPhotoError" class="text-red-500 text-xs mb-2">{{ uploadPhotoError }}</p>
              <div v-if="defectPhotos.length" class="flex flex-wrap gap-2">
                <div v-for="att in defectPhotos" :key="att.id" class="relative group">
                  <a :href="att.file_url" target="_blank">
                    <img
                      v-if="/\.(jpg|jpeg|png|gif|webp)(\?|$)/i.test(att.file_url)"
                      :src="att.file_url"
                      class="w-20 h-20 object-cover rounded-lg border border-gray-200 hover:opacity-80 transition-opacity"
                    />
                    <div
                      v-else
                      class="w-20 h-20 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200 text-xs text-gray-500"
                    >
                      {{ att.file_name || 'Файл' }}
                    </div>
                  </a>
                  <button
                    @click="deletePhoto(att)"
                    class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                  >×</button>
                </div>
              </div>
              <p v-else class="text-sm text-gray-400">Фотографий нет</p>
            </div>

            <!-- ─── Purchases ─────────────────────────────────────────── -->
            <div class="pt-3 border-t">
              <div class="flex items-center justify-between mb-3">
                <h3 class="font-semibold text-gray-800">Закупки</h3>
                <button v-if="canManage" @click="showCreatePurchase = !showCreatePurchase" class="btn btn-secondary text-xs flex items-center gap-1">
                  <Plus class="w-3 h-3" /> Создать закупку
                </button>
              </div>

              <!-- Create purchase form -->
              <div v-if="showCreatePurchase" class="bg-gray-50 rounded-lg p-4 mb-3 space-y-3">
                <div>
                  <label class="block text-xs font-medium text-gray-700 mb-1">Наименование <span class="text-red-500">*</span></label>
                  <input v-model="purchaseForm.item" type="text" class="input text-sm" :class="{ 'border-red-500': purchaseErrors.item }" placeholder="Название запчасти или материала" />
                  <p v-if="purchaseErrors.item" class="text-red-500 text-xs mt-1">{{ purchaseErrors.item }}</p>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Количество</label>
                    <input v-model="purchaseForm.qty" type="number" min="0.01" step="0.01" class="input text-sm" />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Срок до</label>
                    <input v-model="purchaseForm.due_date" type="date" class="input text-sm" />
                  </div>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-700 mb-1">Заметки</label>
                  <input v-model="purchaseForm.notes" type="text" class="input text-sm" placeholder="Поставщик, артикул и т.д." />
                </div>
                <div class="flex justify-end gap-2">
                  <button @click="showCreatePurchase = false" class="btn btn-secondary text-xs">Отмена</button>
                  <button @click="submitPurchase" :disabled="savingPurchase" class="btn btn-primary text-xs disabled:opacity-50">
                    {{ savingPurchase ? 'Сохранение...' : 'Добавить' }}
                  </button>
                </div>
              </div>

              <!-- Purchases list -->
              <div v-if="loadingPurchases" class="text-center py-4 text-gray-400 text-sm">Загрузка...</div>
              <div v-else-if="defectPurchases.length === 0" class="text-center py-4 text-gray-400 text-sm">Закупок нет</div>
              <div v-else class="space-y-2">
                <div
                  v-for="p in defectPurchases"
                  :key="p.id"
                  class="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2"
                >
                  <div>
                    <p class="font-medium text-sm text-gray-900">{{ p.item }}</p>
                    <p class="text-xs text-gray-500">Кол-во: {{ p.qty }}<span v-if="p.due_date"> · до {{ formatDate(p.due_date) }}</span></p>
                  </div>
                  <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="purchaseStatusClass(p.status)">
                    {{ cfg.purchaseStatusLabel(p.status) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="p-6 border-t flex justify-end">
            <button @click="closeDetail" class="btn btn-primary">Закрыть</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { AlertTriangle, X, Eye, Plus, Image as ImageIcon, Upload } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import { useConfigStore } from '../stores/config.js'
import { useAuthStore } from '../stores/auth.js'
import { defectsAPI, purchasesAPI, sitesAPI, attachmentsAPI } from '../services/api.js'

const cfg = useConfigStore()
const auth = useAuthStore()

const canManage = auth.hasGroup('office_group') || auth.hasGroup('admin_group')

const defects = ref([])
const loading = ref(true)
const filterStatus = ref('')
const filterPriority = ref('')

// Detail
const selectedDefect = ref(null)
const newStatus = ref('')
const saving = ref(false)

// Photos in detail
const defectPhotos = ref([])
const uploadingPhoto = ref(false)
const uploadPhotoError = ref('')
const CLOUD_NAME = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME
const UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET

// Purchases in detail
const defectPurchases = ref([])
const loadingPurchases = ref(false)
const showCreatePurchase = ref(false)
const purchaseForm = ref({ item: '', qty: 1, due_date: '', notes: '' })
const purchaseErrors = ref({})
const savingPurchase = ref(false)

// Create defect
const showCreateModal = ref(false)
const sites = ref([])
const createForm = ref({ site_id: null, title: '', description: '', priority: 'medium', action_type: 'repair', suggested_parts: '' })
const createErrors = ref({})

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

async function openDetail(defect) {
  selectedDefect.value = defect
  showCreatePurchase.value = false
  purchaseForm.value = { item: '', qty: 1, due_date: '', notes: '' }
  purchaseErrors.value = {}
  defectPhotos.value = []
  uploadPhotoError.value = ''
  await Promise.all([loadPurchases(defect.id), loadPhotos(defect.id)])
}

function closeDetail() {
  selectedDefect.value = null
  showCreatePurchase.value = false
  defectPurchases.value = []
  defectPhotos.value = []
}

async function loadPhotos(defectId) {
  try {
    const res = await attachmentsAPI.getByDefect(defectId)
    defectPhotos.value = res.data
  } catch {}
}

async function handlePhotoUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  uploadingPhoto.value = true
  uploadPhotoError.value = ''
  try {
    const isImg = file.type.startsWith('image/')
    const resourceType = isImg ? 'image' : 'raw'
    const form = new FormData()
    form.append('file', file)
    form.append('upload_preset', UPLOAD_PRESET)
    const res = await fetch(
      `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/${resourceType}/upload`,
      { method: 'POST', body: form }
    )
    const data = await res.json()
    if (!data.secure_url) throw new Error()
    await attachmentsAPI.upload({
      defect_id: selectedDefect.value.id,
      kind: isImg ? 'photo' : 'document',
      file_url: data.secure_url,
      file_name: file.name,
    })
    await loadPhotos(selectedDefect.value.id)
  } catch {
    uploadPhotoError.value = 'Ошибка загрузки'
  } finally {
    uploadingPhoto.value = false
    e.target.value = ''
  }
}

async function deletePhoto(att) {
  try {
    await attachmentsAPI.delete(att.id)
    defectPhotos.value = defectPhotos.value.filter((a) => a.id !== att.id)
  } catch {}
}

async function loadPurchases(defectId) {
  loadingPurchases.value = true
  try {
    const res = await purchasesAPI.getAll({ defect_id: defectId })
    defectPurchases.value = res.data
  } finally {
    loadingPurchases.value = false
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

async function openCreateModal() {
  createForm.value = { site_id: null, title: '', description: '', priority: 'medium', action_type: 'repair', suggested_parts: '' }
  createErrors.value = {}
  showCreateModal.value = true
  if (sites.value.length === 0) {
    const res = await sitesAPI.getAll({ show_archived: false })
    sites.value = res.data
  }
}

function validateCreate() {
  const errors = {}
  if (!createForm.value.site_id) errors.site_id = 'Выберите объект'
  if (!createForm.value.title.trim()) errors.title = 'Введите название'
  createErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submitCreate() {
  if (!validateCreate()) return
  saving.value = true
  try {
    const payload = {
      site_id: createForm.value.site_id,
      title: createForm.value.title.trim(),
      description: createForm.value.description.trim() || null,
      priority: createForm.value.priority,
      action_type: createForm.value.action_type,
      suggested_parts: createForm.value.suggested_parts.trim() || null,
    }
    const res = await defectsAPI.create(payload)
    defects.value.unshift(res.data)
    showCreateModal.value = false
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function validatePurchase() {
  const errors = {}
  if (!purchaseForm.value.item.trim()) errors.item = 'Введите наименование'
  purchaseErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submitPurchase() {
  if (!validatePurchase()) return
  savingPurchase.value = true
  try {
    const payload = {
      defect_id: selectedDefect.value.id,
      site_id: selectedDefect.value.site_id,
      item: purchaseForm.value.item.trim(),
      qty: purchaseForm.value.qty,
      due_date: purchaseForm.value.due_date || null,
      notes: purchaseForm.value.notes.trim() || null,
    }
    const res = await purchasesAPI.create(payload)
    defectPurchases.value.unshift(res.data)
    showCreatePurchase.value = false
    purchaseForm.value = { item: '', qty: 1, due_date: '', notes: '' }
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    savingPurchase.value = false
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
function purchaseStatusClass(s) {
  const m = { draft: 'bg-gray-100 text-gray-600', approved: 'bg-blue-100 text-blue-700', ordered: 'bg-yellow-100 text-yellow-700', received: 'bg-cyan-100 text-cyan-700', installed: 'bg-orange-100 text-orange-700', closed: 'bg-green-100 text-green-700' }
  return m[s] || 'bg-gray-100 text-gray-700'
}
function formatDate(d) {
  if (!d) return '—'
  return new Date(d.includes('T') ? d : d + 'T00:00:00').toLocaleDateString('ru-RU')
}

onMounted(loadDefects)
</script>
