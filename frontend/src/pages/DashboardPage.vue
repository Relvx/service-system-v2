<template>
  <Layout>
    <div>
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Добро пожаловать, {{ user?.full_name }}!</h1>
        <p class="text-gray-600 mt-2">Обзор системы учета выездов</p>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <template v-else>
        <!-- Stats Grid (clickable) -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <RouterLink
            v-for="stat in statCards"
            :key="stat.name"
            :to="stat.link"
            class="card hover:shadow-md transition-shadow cursor-pointer"
          >
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600">{{ stat.name }}</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{{ stat.value }}</p>
              </div>
              <div :class="`${stat.color} p-3 rounded-lg`">
                <component :is="stat.icon" class="h-6 w-6 text-white" />
              </div>
            </div>
          </RouterLink>
        </div>

        <!-- Today's Visits + Defects by Priority -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <!-- Today's visits list -->
          <div class="card">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-gray-900">Выезды сегодня</h2>
              <RouterLink :to="todayVisitsLink" class="text-sm text-primary-600 hover:underline">Все</RouterLink>
            </div>
            <div v-if="stats?.today_visits?.length" class="space-y-3">
              <div
                v-for="v in stats.today_visits"
                :key="v.id"
                class="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
              >
                <div class="min-w-0">
                  <p class="text-sm font-medium text-gray-900 truncate">{{ v.site_title || '—' }}</p>
                  <p class="text-xs text-gray-500 truncate">{{ v.client_name || '—' }} · {{ v.master_name || 'Без мастера' }}</p>
                </div>
                <span class="ml-3 text-xs px-2 py-0.5 rounded-full flex-shrink-0" :class="statusClass(v.status)">
                  {{ cfg.visitStatusLabel(v.status) }}
                </span>
              </div>
            </div>
            <p v-else class="text-sm text-gray-400 py-4 text-center">Нет выездов на сегодня</p>
          </div>

          <!-- Defects by Priority -->
          <div class="card">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-gray-900">Дефекты по приоритетам</h2>
              <RouterLink to="/defects" class="text-sm text-primary-600 hover:underline">Все</RouterLink>
            </div>
            <div v-if="stats?.open_defects?.length" class="space-y-3">
              <div v-for="d in stats.open_defects" :key="d.priority" class="flex items-center justify-between">
                <div class="flex items-center">
                  <div class="w-3 h-3 rounded-full mr-3" :class="priorityDotClass(d.priority)" />
                  <span class="text-gray-700">{{ cfg.priorityLabel(d.priority) }}</span>
                </div>
                <span class="text-gray-900 font-semibold">{{ d.count }}</span>
              </div>
            </div>
            <p v-else class="text-sm text-gray-400 py-4 text-center">Нет открытых дефектов</p>
          </div>
        </div>

        <!-- Recent Completed Visits -->
        <div v-if="stats?.recent_completed?.length" class="card mb-8">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-900">Последние завершённые выезды</h2>
            <RouterLink to="/visits?status=closed" class="text-sm text-primary-600 hover:underline">Все</RouterLink>
          </div>
          <div class="space-y-3">
            <div
              v-for="v in stats.recent_completed"
              :key="v.id"
              class="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
            >
              <div class="min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">{{ v.site_title || '—' }}</p>
                <p class="text-xs text-gray-500 truncate">{{ v.client_name || '—' }} · {{ v.master_name || 'Без мастера' }}</p>
              </div>
              <span class="ml-3 text-xs text-gray-400 flex-shrink-0">{{ formatDate(v.planned_date) }}</span>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <RouterLink to="/visits" class="card hover:shadow-md transition-shadow">
            <div class="flex items-center mb-2">
              <Plus class="w-5 h-5 text-primary-600 mr-2" />
              <h3 class="font-semibold text-gray-900">Создать выезд</h3>
            </div>
            <p class="text-sm text-gray-600">Запланировать новый выезд мастера</p>
          </RouterLink>

          <RouterLink to="/sites" class="card hover:shadow-md transition-shadow">
            <div class="flex items-center mb-2">
              <Building2 class="w-5 h-5 text-primary-600 mr-2" />
              <h3 class="font-semibold text-gray-900">Добавить объект</h3>
            </div>
            <p class="text-sm text-gray-600">Добавить новую котельную</p>
          </RouterLink>

          <RouterLink to="/calendar" class="card hover:shadow-md transition-shadow">
            <div class="flex items-center mb-2">
              <Calendar class="w-5 h-5 text-primary-600 mr-2" />
              <h3 class="font-semibold text-gray-900">Календарь</h3>
            </div>
            <p class="text-sm text-gray-600">Посмотреть расписание выездов</p>
          </RouterLink>
        </div>
      </template>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { Calendar, ClipboardList, AlertTriangle, ShoppingCart, Plus, Building2 } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { useAuthStore } from '../stores/auth.js'
import { useConfigStore } from '../stores/config.js'
import { dashboardAPI } from '../services/api.js'

const auth = useAuthStore()
const cfg = useConfigStore()
const user = computed(() => auth.user)
const stats = ref(null)
const loading = ref(true)

const todayStr = new Date().toISOString().slice(0, 10)
const todayVisitsLink = `/visits?date_from=${todayStr}&date_to=${todayStr}`

const statCards = computed(() => [
  { name: 'Выезды сегодня',  value: stats.value?.visits_today || 0,  icon: Calendar,      color: 'bg-blue-500',   link: todayVisitsLink },
  { name: 'Выезды на неделю', value: stats.value?.visits_this_week || 0, icon: ClipboardList, color: 'bg-green-500',  link: '/visits' },
  { name: 'Открытые дефекты', value: stats.value?.open_defects?.reduce((s, d) => s + d.count, 0) || 0, icon: AlertTriangle, color: 'bg-yellow-500', link: '/defects' },
  { name: 'Активные закупки', value: stats.value?.active_purchases || 0, icon: ShoppingCart,  color: 'bg-purple-500', link: '/purchases' },
])

function priorityDotClass(priority) {
  const map = { urgent: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-yellow-500', low: 'bg-gray-400' }
  return map[priority] || 'bg-gray-400'
}

function statusClass(status) {
  const map = {
    planned:     'bg-blue-100 text-blue-700',
    in_progress: 'bg-yellow-100 text-yellow-700',
    done:        'bg-green-100 text-green-700',
    closed:      'bg-gray-100 text-gray-600',
    cancelled:   'bg-red-100 text-red-600',
  }
  return map[status] || 'bg-gray-100 text-gray-600'
}

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('ru-RU') : ''
}

onMounted(async () => {
  try {
    const res = await dashboardAPI.getStats()
    stats.value = res.data
  } finally {
    loading.value = false
  }
})
</script>
