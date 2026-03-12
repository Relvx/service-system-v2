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
          <button @click="loadAll(true)" class="btn btn-secondary flex items-center">
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

      <!-- Day click choice modal (office/admin only) -->
      <div v-if="dayChoiceDate" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-xs mx-4">
          <div class="flex items-center justify-between p-5 border-b">
            <h2 class="text-base font-semibold text-gray-900">{{ formatDate(dayChoiceDate) }}</h2>
            <button @click="dayChoiceDate = null" class="text-gray-400 hover:text-gray-600"><X class="w-5 h-5" /></button>
          </div>
          <div class="p-5 flex flex-col gap-3">
            <button @click="chooseCreateVisit" class="btn btn-secondary w-full flex items-center justify-center gap-2">
              <CalendarPlus class="w-4 h-4" /> Запланировать выезд
            </button>
            <button @click="chooseAddNote" class="btn w-full flex items-center justify-center gap-2 bg-purple-600 text-white hover:bg-purple-700">
              <StickyNote class="w-4 h-4" /> Добавить заметку
            </button>
          </div>
        </div>
      </div>

      <!-- Note create/edit modal -->
      <div v-if="noteModal.open" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
          <div class="flex items-center justify-between p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">
              {{ noteModal.isEdit ? 'Редактировать заметку' : 'Новая заметка' }}
            </h2>
            <button @click="closeNoteModal" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm text-gray-500 mb-1">Дата</label>
              <p class="text-gray-900 font-medium">{{ formatDate(noteModal.date) }}</p>
            </div>
            <div>
              <label class="block text-sm text-gray-500 mb-1">Заметка</label>
              <textarea
                v-model="noteModal.text"
                class="input w-full"
                rows="4"
                placeholder="Текст заметки..."
              />
            </div>
          </div>
          <div class="p-6 border-t flex justify-between gap-3">
            <button
              v-if="noteModal.isEdit"
              @click="deleteNote"
              class="btn text-red-600 hover:bg-red-50"
            >Удалить</button>
            <div class="flex gap-3 ml-auto">
              <button @click="closeNoteModal" class="btn btn-secondary">Отмена</button>
              <button
                @click="saveNote"
                :disabled="!noteModal.text.trim() || noteModal.saving"
                class="btn btn-primary disabled:opacity-50"
              >
                {{ noteModal.saving ? 'Сохранение...' : 'Сохранить' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { X, RefreshCw, CalendarPlus, StickyNote } from 'lucide-vue-next'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import ruLocale from '@fullcalendar/core/locales/ru'
import Layout from '../components/Layout.vue'
import { useAuthStore } from '../stores/auth.js'
import { useConfigStore } from '../stores/config.js'
import { visitsAPI, usersAPI, calendarNotesAPI } from '../services/api.js'

const auth = useAuthStore()
const cfg = useConfigStore()
const router = useRouter()

const allVisitEvents = ref([])
const allNotes = ref([])
const loading = ref(false)
const refreshing = ref(false)
const selectedVisit = ref(null)
const calendarRef = ref(null)
const masters = ref([])
const selectedMasterId = ref(null)

const dayChoiceDate = ref(null)

const noteModal = ref({
  open: false,
  isEdit: false,
  id: null,
  date: null,
  text: '',
  saving: false,
})

const canEditNotes = computed(
  () => auth.hasGroup('office_group') || auth.hasGroup('admin_group')
)

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

const NOTE_COLOR = '#9333ea'

const legend = [
  { label: 'Запланирован',    color: STATUS_COLORS.planned },
  { label: 'В работе',        color: STATUS_COLORS.in_progress },
  { label: 'Завершён/закрыт', color: STATUS_COLORS.done },
  { label: 'Отменён',         color: STATUS_COLORS.cancelled },
  { label: 'Заметка',         color: NOTE_COLOR },
]

function visitToEvent(v) {
  const color = STATUS_COLORS[v.status] || '#3b82f6'
  const dateStr = v.planned_date.slice(0, 10)
  return {
    id: `visit-${v.id}`,
    title: v.site_title,
    start: v.planned_time_from ? `${dateStr}T${v.planned_time_from}` : dateStr,
    end: v.planned_time_to ? `${dateStr}T${v.planned_time_to}` : undefined,
    backgroundColor: color,
    borderColor: color,
    allDay: !v.planned_time_from,
    extendedProps: { ...v, _type: 'visit' },
  }
}

function noteToEvent(n) {
  return {
    id: `note-${n.id}`,
    title: `📝 ${n.text}`,
    start: n.date,
    allDay: true,
    backgroundColor: NOTE_COLOR,
    borderColor: NOTE_COLOR,
    extendedProps: { ...n, _type: 'note' },
  }
}

const filteredVisitEvents = computed(() => {
  if (!selectedMasterId.value) return allVisitEvents.value
  return allVisitEvents.value.filter(
    (e) => e.extendedProps.assigned_user_id === selectedMasterId.value
  )
})

const allEvents = computed(() => [...filteredVisitEvents.value, ...allNotes.value.map(noteToEvent)])

async function loadVisits(year) {
  const res = await visitsAPI.getCalendar(`${year}-01-01`, `${year}-12-31`)
  allVisitEvents.value = res.data.map(visitToEvent)
}

async function loadNotes(year) {
  if (!canEditNotes.value) return
  const res = await calendarNotesAPI.getAll(year)
  allNotes.value = res.data
}

async function loadAll(isRefresh = false) {
  isRefresh ? (refreshing.value = true) : (loading.value = true)
  try {
    const year = new Date().getFullYear()
    await Promise.all([loadVisits(year), loadNotes(year)])
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
  if (!d) return '—'
  const str = typeof d === 'string' ? d.slice(0, 10) : d.toISOString().slice(0, 10)
  return new Date(str + 'T00:00:00').toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

// Day click → show choice modal (office/admin only)
function handleDateClick({ dateStr }) {
  if (!canEditNotes.value) return
  dayChoiceDate.value = dateStr
}

function chooseCreateVisit() {
  router.push({ path: '/visits', query: { date_from: dayChoiceDate.value, date_to: dayChoiceDate.value } })
  dayChoiceDate.value = null
}

function chooseAddNote() {
  noteModal.value = { open: true, isEdit: false, id: null, date: dayChoiceDate.value, text: '', saving: false }
  dayChoiceDate.value = null
}

function openNoteEdit(note) {
  noteModal.value = { open: true, isEdit: true, id: note.id, date: note.date, text: note.text, saving: false }
}

function closeNoteModal() {
  noteModal.value.open = false
}

async function saveNote() {
  const m = noteModal.value
  if (!m.text.trim()) return
  m.saving = true
  try {
    if (m.isEdit) {
      const res = await calendarNotesAPI.update(m.id, { text: m.text.trim() })
      const idx = allNotes.value.findIndex((n) => n.id === m.id)
      if (idx !== -1) allNotes.value[idx] = res.data
    } else {
      const res = await calendarNotesAPI.create({ date: m.date, text: m.text.trim() })
      allNotes.value.push(res.data)
    }
    closeNoteModal()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    m.saving = false
  }
}

async function deleteNote() {
  const m = noteModal.value
  try {
    await calendarNotesAPI.delete(m.id)
    allNotes.value = allNotes.value.filter((n) => n.id !== m.id)
    closeNoteModal()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
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
  events: allEvents.value,
  eventClick: ({ event }) => {
    if (event.extendedProps._type === 'note') {
      openNoteEdit(event.extendedProps)
    } else {
      selectedVisit.value = event.extendedProps
    }
  },
  dateClick: handleDateClick,
  datesSet: (info) => {
    const year = info.view.currentStart.getFullYear()
    loadVisits(year)
    loadNotes(year)
  },
  height: 'auto',
}))

onMounted(async () => {
  loadAll()
  if (canFilterByMaster.value) {
    try {
      const res = await usersAPI.getMasters()
      masters.value = res.data
    } catch {}
  }
})
</script>
