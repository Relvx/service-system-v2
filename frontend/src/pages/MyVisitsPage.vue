<template>
  <Layout>
    <div>
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">Мои выезды</h1>
        <p class="text-gray-600 mt-1">Привет, {{ user?.full_name }}</p>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-gray-200 mb-6">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === tab.id ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          {{ tab.label }} ({{ tab.count }})
        </button>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <div v-else class="space-y-4">
        <div v-for="v in filteredVisits" :key="v.id" class="card hover:shadow-md transition-shadow">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <h3 class="text-lg font-semibold text-gray-900">{{ v.site_title }}</h3>
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="statusClass(v.status)">
                  {{ cfg.visitStatusLabel(v.status) }}
                </span>
              </div>
              <div class="text-sm text-gray-600 space-y-1">
                <div class="flex items-center"><MapPin class="w-4 h-4 mr-2" />{{ v.site_address }}</div>
                <div class="flex items-center">
                  <Calendar class="w-4 h-4 mr-2" />{{ formatDate(v.planned_date) }}
                  <span v-if="v.planned_time_from"> в {{ v.planned_time_from.slice(0,5) }}</span>
                </div>
                <div v-if="v.client_name" class="flex items-center">
                  <Building2 class="w-4 h-4 mr-2" />{{ v.client_name }}
                </div>
              </div>
              <p v-if="v.office_notes" class="mt-2 text-sm text-primary-700 bg-primary-50 p-2 rounded">
                💬 {{ v.office_notes }}
              </p>
            </div>
            <div class="ml-4 flex flex-col gap-2">
              <button @click="openDetail(v)" class="btn btn-secondary text-sm py-1.5">
                <Eye class="w-4 h-4 mr-1 inline" />Подробнее
              </button>
              <button
                v-if="v.status === 'planned'"
                @click="startVisit(v)"
                :disabled="actionLoading === v.id"
                class="btn btn-primary text-sm py-1.5 flex items-center justify-center"
              >
                <Play class="w-4 h-4 mr-1" />Начать
              </button>
              <button
                v-if="v.status === 'in_progress'"
                @click="completeModal = v"
                class="btn bg-green-600 text-white hover:bg-green-700 text-sm py-1.5 flex items-center justify-center"
              >
                <CheckCircle class="w-4 h-4 mr-1" />Завершить
              </button>
            </div>
          </div>
        </div>

        <div v-if="filteredVisits.length === 0" class="text-center py-12 card">
          <Calendar class="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900">Нет выездов</h3>
        </div>
      </div>

      <!-- Detail Modal -->
      <div v-if="detailVisit" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ detailVisit.site_title }}</h2>
            <button @click="detailVisit = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <div class="p-6 space-y-3 text-sm">
            <div><p class="text-gray-500">Адрес</p><p class="text-gray-900">{{ detailVisit.site_address }}</p></div>
            <div><p class="text-gray-500">Дата</p><p class="text-gray-900">{{ formatDate(detailVisit.planned_date) }}</p></div>
            <div v-if="detailVisit.access_notes"><p class="text-gray-500">Доступ</p><p class="text-gray-900">{{ detailVisit.access_notes }}</p></div>
            <div v-if="detailVisit.onsite_contact"><p class="text-gray-500">Контакт на месте</p><p class="text-gray-900">{{ detailVisit.onsite_contact }}</p></div>
            <div v-if="detailVisit.office_notes"><p class="text-gray-500">Заметки офиса</p><p class="text-gray-900">{{ detailVisit.office_notes }}</p></div>
            <div v-if="detailVisit.client_contacts"><p class="text-gray-500">Контакты клиента</p><p class="text-gray-900">{{ detailVisit.client_contacts }}</p></div>
          </div>
          <div class="p-6 border-t flex justify-end">
            <button @click="detailVisit = null" class="btn btn-primary">Закрыть</button>
          </div>
        </div>
      </div>

      <!-- Complete Modal -->
      <div v-if="completeModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">Завершить выезд</h2>
            <button @click="completeModal = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleComplete" class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Итог работ *</label>
              <textarea v-model="completeForm.work_summary" required class="input" rows="4" placeholder="Опишите выполненные работы..." />
            </div>
            <div>
              <label class="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
                <input v-model="completeForm.defects_present" type="checkbox" class="w-4 h-4 rounded border-gray-300" />
                Обнаружены дефекты
              </label>
            </div>
            <div v-if="completeForm.defects_present">
              <label class="block text-sm font-medium text-gray-700 mb-1">Описание дефектов</label>
              <textarea v-model="completeForm.defects_summary" class="input" rows="3" placeholder="Описание дефектов..." />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Рекомендации</label>
              <textarea v-model="completeForm.recommendations" class="input" rows="2" placeholder="Рекомендации..." />
            </div>
            <PhotoUpload v-model="photos" label="Фото акта" />
            <div class="flex justify-end gap-3 pt-4">
              <button type="button" @click="completeModal = null" class="btn btn-secondary">Отмена</button>
              <button type="submit" :disabled="saving" class="btn bg-green-600 text-white hover:bg-green-700 disabled:opacity-50">
                {{ saving ? 'Сохранение...' : 'Завершить выезд' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Calendar, MapPin, Play, CheckCircle, X, Eye, Building2 } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import PhotoUpload from '../components/PhotoUpload.vue'
import { useAuthStore } from '../stores/auth.js'
import { useConfigStore } from '../stores/config.js'
import { visitsAPI, attachmentsAPI } from '../services/api.js'

const auth = useAuthStore()
const cfg = useConfigStore()
const user = computed(() => auth.user)

const visits = ref([])
const loading = ref(true)
const actionLoading = ref(null)
const completeModal = ref(null)
const detailVisit = ref(null)
const saving = ref(false)
const activeTab = ref('active')
const photos = ref([])

const completeForm = ref({ work_summary: '', defects_present: false, defects_summary: '', recommendations: '' })

const tabs = computed(() => [
  { id: 'active', label: 'Активные', count: visits.value.filter((v) => ['planned', 'in_progress'].includes(v.status)).length },
  { id: 'closed', label: 'Завершённые', count: visits.value.filter((v) => ['closed', 'done'].includes(v.status)).length },
  { id: 'all', label: 'Все', count: visits.value.length },
])

const filteredVisits = computed(() => {
  if (activeTab.value === 'active') return visits.value.filter((v) => ['planned', 'in_progress'].includes(v.status))
  if (activeTab.value === 'closed') return visits.value.filter((v) => ['closed', 'done'].includes(v.status))
  return visits.value
})

async function loadMyVisits() {
  loading.value = true
  try {
    const res = await visitsAPI.getAll({ master_id: user.value.id })
    visits.value = res.data
  } finally {
    loading.value = false
  }
}

async function startVisit(v) {
  actionLoading.value = v.id
  try {
    await visitsAPI.update(v.id, { status: 'in_progress' })
    await loadMyVisits()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    actionLoading.value = null
  }
}

async function openDetail(v) {
  try {
    const res = await visitsAPI.getById(v.id)
    detailVisit.value = res.data
  } catch {
    detailVisit.value = v
  }
}

async function handleComplete() {
  saving.value = true
  try {
    await visitsAPI.complete(completeModal.value.id, {
      work_summary: completeForm.value.work_summary,
      defects_present: completeForm.value.defects_present,
      defects_summary: completeForm.value.defects_summary || null,
      recommendations: completeForm.value.recommendations || null,
    })
    for (const url of photos.value) {
      await attachmentsAPI.upload({ visit_id: completeModal.value.id, kind: 'act_photo', file_url: url })
    }
    completeModal.value = null
    photos.value = []
    await loadMyVisits()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function statusClass(s) {
  const m = { planned: 'bg-blue-100 text-blue-700', in_progress: 'bg-green-100 text-green-700', closed: 'bg-gray-400 text-white', done: 'bg-gray-400 text-white', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-700'
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }

watch(visits, (vl) => {
  const id = window.history.state?.openVisitId
  if (id && vl?.length) {
    const v = vl.find((x) => x.id === id)
    if (v) { activeTab.value = 'all'; detailVisit.value = v }
  }
}, { once: true })

onMounted(loadMyVisits)
</script>
