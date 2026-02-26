<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Sidebar -->
    <div class="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 flex flex-col">
      <!-- Logo -->
      <div class="flex items-center justify-center h-16 border-b border-gray-200">
        <h1 class="text-xl font-bold text-primary-600">Service System v2</h1>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
        <RouterLink
          v-for="item in filteredNav"
          :key="item.href"
          :to="item.href"
          class="flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors"
          :class="
            route.path === item.href
              ? 'bg-primary-50 text-primary-700'
              : 'text-gray-700 hover:bg-gray-50'
          "
        >
          <component :is="item.icon" class="mr-3 h-5 w-5" />
          {{ item.name }}
        </RouterLink>
      </nav>

      <!-- User section -->
      <div class="border-t border-gray-200 p-4">
        <div class="flex items-center mb-3">
          <div class="flex-1">
            <p class="text-sm font-medium text-gray-900">{{ user?.full_name }}</p>
            <p class="text-xs text-gray-500">{{ userGroupLabel }}</p>
          </div>
          <RouterLink
            to="/notifications"
            class="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg"
          >
            <Bell class="h-5 w-5" />
            <span
              v-if="unreadCount > 0"
              class="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold"
            >
              {{ unreadCount > 9 ? '9+' : unreadCount }}
            </span>
          </RouterLink>
        </div>
        <button
          @click="handleLogout"
          class="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
        >
          <LogOut class="mr-2 h-4 w-4" />
          Выйти
        </button>
      </div>
    </div>

    <!-- Main content -->
    <div class="ml-64">
      <main class="p-8">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  LayoutDashboard, Map, Calendar, Users, Building2,
  ClipboardList, AlertTriangle, ShoppingCart, LogOut, Bell, Settings,
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth.js'
import { notificationsAPI } from '../services/api.js'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const user = computed(() => auth.user)
const unreadCount = ref(0)

const GROUP_LABELS = {
  admin_group: 'Администратор',
  office_group: 'Офис',
  master_group: 'Мастер',
}

const userGroupLabel = computed(() => {
  const groups = auth.groups
  if (!groups.length) return ''
  return groups.map((g) => GROUP_LABELS[g] || g).join(', ')
})

const allNav = [
  { name: 'Дашборд',   href: '/dashboard', icon: LayoutDashboard, groups: ['office_group', 'admin_group'] },
  { name: 'Карта',     href: '/map',        icon: Map,             groups: ['office_group', 'admin_group'] },
  { name: 'Календарь', href: '/calendar',   icon: Calendar,        groups: ['office_group', 'admin_group', 'master_group'] },
  { name: 'Мои выезды',href: '/my-visits',  icon: ClipboardList,   groups: ['master_group'] },
  { name: 'Клиенты',   href: '/clients',    icon: Users,           groups: ['office_group', 'admin_group'] },
  { name: 'Объекты',   href: '/sites',      icon: Building2,       groups: ['office_group', 'admin_group'] },
  { name: 'Выезды',    href: '/visits',     icon: ClipboardList,   groups: ['office_group', 'admin_group'] },
  { name: 'Дефекты',   href: '/defects',    icon: AlertTriangle,   groups: ['office_group', 'admin_group'] },
  { name: 'Закупки',   href: '/purchases',  icon: ShoppingCart,    groups: ['office_group', 'admin_group'] },
  { name: 'Админ',     href: '/admin',      icon: Settings,        groups: ['admin_group'] },
]

const filteredNav = computed(() =>
  allNav.filter((item) => item.groups.some((g) => auth.groups.includes(g)))
)

async function fetchUnread() {
  try {
    const res = await notificationsAPI.getAll()
    unreadCount.value = res.data.filter((n) => !n.is_read).length
  } catch {}
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(fetchUnread)
watch(() => route.path, fetchUnread)
</script>
