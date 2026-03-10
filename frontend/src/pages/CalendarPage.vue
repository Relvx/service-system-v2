<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-3xl font-bold text-gray-900">Календарь</h1>
        <div class="flex items-center gap-3">
          <!-- Master filter (office/admin only) -->
          <select
            v-if="canFilterByMaster"
            v-model="selectedMasterId"
            class="input w-48 text-sm"
          >
            <option :value="null">Все мастера</option>
            <option v-for="m in masters" :key="m.id" :value="m.id">{{ m.full_name }}</option>
          </select>
          <button @click="loadVisits(true)" class="btn btn-secondary flex items-center">
            <RefreshCw class="w-4 h-4 mr-2" :class="{ 'animate-spin': refreshing }" />Обновить
          </button>
        </div>
      </div>

      <!-- Color legend -->
      <div class="flex flex-wrap items-center gap-4 mb-4 text-sm text-gray-600">
        <div v-for="l in legend" :key="l.label" class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-3 rounded-sm flex-shrink-0" :style="{ background: l.color }"></span>
          {{ l.label }}
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <div class="card">
        <FullCalendar
          ref="calendarRef"
          :options="calendarOptions"
        />
      </div>

      <!-- Visit Detail Modal -->
      <div v-if="selectedVisit" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ selectedVisit.site_title }}</h2>
            <button @click="selectedVisit = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <div class="p-6 space-y-3 text-sm">
            <div class="flex gap-2">
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="statusClass(selectedVisit.status)">
                {{ cfg.visitStatusLabel(selectedVisit.status) }}
              </span>
            </div>
            <div><p class="text-gray-500">Адрес</p><p class="text-gray-900">{{ selectedVisit.site_address }}</p></div>
            <div><p class="text-gray-500">Дата</p><p class="text-gray-900">{{ formatDate(selectedVisit.planned_date) }}</p></div>
            <div v-if="selectedVisit.planned_time_from">
              <p class="text-gray-500">Время</p>
              <p class="text-gray-900">{{ selectedVisit.planned_time_from?.slice(0,5) }} — {{ selectedVisit.planned_time_to?.slice(0,5) || '—' }}</p>
            </div>
            <div><p class="text-gray-500">Мастер</p><p class="text-gray-900">{{ selectedVisit.master_name || 'Не назначен' }}</p></div>
            <div><p class="text-gray-500">Тип</p><p class="text-gray-900">{{ cfg.visitTypeLabel(selectedVisit.visit_type) }}</p></div>
          </div>
          <div class="p-6 border-t flex justify-end gap-3">
            <button @click="goToVisit" class="btn btn-secondary">К выезду</button>
            <button @click="selectedVisit = null" class="btn btn-primary">Закрыть</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { X, RefreshCw } from 'lucide-vue-next'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import ruLocale from '@fullcalendar/core/locales/ru'
import Layout from '../components/Layout.vue'
import { useAuthStore } from '../stores/auth.js'
import { useConfigStore } from '../stores/config.js'
import { visitsAPI, usersAPI } from '../services/api.js'

const auth = useAuthStore()
const cfg = useConfigStore()
const router = useRouter()

const allEvents = ref([])
const loading = ref(false)
const refreshing = ref(false)
const selectedVisit = ref(null)
const calendarRef = ref(null)
const masters = ref([])
const selectedMasterId = ref(null)

const canFilterByMaster = computed(
  () => auth.hasGroup('office_group') || auth.hasGroup('admin_group')
)

const STATUS_COLORS = {
  planned: '#3b82f6',
  in_progress: '#22c55e',
  done: '#6b7280',
  closed: '#6b7280',
  cancelled: '#ef4444',
}

const legend = [
  { label: 'Запланирован',    color: STATUS_COLORS.planned },
  { label: 'В работе',        color: STATUS_COLORS.in_progress },
  { label: 'Завершён/закрыт', color: STATUS_COLORS.done },
  { label: 'Отменён',         color: STATUS_COLORS.cancelled },
]

function visitToEvent(v) {
  const color = STATUS_COLORS[v.status] || '#3b82f6'
  const dateStr = v.planned_date.slice(0, 10)
  return {
    id: v.id,
    title: v.site_title,
    start: v.planned_time_from ? `${dateStr}T${v.planned_time_from}` : dateStr,
    end: v.planned_time_to ? `${dateStr}T${v.planned_time_to}` : undefined,
    backgroundColor: color,
    borderColor: color,
    allDay: !v.planned_time_from,
    extendedProps: v,
  }
}

const filteredEvents = computed(() => {
  if (!selectedMasterId.value) return allEvents.value
  return allEvents.value.filter(
    (e) => e.extendedProps.assigned_user_id === selectedMasterId.value
  )
})

async function loadVisits(isRefresh = false) {
  isRefresh ? (refreshing.value = true) : (loading.value = true)
  try {
    const year = new Date().getFullYear()
    const res = await visitsAPI.getCalendar(`${year}-01-01`, `${year}-12-31`)
    allEvents.value = res.data.map(visitToEvent)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function goToVisit() {
  if (!selectedVisit.value) return
  const isMaster =
    auth.hasGroup('master_group') &&
    !auth.hasGroup('office_group') &&
    !auth.hasGroup('admin_group')
  const date = selectedVisit.value.planned_date?.slice(0, 10)
  if (isMaster) {
    router.push('/my-visits')
  } else {
    router.push({ path: '/visits', query: { date_from: date, date_to: date } })
  }
  selectedVisit.value = null
}

function statusClass(s) {
  const m = {
    planned: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-green-100 text-green-700',
    closed: 'bg-gray-400 text-white',
    done: 'bg-gray-400 text-white',
    cancelled: 'bg-red-100 text-red-700',
  }
  return m[s] || 'bg-gray-100 text-gray-700'
}

function formatDate(d) {
  return d
    ? new Date(d.slice(0, 10) + 'T00:00:00').toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      })
    : '—'
}

const calendarOptions = computed(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  locale: ruLocale,
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay',
  },
  events: filteredEvents.value,
  eventClick: ({ event }) => {
    selectedVisit.value = event.extendedProps
  },
  datesSet: (info) => {
    const year = info.view.currentStart.getFullYear()
    visitsAPI.getCalendar(`${year}-01-01`, `${year}-12-31`).then((res) => {
      allEvents.value = res.data.map(visitToEvent)
    })
  },
  height: 'auto',
}))

onMounted(async () => {
  loadVisits()
  if (canFilterByMaster.value) {
    try {
      const res = await usersAPI.getMasters()
      masters.value = res.data
    } catch {}
  }
})
</script>
