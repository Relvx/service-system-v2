<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Выезды</h1>
          <p class="text-gray-600 mt-1">Всего: {{ visits.length }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Создать выезд
        </button>
      </div>

      <!-- Filters -->
      <div class="card mb-6">
        <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-3">
          <select v-model="filters.status" class="input">
            <option value="">Все статусы</option>
            <option v-for="s in cfg.visitStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
          </select>
          <select v-model="filters.priority" class="input">
            <option value="">Все приоритеты</option>
            <option v-for="p in cfg.priorities" :key="p.sysname" :value="p.sysname">{{ p.display_name }}</option>
          </select>
          <input v-model="filters.date_from" type="date" class="input" />
          <input v-model="filters.date_to" type="date" class="input" />
          <button @click="loadVisits" class="btn btn-primary flex items-center justify-center">
            <Filter class="w-5 h-5 mr-2" />Применить
          </button>
        </div>
        <label v-if="auth.hasGroup('admin_group')" class="flex items-center gap-2 cursor-pointer text-sm text-gray-600">
          <input type="checkbox" v-model="showArchived" @change="loadVisits" class="rounded" />
          Показать архивные
        </label>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <DataTable v-else :columns="columns" :rows="visits" storage-key="visits_table">
        <template #planned_date="{ row }">
          <span class="whitespace-nowrap">{{ formatDate(row.planned_date) }}</span>
          <span v-if="row.planned_time_from" class="text-gray-500 text-xs block">{{ row.planned_time_from.slice(0,5) }}</span>
        </template>

        <template #status="{ row }">
          <div class="flex flex-col gap-1">
            <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full w-fit" :class="statusClass(row.status)">
              {{ cfg.visitStatusLabel(row.status) }}
            </span>
            <span v-if="row.is_archived" class="inline-flex px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded-full w-fit">Архив</span>
          </div>
        </template>

        <template #priority="{ row }">
          <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="priorityClass(row.priority)">
            {{ cfg.priorityLabel(row.priority) }}
          </span>
        </template>

        <template #visit_type="{ row }">
          <span class="text-gray-700">{{ cfg.visitTypeLabel(row.visit_type) }}</span>
        </template>

        <template #actions="{ row }">
          <div class="flex items-center gap-2">
            <template v-if="!row.is_archived">
              <button @click="openEdit(row)" class="text-gray-500 hover:text-primary-600" title="Редактировать">
                <Pencil class="w-4 h-4" />
              </button>
              <button @click="openDetail(row)" class="text-primary-600 hover:text-primary-900" title="Подробнее">
                <Eye class="w-4 h-4" />
              </button>
              <button @click="archiveConfirm = row" class="text-amber-600 hover:text-amber-800" title="В архив">
                <Archive class="w-4 h-4" />
              </button>
            </template>
            <template v-else>
              <button @click="openDetail(row)" class="text-primary-600 hover:text-primary-900" title="Подробнее">
                <Eye class="w-4 h-4" />
              </button>
              <button v-if="auth.hasGroup('admin_group')" @click="handleUnarchive(row)" class="text-green-600 hover:text-green-800" title="Восстановить">
                <ArchiveRestore class="w-4 h-4" />
              </button>
            </template>
          </div>
        </template>

        <template #empty>
          <div class="flex flex-col items-center gap-2">
            <Calendar class="w-12 h-12 text-gray-300" />
            <span>Выезды не найдены</span>
          </div>
        </template>
      </DataTable>

      <!-- Detail Modal -->
      <div v-if="detailVisit" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ detailVisit.site_title }}</h2>
            <button @click="detailVisit = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <div class="p-6 space-y-4">
            <div class="flex gap-2">
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="statusClass(detailVisit.status)">{{ cfg.visitStatusLabel(detailVisit.status) }}</span>
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="priorityClass(detailVisit.priority)">{{ cfg.priorityLabel(detailVisit.priority) }}</span>
            </div>
            <div><p class="text-sm text-gray-500">Адрес</p><p class="text-gray-900">{{ detailVisit.site_address }}</p></div>
            <div class="grid grid-cols-2 gap-4">
              <div><p class="text-sm text-gray-500">Дата</p><p class="text-gray-900">{{ formatDate(detailVisit.planned_date) }}</p></div>
              <div><p class="text-sm text-gray-500">Время</p><p class="text-gray-900">{{ detailVisit.planned_time_from?.slice(0,5) || '—' }} — {{ detailVisit.planned_time_to?.slice(0,5) || '—' }}</p></div>
            </div>
            <div><p class="text-sm text-gray-500">Мастер</p><p class="text-gray-900">{{ detailVisit.master_name || 'Не назначен' }}</p></div>
            <div><p class="text-sm text-gray-500">Тип</p><p class="text-gray-900">{{ cfg.visitTypeLabel(detailVisit.visit_type) }}</p></div>
            <div v-if="detailVisit.client_name"><p class="text-sm text-gray-500">Клиент</p><p class="text-gray-900">{{ detailVisit.client_name }}</p></div>
            <div v-if="detailVisit.work_summary"><p class="text-sm text-gray-500">Итог работ</p><p class="text-gray-900">{{ detailVisit.work_summary }}</p></div>
            <div v-if="detailVisit.office_notes"><p class="text-sm text-gray-500">Заметки офиса</p><p class="text-gray-900">{{ detailVisit.office_notes }}</p></div>
            <div v-if="detailVisit.recommendations"><p class="text-sm text-gray-500">Рекомендации</p><p class="text-gray-900">{{ detailVisit.recommendations }}</p></div>
            <div v-if="attachments.length > 0">
              <p class="text-sm text-gray-500 mb-2 flex items-center gap-1"><ImageIcon class="w-4 h-4" /> Фотографии ({{ attachments.length }})</p>
              <div class="flex flex-wrap gap-2">
                <img v-for="a in attachments" :key="a.id" :src="a.file_url" @click="() => openUrl(a.file_url)"
                  class="w-20 h-20 object-cover rounded-lg border border-gray-200 cursor-pointer hover:opacity-80" />
              </div>
            </div>
          </div>
          <div class="flex justify-end gap-3 p-6 border-t">
            <button v-if="!detailVisit.is_archived" @click="openEdit(detailVisit)" class="btn btn-secondary flex items-center"><Pencil class="w-4 h-4 mr-2" />Редактировать</button>
            <button @click="detailVisit = null" class="btn btn-primary">Закрыть</button>
          </div>
        </div>
      </div>

      <!-- Create / Edit Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ editing ? 'Редактировать выезд' : 'Создать выезд' }}</h2>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Объект *</label>
              <select v-model="form.site_id" class="input" :class="{ 'border-red-400': errors.site_id }" @change="delete errors.site_id">
                <option value="">Выберите объект</option>
                <option v-for="s in sites" :key="s.id" :value="s.id">{{ s.title }} — {{ s.address }}</option>
              </select>
              <p v-if="errors.site_id" class="text-red-600 text-xs mt-1">{{ errors.site_id }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Мастер</label>
              <select v-model="form.assigned_user_id" class="input">
                <option value="">Не назначен</option>
                <option v-for="m in masters" :key="m.id" :value="m.id">{{ m.full_name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Дата *</label>
              <input v-model="form.planned_date" type="date" class="input" :class="{ 'border-red-400': errors.planned_date }" @input="delete errors.planned_date" />
              <p v-if="errors.planned_date" class="text-red-600 text-xs mt-1">{{ errors.planned_date }}</p>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div><label class="block text-sm font-medium text-gray-700 mb-1">Время с</label><input v-model="form.planned_time_from" type="time" class="input" /></div>
              <div><label class="block text-sm font-medium text-gray-700 mb-1">Время до</label><input v-model="form.planned_time_to" type="time" class="input" /></div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Тип</label>
                <select v-model="form.visit_type" class="input">
                  <option v-for="t in cfg.visitTypes" :key="t.sysname" :value="t.sysname">{{ t.display_name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Приоритет</label>
                <select v-model="form.priority" class="input">
                  <option v-for="p in cfg.priorities" :key="p.sysname" :value="p.sysname">{{ p.display_name }}</option>
                </select>
              </div>
            </div>
            <div v-if="editing">
              <label class="block text-sm font-medium text-gray-700 mb-1">Статус</label>
              <select v-model="form.status" class="input">
                <option v-for="s in cfg.visitStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
              <textarea v-model="form.office_notes" class="input" rows="3" placeholder="Дополнительная информация..." />
            </div>
            <div class="flex justify-end gap-3 pt-4">
              <button type="button" @click="closeModal" class="btn btn-secondary">Отмена</button>
              <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
                {{ saving ? 'Сохранение...' : (editing ? 'Сохранить' : 'Создать') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Archive Confirm -->
      <div v-if="archiveConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Отправить в архив?</h2>
          <p class="text-gray-600 mb-1">Выезд <strong>{{ archiveConfirm.site_title }}</strong> будет скрыт из основного списка.</p>
          <p class="text-sm text-gray-500 mb-6">Все данные сохранятся.</p>
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
import { ref, onMounted, watch } from 'vue'
import { Plus, Calendar, MapPin, User, Filter, X, Eye, Pencil, Archive, ArchiveRestore, Image as ImageIcon } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import { useConfigStore } from '../stores/config.js'
import { useAuthStore } from '../stores/auth.js'
import { visitsAPI, sitesAPI, usersAPI, attachmentsAPI } from '../services/api.js'

const cfg = useConfigStore()
const auth = useAuthStore()

const visits = ref([])
const loading = ref(true)
const filters = ref({ status: '', priority: '', date_from: '', date_to: '' })
const showArchived = ref(false)
const modalOpen = ref(false)
const detailVisit = ref(null)
const editing = ref(null)
const saving = ref(false)
const archiveConfirm = ref(null)
const sites = ref([])
const masters = ref([])
const attachments = ref([])
const errors = ref({})

const columns = [
  { key: 'planned_date', label: 'Дата',       width: 130 },
  { key: 'site_title',   label: 'Объект',     width: 200 },
  { key: 'site_address', label: 'Адрес',      width: 200, defaultVisible: false },
  { key: 'master_name',  label: 'Мастер',     width: 160 },
  { key: 'visit_type',   label: 'Тип',        width: 130 },
  { key: 'status',       label: 'Статус',     width: 140 },
  { key: 'priority',     label: 'Приоритет',  width: 130, defaultVisible: false },
  { key: 'actions',      label: 'Действия',   width: 110, sortable: false },
]

const form = ref({
  site_id: '', assigned_user_id: '', planned_date: '', planned_time_from: '',
  planned_time_to: '', visit_type: 'maintenance', priority: 'medium',
  office_notes: '', status: 'planned',
})

async function loadVisits() {
  loading.value = true
  try {
    const params = {}
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.priority) params.priority = filters.value.priority
    if (filters.value.date_from) params.date_from = filters.value.date_from
    if (filters.value.date_to) params.date_to = filters.value.date_to
    if (showArchived.value) params.show_archived = true
    const res = await visitsAPI.getAll(params)
    visits.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadFormData() {
  const [sr, mr] = await Promise.all([sitesAPI.getAll({ active_only: true }), usersAPI.getMasters()])
  sites.value = sr.data
  masters.value = mr.data
}

function validate() {
  const e = {}
  if (!form.value.site_id) e.site_id = 'Выберите объект'
  if (!form.value.planned_date) e.planned_date = 'Укажите дату'
  errors.value = e
  return Object.keys(e).length === 0
}

function openCreate() {
  editing.value = null
  errors.value = {}
  form.value = { site_id: '', assigned_user_id: '', planned_date: '', planned_time_from: '', planned_time_to: '', visit_type: 'maintenance', priority: 'medium', office_notes: '', status: 'planned' }
  loadFormData()
  modalOpen.value = true
}

function openEdit(v) {
  editing.value = v
  errors.value = {}
  form.value = {
    site_id: v.site_id || '', assigned_user_id: v.assigned_user_id || '',
    planned_date: v.planned_date?.slice(0, 10) || '', planned_time_from: v.planned_time_from?.slice(0, 5) || '',
    planned_time_to: v.planned_time_to?.slice(0, 5) || '', visit_type: v.visit_type || 'maintenance',
    priority: v.priority || 'medium', office_notes: v.office_notes || '', status: v.status || 'planned',
  }
  detailVisit.value = null
  loadFormData()
  modalOpen.value = true
}

async function openDetail(v) {
  try {
    const [vr, ar] = await Promise.all([visitsAPI.getById(v.id), attachmentsAPI.getAll(v.id)])
    detailVisit.value = vr.data
    attachments.value = ar.data
  } catch {
    detailVisit.value = v
    attachments.value = []
  }
}

async function handleSave() {
  if (!validate()) return
  saving.value = true
  try {
    const payload = {
      site_id: form.value.site_id, assigned_user_id: form.value.assigned_user_id || null,
      planned_date: form.value.planned_date, planned_time_from: form.value.planned_time_from || null,
      planned_time_to: form.value.planned_time_to || null, visit_type: form.value.visit_type,
      priority: form.value.priority, office_notes: form.value.office_notes || null,
    }
    if (editing.value) {
      await visitsAPI.update(editing.value.id, { ...payload, status: form.value.status })
    } else {
      await visitsAPI.create(payload)
    }
    closeModal()
    await loadVisits()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleArchive() {
  try {
    await visitsAPI.archive(archiveConfirm.value.id)
    archiveConfirm.value = null
    await loadVisits()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleUnarchive(v) {
  try {
    await visitsAPI.unarchive(v.id)
    await loadVisits()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

function closeModal() { modalOpen.value = false; editing.value = null; errors.value = {} }
function openUrl(url) { window.open(url, '_blank') }

function statusClass(s) {
  const m = { planned: 'bg-blue-100 text-blue-700', in_progress: 'bg-green-100 text-green-700', closed: 'bg-gray-400 text-white', done: 'bg-gray-400 text-white', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-700'
}
function priorityClass(p) {
  const m = { low: 'bg-gray-100 text-gray-600', medium: 'bg-yellow-100 text-yellow-700', high: 'bg-orange-100 text-orange-700', urgent: 'bg-red-100 text-red-700' }
  return m[p] || 'bg-gray-100 text-gray-700'
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }

watch(visits, (vl) => {
  const id = window.history.state?.openVisitId
  if (id && vl?.length) {
    const v = vl.find((x) => x.id === id)
    if (v) openDetail(v)
  }
}, { once: true })

onMounted(loadVisits)
</script>
