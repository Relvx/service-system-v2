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
        <!-- Stats Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div v-for="stat in statCards" :key="stat.name" class="card">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-600">{{ stat.name }}</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{{ stat.value }}</p>
              </div>
              <div :class="`${stat.color} p-3 rounded-lg`">
                <component :is="stat.icon" class="h-6 w-6 text-white" />
              </div>
            </div>
          </div>
        </div>

        <!-- Defects by Priority -->
        <div v-if="stats?.open_defects?.length" class="card mb-8">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Дефекты по приоритетам</h2>
          <div class="space-y-3">
            <div v-for="d in stats.open_defects" :key="d.priority" class="flex items-center justify-between">
              <div class="flex items-center">
                <div class="w-3 h-3 rounded-full mr-3" :class="priorityDotClass(d.priority)" />
                <span class="text-gray-700">{{ cfg.priorityLabel(d.priority) }}</span>
              </div>
              <span class="text-gray-900 font-semibold">{{ d.count }}</span>
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

const statCards = computed(() => [
  { name: 'Выезды сегодня', value: stats.value?.visits_today || 0, icon: Calendar, color: 'bg-blue-500' },
  { name: 'Выезды на неделю', value: stats.value?.visits_this_week || 0, icon: ClipboardList, color: 'bg-green-500' },
  {
    name: 'Открытые дефекты',
    value: stats.value?.open_defects?.reduce((s, d) => s + d.count, 0) || 0,
    icon: AlertTriangle,
    color: 'bg-yellow-500',
  },
  { name: 'Активные закупки', value: stats.value?.active_purchases || 0, icon: ShoppingCart, color: 'bg-purple-500' },
])

function priorityDotClass(priority) {
  const map = { urgent: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-yellow-500', low: 'bg-gray-400' }
  return map[priority] || 'bg-gray-400'
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
