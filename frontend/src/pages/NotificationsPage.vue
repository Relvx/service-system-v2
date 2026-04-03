<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between flex-wrap gap-y-3 mb-6">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Уведомления</h1>
          <p class="text-gray-600 mt-1">Непрочитанных: {{ unreadCount }}</p>
        </div>
        <button v-if="unreadCount > 0" @click="markAllRead" class="btn btn-secondary text-sm">
          Прочитать все
        </button>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="n in notifications"
          :key="n.id"
          class="card transition-all"
          :class="[
            n.is_read ? 'opacity-60' : 'border-l-4 border-primary-500',
            notifRoute(n) ? 'cursor-pointer hover:shadow-md' : ''
          ]"
          @click="handleClick(n)"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <component :is="notifIcon(n)" class="w-4 h-4 flex-shrink-0" :class="notifIconClass(n)" />
                <h3 class="font-semibold text-gray-900">{{ n.title }}</h3>
                <span v-if="!n.is_read" class="inline-flex w-2 h-2 rounded-full bg-primary-500 flex-shrink-0"></span>
              </div>
              <p class="text-sm text-gray-600">{{ n.message }}</p>
              <div class="flex items-center gap-3 mt-1">
                <p class="text-xs text-gray-400">{{ formatDate(n.created_at) }}</p>
                <span v-if="notifRoute(n)" class="text-xs text-primary-500 flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" />{{ notifLinkLabel(n) }}
                </span>
              </div>
            </div>
            <button
              @click.stop="toggleRead(n)"
              class="ml-4 text-xs text-gray-400 hover:text-primary-600 transition-colors whitespace-nowrap flex-shrink-0"
            >
              {{ n.is_read ? 'Непрочитанное' : 'Прочитать' }}
            </button>
          </div>
        </div>

        <div v-if="notifications.length === 0" class="text-center py-12 card">
          <Bell class="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900">Нет уведомлений</h3>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, CalendarCheck, AlertTriangle, ShoppingCart, ExternalLink } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { notificationsAPI } from '../services/api.js'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const auth = useAuthStore()
const notifications = ref([])
const loading = ref(true)
const unreadCount = computed(() => notifications.value.filter((n) => !n.is_read).length)

// Определяем маршрут по полям уведомления
function notifRoute(n) {
  if (n.related_visit_id) {
    const visitPath = auth.hasGroup('master_group') && !auth.hasGroup('office_group') && !auth.hasGroup('admin_group')
      ? '/my-visits'
      : '/visits'
    return { path: visitPath, query: { open_visit: n.related_visit_id } }
  }
  if (n.related_defect_id)   return { path: '/defects',   query: { highlight: n.related_defect_id } }
  if (n.related_purchase_id) return { path: '/purchases', query: { highlight: n.related_purchase_id } }
  return null
}

function notifLinkLabel(n) {
  if (n.related_visit_id)    return 'Перейти к выезду'
  if (n.related_defect_id)   return 'Перейти к дефекту'
  if (n.related_purchase_id) return 'Перейти к закупке'
  return ''
}

function notifIcon(n) {
  if (n.type?.includes('visit'))    return CalendarCheck
  if (n.type?.includes('defect'))   return AlertTriangle
  if (n.type?.includes('purchase')) return ShoppingCart
  return Bell
}

function notifIconClass(n) {
  if (n.type?.includes('visit'))    return 'text-blue-500'
  if (n.type?.includes('defect'))   return 'text-orange-500'
  if (n.type?.includes('purchase')) return 'text-green-500'
  return 'text-primary-500'
}

async function handleClick(n) {
  const route = notifRoute(n)
  if (!route) return
  // Помечаем прочитанным при переходе
  if (!n.is_read) {
    try {
      await notificationsAPI.markAsRead(n.id)
      n.is_read = true
    } catch (e) {
      console.error(e)
    }
  }
  router.push(route)
}

async function load() {
  loading.value = true
  try {
    const res = await notificationsAPI.getAll()
    notifications.value = res.data
  } finally {
    loading.value = false
  }
}

async function toggleRead(n) {
  try {
    if (n.is_read) {
      await notificationsAPI.markAsUnread(n.id)
      n.is_read = false
    } else {
      await notificationsAPI.markAsRead(n.id)
      n.is_read = true
    }
  } catch (e) {
    console.error(e)
  }
}

async function markAllRead() {
  await notificationsAPI.markAllAsRead()
  notifications.value.forEach((n) => { n.is_read = true })
}

function formatDate(d) {
  return d ? new Date(d).toLocaleString('ru-RU') : ''
}

onMounted(load)
</script>
