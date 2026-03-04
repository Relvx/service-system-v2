<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Sidebar -->
    <div
      class="fixed inset-y-0 left-0 bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ease-in-out z-30"
      :class="collapsed ? 'w-16' : 'w-64'"
    >
      <!-- Logo + collapse toggle -->
      <div
        class="flex items-center h-16 border-b border-gray-200"
        :class="collapsed ? 'justify-center' : 'justify-between px-4'"
      >
        <h1 v-if="!collapsed" class="text-lg font-bold text-primary-600 truncate">Service System</h1>
        <button
          @click="toggleCollapse"
          class="flex items-center justify-center w-8 h-8 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors flex-shrink-0"
          :title="collapsed ? 'Развернуть меню' : 'Свернуть меню'"
        >
          <ChevronLeft v-if="!collapsed" class="w-4 h-4" />
          <ChevronRight v-else class="w-4 h-4" />
        </button>
      </div>

      <!-- Navigation -->
      <nav
        class="flex-1 py-4 space-y-1 overflow-y-auto overflow-x-hidden"
        :class="collapsed ? 'px-2' : 'px-3'"
      >
        <RouterLink
          v-for="item in filteredNav"
          :key="item.href"
          :to="item.href"
          class="flex items-center rounded-lg transition-colors group relative"
          :class="[
            collapsed ? 'justify-center px-2 py-3' : 'px-3 py-2.5',
            route.path === item.href
              ? 'bg-primary-50 text-primary-700'
              : 'text-gray-700 hover:bg-gray-50',
          ]"
        >
          <component :is="item.icon" class="flex-shrink-0 h-5 w-5" :class="collapsed ? '' : 'mr-3'" />
          <span v-if="!collapsed" class="text-sm font-medium truncate">{{ item.name }}</span>
          <!-- Tooltip в свёрнутом состоянии -->
          <div
            v-if="collapsed"
            class="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50"
          >
            {{ item.name }}
          </div>
        </RouterLink>
      </nav>

      <!-- User section -->
      <div class="border-t border-gray-200 p-3">
        <!-- Развёрнутое состояние -->
        <div v-if="!collapsed" class="flex items-center mb-3">
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ user?.full_name }}</p>
            <p class="text-xs text-gray-500 truncate">{{ userGroupLabel }}</p>
          </div>
          <RouterLink
            to="/notifications"
            class="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg flex-shrink-0"
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

        <!-- Свёрнутое: только иконка уведомлений -->
        <div v-if="collapsed" class="flex justify-center mb-2">
          <RouterLink
            to="/notifications"
            class="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg"
            title="Уведомления"
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
          class="w-full flex items-center justify-center px-3 py-2 text-sm font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
          :title="collapsed ? 'Выйти' : ''"
        >
          <LogOut class="h-4 w-4 flex-shrink-0" :class="collapsed ? '' : 'mr-2'" />
          <span v-if="!collapsed">Выйти</span>
        </button>
      </div>
    </div>

    <!-- Main content — сдвигается вместе с сайдбаром -->
    <div class="transition-all duration-300 ease-in-out" :class="collapsed ? 'ml-16' : 'ml-64'">
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
  ClipboardList, AlertTriangle, ShoppingCart, LogOut, Bell, Settings, ScrollText,
  ChevronLeft, ChevronRight,
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth.js'
import { notificationsAPI } from '../services/api.js'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const user = computed(() => auth.user)
const unreadCount = ref(0)

const COLLAPSED_KEY = 'sidebar_collapsed'
const collapsed = ref(localStorage.getItem(COLLAPSED_KEY) === 'true')

function toggleCollapse() {
  collapsed.value = !collapsed.value
  localStorage.setItem(COLLAPSED_KEY, String(collapsed.value))
}

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
  { name: 'Дашборд',    href: '/dashboard', icon: LayoutDashboard, groups: ['office_group', 'admin_group'] },
  { name: 'Карта',      href: '/map',        icon: Map,             groups: ['office_group', 'admin_group'] },
  { name: 'Календарь',  href: '/calendar',   icon: Calendar,        groups: ['office_group', 'admin_group', 'master_group'] },
  { name: 'Мои выезды', href: '/my-visits',  icon: ClipboardList,   groups: ['master_group'] },
  { name: 'Клиенты',    href: '/clients',    icon: Users,           groups: ['office_group', 'admin_group'] },
  { name: 'Объекты',    href: '/sites',      icon: Building2,       groups: ['office_group', 'admin_group'] },
  { name: 'Выезды',     href: '/visits',     icon: ClipboardList,   groups: ['office_group', 'admin_group'] },
  { name: 'Дефекты',    href: '/defects',    icon: AlertTriangle,   groups: ['office_group', 'admin_group'] },
  { name: 'Закупки',    href: '/purchases',  icon: ShoppingCart,    groups: ['office_group', 'admin_group'] },
  { name: 'Журнал',     href: '/logs',       icon: ScrollText,      groups: ['office_group', 'admin_group'] },
  { name: 'Админ',      href: '/admin',      icon: Settings,        groups: ['admin_group'] },
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
