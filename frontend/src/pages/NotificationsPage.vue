<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Уведомления</h1>
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
          :class="n.is_read ? 'opacity-60' : 'border-l-4 border-primary-500'"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <Bell class="w-4 h-4 text-primary-500" />
                <h3 class="font-semibold text-gray-900">{{ n.title }}</h3>
                <span v-if="!n.is_read" class="inline-flex w-2 h-2 rounded-full bg-primary-500"></span>
              </div>
              <p class="text-sm text-gray-600">{{ n.message }}</p>
              <p class="text-xs text-gray-400 mt-1">{{ formatDate(n.created_at) }}</p>
            </div>
            <button
              @click="toggleRead(n)"
              class="ml-4 text-xs text-gray-400 hover:text-primary-600 transition-colors whitespace-nowrap"
            >
              {{ n.is_read ? 'Отметить непрочитанным' : 'Прочитать' }}
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
import { Bell } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { notificationsAPI } from '../services/api.js'

const notifications = ref([])
const loading = ref(true)
const unreadCount = computed(() => notifications.value.filter((n) => !n.is_read).length)

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
