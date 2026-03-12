<template>
  <Layout>
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>

    <div v-else-if="site">
      <!-- Шапка -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <button @click="$router.back()" class="text-gray-500 hover:text-gray-700">
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div>
            <h1 class="text-3xl font-bold text-gray-900">{{ site.title }}</h1>
            <p v-if="site.client_name" class="text-gray-500 mt-0.5 text-sm">{{ site.client_name }}</p>
          </div>
          <span v-if="site.is_archived" class="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">Архив</span>
        </div>
        <button v-if="!site.is_archived" @click="openEdit" class="btn btn-secondary flex items-center">
          <Edit class="w-4 h-4 mr-2" />Редактировать
        </button>
      </div>

      <!-- Вкладки -->
      <div class="border-b mb-6">
        <nav class="flex gap-6">
          <button
            v-for="tab in tabs" :key="tab.key"
            @click="activeTab = tab.key"
            class="pb-3 text-sm font-medium border-b-2 transition-colors"
            :class="activeTab === tab.key
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'"
          >
            {{ tab.label }}
            <span v-if="tab.count !== undefined" class="ml-1 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">{{ tab.count }}</span>
          </button>
        </nav>
      </div>

      <!-- Основное -->
      <div v-if="activeTab === 'main'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card space-y-4">
          <h3 class="font-semibold text-gray-900">Основная информация</h3>
          <div><p class="text-sm text-gray-500">Название</p><p class="text-gray-900">{{ site.title }}</p></div>
          <div><p class="text-sm text-gray-500">Адрес</p><p class="text-gray-900">{{ site.address }}</p></div>
          <div v-if="site.onsite_contact"><p class="text-sm text-gray-500">Контакт на месте</p><p class="text-gray-900">{{ site.onsite_contact }}</p></div>
          <div v-if="site.access_notes"><p class="text-sm text-gray-500">Описание доступа</p><p class="text-gray-900 whitespace-pre-wrap">{{ site.access_notes }}</p></div>
          <div v-if="site.service_frequency"><p class="text-sm text-gray-500">Частота обслуживания</p><p class="text-gray-900">{{ cfg.serviceFrequencyLabel(site.service_frequency) }}</p></div>
          <div v-if="site.latitude"><p class="text-sm text-gray-500">Координаты</p><p class="text-gray-900 text-sm font-mono">{{ site.latitude }}, {{ site.longitude }}</p></div>
        </div>

        <div class="card space-y-4">
          <h3 class="font-semibold text-gray-900">Стоимость выездов</h3>
          <div>
            <p class="text-sm text-gray-500">Техническое обслуживание</p>
            <p class="text-gray-900">{{ site.price_maintenance ? site.price_maintenance.toLocaleString('ru-RU') + ' ₽' : '—' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Ремонт</p>
            <p class="text-gray-900">{{ site.price_repair ? site.price_repair.toLocaleString('ru-RU') + ' ₽' : '—' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Аварийный выезд</p>
            <p class="text-gray-900">{{ site.price_emergency ? site.price_emergency.toLocaleString('ru-RU') + ' ₽' : '—' }}</p>
          </div>
        </div>
      </div>

      <!-- Активные дефекты -->
      <div v-if="activeTab === 'defects'">
        <div v-if="site.active_defects.length === 0" class="text-center py-12 text-gray-500">
          <ShieldCheck class="w-12 h-12 mx-auto mb-3 text-gray-300" />
          Активных дефектов нет
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="d in site.active_defects" :key="d.id"
            class="card flex items-start justify-between gap-4"
          >
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-900">{{ d.title }}</p>
              <p v-if="d.description" class="text-sm text-gray-600 mt-0.5 truncate">{{ d.description }}</p>
              <p class="text-xs text-gray-400 mt-1">{{ formatDate(d.created_at) }}</p>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="priorityClass(d.priority)">
                {{ cfg.priorityLabel(d.priority) }}
              </span>
              <span class="text-xs px-2 py-0.5 rounded-full" :class="defectStatusClass(d.status)">
                {{ cfg.defectStatusLabel(d.status) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Файлы -->
      <div v-if="activeTab === 'files'">
        <AttachmentsTab entity-type="site" :entity-id="site.id" />
      </div>

      <!-- История выездов -->
      <div v-if="activeTab === 'visits'">
        <div class="flex justify-end mb-4">
          <button @click="openCreateVisit" class="btn btn-primary flex items-center gap-2">
            <Plus class="w-4 h-4" />Создать выезд
          </button>
        </div>
        <div v-if="site.recent_visits.length === 0" class="text-center py-12 text-gray-500">
          <Calendar class="w-12 h-12 mx-auto mb-3 text-gray-300" />
          Выездов пока нет
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="v in site.recent_visits" :key="v.id"
            class="card flex items-center justify-between gap-4"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <p class="font-medium text-gray-900">{{ formatDate(v.planned_date) }}</p>
                <span class="text-xs px-2 py-0.5 rounded-full" :class="visitStatusClass(v.status)">
                  {{ cfg.visitStatusLabel(v.status) }}
                </span>
              </div>
              <p class="text-sm text-gray-600 mt-0.5">
                {{ cfg.visitTypeLabel(v.visit_type) }}
                <span v-if="v.master_name"> · {{ v.master_name }}</span>
              </p>
              <p v-if="v.work_summary" class="text-xs text-gray-400 mt-0.5 truncate">{{ v.work_summary }}</p>
            </div>
            <div class="flex items-center gap-3 flex-shrink-0">
              <span v-if="v.cost" class="text-sm font-medium text-gray-700">{{ v.cost.toLocaleString('ru-RU') }} ₽</span>
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="priorityClass(v.priority)">
                {{ cfg.priorityLabel(v.priority) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12 text-gray-500">Объект не найден</div>

    <!-- Create Visit Modal -->
    <div v-if="visitModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 flex flex-col max-h-[90vh]">
        <div class="flex items-center justify-between p-6 border-b flex-shrink-0">
          <h2 class="text-xl font-semibold text-gray-900">Создать выезд</h2>
          <button @click="visitModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleCreateVisit" class="p-6 space-y-4 overflow-y-auto flex-1">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Мастер *</label>
            <select v-model="visitForm.assigned_user_id" class="input" required>
              <option value="">— Выберите мастера —</option>
              <option v-for="m in masters" :key="m.id" :value="m.id">{{ m.full_name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Дата *</label>
            <input v-model="visitForm.planned_date" type="date" class="input" required />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Время с</label>
              <input v-model="visitForm.planned_time_from" type="time" class="input" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Время до</label>
              <input v-model="visitForm.planned_time_to" type="time" class="input" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Тип выезда</label>
            <select v-model="visitForm.visit_type" class="input">
              <option v-for="t in cfg.visitTypes" :key="t.sysname" :value="t.sysname">{{ t.display_name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Приоритет</label>
            <select v-model="visitForm.priority" class="input">
              <option v-for="p in cfg.priorities" :key="p.sysname" :value="p.sysname">{{ p.display_name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Стоимость (₽)</label>
            <input v-model="visitForm.cost" type="number" step="any" min="0" class="input" :placeholder="costPlaceholder" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Заметки офиса</label>
            <textarea v-model="visitForm.office_notes" class="input" rows="2" />
          </div>
        </form>
        <div class="flex justify-end gap-3 p-6 border-t flex-shrink-0">
          <button type="button" @click="visitModalOpen = false" class="btn btn-secondary">Отмена</button>
          <button @click="handleCreateVisit" :disabled="visitSaving" class="btn btn-primary disabled:opacity-50">
            {{ visitSaving ? 'Создание...' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">Редактировать объект</h2>
          <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleSave" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
            <input v-model="form.title" required class="input" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Адрес *</label>
            <input v-model="form.address" required class="input" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Контакт на месте</label>
            <input v-model="form.onsite_contact" class="input" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Описание доступа</label>
            <textarea v-model="form.access_notes" class="input" rows="2" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Частота обслуживания</label>
            <select v-model="form.service_frequency" class="input">
              <option value="">Не указано</option>
              <option v-for="f in cfg.serviceFrequencies" :key="f.sysname" :value="f.sysname">{{ f.display_name }}</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div><label class="block text-sm font-medium text-gray-700 mb-1">Широта</label><input v-model="form.latitude" type="number" step="any" class="input" /></div>
            <div><label class="block text-sm font-medium text-gray-700 mb-1">Долгота</label><input v-model="form.longitude" type="number" step="any" class="input" /></div>
          </div>
          <p class="text-sm font-medium text-gray-700 -mb-2">Стоимость выездов (руб.)</p>
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-xs text-gray-500 mb-1">ТО</label>
              <input v-model="form.price_maintenance" type="number" step="any" min="0" class="input" placeholder="0" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Ремонт</label>
              <input v-model="form.price_repair" type="number" step="any" min="0" class="input" placeholder="0" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Аварийный</label>
              <input v-model="form.price_emergency" type="number" step="any" min="0" class="input" placeholder="0" />
            </div>
          </div>
          <div class="flex justify-end gap-3 pt-4">
            <button type="button" @click="modalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Edit, X, ShieldCheck, Calendar, Plus } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import AttachmentsTab from '../components/AttachmentsTab.vue'
import { useConfigStore } from '../stores/config.js'
import { sitesAPI, visitsAPI, usersAPI } from '../services/api.js'

const cfg = useConfigStore()
const route = useRoute()
const site = ref(null)
const loading = ref(true)
const modalOpen = ref(false)
const saving = ref(false)
const activeTab = ref('main')
const form = ref({})

// Create visit
const visitModalOpen = ref(false)
const visitSaving = ref(false)
const masters = ref([])
const visitForm = ref({})

const costPlaceholder = computed(() => {
  if (!site.value) return ''
  const map = { maintenance: site.value.price_maintenance, repair: site.value.price_repair, emergency: site.value.price_emergency }
  const val = map[visitForm.value.visit_type]
  return val ? String(val) : ''
})

const tabs = computed(() => [
  { key: 'main', label: 'Основное' },
  { key: 'defects', label: 'Дефекты', count: site.value?.active_defects?.length ?? 0 },
  { key: 'visits', label: 'История выездов', count: site.value?.recent_visits?.length ?? 0 },
  { key: 'files', label: 'Файлы и фото' },
])

async function loadSite() {
  loading.value = true
  try {
    const res = await sitesAPI.getById(route.params.id)
    site.value = res.data
  } finally {
    loading.value = false
  }
}

async function openCreateVisit() {
  if (!masters.value.length) {
    const res = await usersAPI.getMasters()
    masters.value = res.data
  }
  visitForm.value = {
    assigned_user_id: '',
    planned_date: '',
    planned_time_from: '',
    planned_time_to: '',
    visit_type: 'maintenance',
    priority: 'medium',
    cost: '',
    office_notes: '',
  }
  visitModalOpen.value = true
}

async function handleCreateVisit() {
  if (!visitForm.value.assigned_user_id || !visitForm.value.planned_date) return
  visitSaving.value = true
  try {
    await visitsAPI.create({
      site_id: Number(route.params.id),
      assigned_user_id: visitForm.value.assigned_user_id,
      planned_date: visitForm.value.planned_date,
      planned_time_from: visitForm.value.planned_time_from || null,
      planned_time_to: visitForm.value.planned_time_to || null,
      visit_type: visitForm.value.visit_type,
      priority: visitForm.value.priority,
      cost: visitForm.value.cost || null,
      office_notes: visitForm.value.office_notes || null,
    })
    visitModalOpen.value = false
    await loadSite()
    activeTab.value = 'visits'
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    visitSaving.value = false
  }
}

function openEdit() {
  form.value = {
    title: site.value.title,
    address: site.value.address,
    onsite_contact: site.value.onsite_contact || '',
    access_notes: site.value.access_notes || '',
    service_frequency: site.value.service_frequency || '',
    latitude: site.value.latitude || '',
    longitude: site.value.longitude || '',
    price_maintenance: site.value.price_maintenance || '',
    price_repair: site.value.price_repair || '',
    price_emergency: site.value.price_emergency || '',
  }
  modalOpen.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const payload = {
      ...form.value,
      latitude: form.value.latitude || null,
      longitude: form.value.longitude || null,
      price_maintenance: form.value.price_maintenance || null,
      price_repair: form.value.price_repair || null,
      price_emergency: form.value.price_emergency || null,
    }
    await sitesAPI.update(route.params.id, payload)
    modalOpen.value = false
    await loadSite()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function formatDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('ru-RU')
}

function priorityClass(p) {
  return {
    critical: 'bg-red-100 text-red-700',
    high: 'bg-orange-100 text-orange-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-gray-100 text-gray-600',
  }[p] || 'bg-gray-100 text-gray-600'
}

function defectStatusClass(s) {
  return {
    open: 'bg-red-50 text-red-600',
    in_progress: 'bg-blue-50 text-blue-600',
    fixed: 'bg-green-50 text-green-600',
    cancelled: 'bg-gray-50 text-gray-500',
  }[s] || 'bg-gray-50 text-gray-500'
}

function visitStatusClass(s) {
  return {
    planned: 'bg-blue-50 text-blue-600',
    in_progress: 'bg-green-50 text-green-600',
    closed: 'bg-gray-100 text-gray-500',
    cancelled: 'bg-red-50 text-red-500',
  }[s] || 'bg-gray-50 text-gray-500'
}

onMounted(loadSite)
</script>
