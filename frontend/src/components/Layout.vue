<template>
  <div class="min-h-screen bg-gray-50">

    <!-- Mobile top bar (only on < md) -->
    <div class="md:hidden fixed top-0 left-0 right-0 z-40">
      <!-- Верхняя строка -->
      <div class="h-14 bg-white border-b border-gray-200 flex items-center px-3 gap-2">
        <button
          @click="mobileOpen = !mobileOpen"
          class="flex items-center justify-center w-9 h-9 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors flex-shrink-0"
        >
          <Menu class="w-5 h-5" />
        </button>
        <h1 class="text-base font-bold text-primary-600 flex-shrink-0">Service System</h1>
        <div class="flex-1 relative" ref="mobileSearchWrapRef">
          <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          <input
            v-model="searchQuery"
            @input="onSearchInput"
            @focus="searchFocused = true"
            @keydown.escape="closeSearch"
            placeholder="Поиск..."
            class="w-full pl-8 pr-7 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button v-if="searchQuery" @click="closeSearch" class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400">
            <X class="w-3.5 h-3.5" />
          </button>
        </div>
        <RouterLink to="/notifications" class="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg flex-shrink-0">
          <Bell class="h-5 w-5" />
          <span
            v-if="unreadCount > 0"
            class="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold"
          >{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
        </RouterLink>
      </div>
      <!-- Мобильный дропдаун поиска -->
      <div
        v-if="searchFocused && searchQuery.length >= 1"
        class="bg-white border-b border-gray-200 shadow-lg flex flex-col"
        style="max-height: 60vh; overflow-y: auto"
      >
        <div v-if="searchLoading" class="px-4 py-3 text-sm text-gray-500 text-center">Поиск...</div>
        <div v-else-if="searchResults.length === 0" class="px-4 py-3 text-sm text-gray-500 text-center">Ничего не найдено</div>
        <div v-else>
          <div
            v-for="r in searchResults" :key="`m-${r.type}-${r.id}`"
            @mousedown.prevent="navigateTo(r.url)"
            @touchstart.prevent="navigateTo(r.url)"
            class="flex items-center gap-3 px-4 py-3 border-b border-gray-50 active:bg-gray-50 cursor-pointer"
          >
            <div class="flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center"
              :class="{
                'bg-blue-100': r.type === 'client',
                'bg-green-100': r.type === 'site',
                'bg-purple-100': r.type === 'contract',
              }"
            >
              <Users v-if="r.type === 'client'" class="w-4 h-4 text-blue-600" />
              <Building2 v-else-if="r.type === 'site'" class="w-4 h-4 text-green-600" />
              <FileText v-else class="w-4 h-4 text-purple-600" />
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-gray-900 truncate">{{ r.title }}</p>
              <p v-if="r.subtitle" class="text-xs text-gray-500 truncate">{{ r.subtitle }}</p>
            </div>
            <span class="text-xs text-gray-400 flex-shrink-0">
              {{ r.type === 'client' ? 'Клиент' : r.type === 'site' ? 'Объект' : 'Договор' }}
            </span>
          </div>
          <button
            v-if="hasMoreResults"
            @click="loadMoreSearch"
            :disabled="searchLoadingMore"
            class="w-full px-4 py-3 text-sm text-primary-600 font-medium disabled:opacity-50 text-center"
          >
            {{ searchLoadingMore ? 'Загрузка...' : `Показать ещё (${searchTotal - searchResults.length})` }}
          </button>
        </div>
      </div>
    </div>

    <!-- Global search bar (desktop) -->
    <div class="hidden md:block fixed top-0 right-0 z-30 p-3" :class="collapsed ? 'left-16' : 'left-64'">
      <div class="relative max-w-xl mx-auto" ref="searchWrapRef">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          <input
            v-model="searchQuery"
            @input="onSearchInput"
            @focus="searchFocused = true"
            @keydown.escape="closeSearch"
            placeholder="Поиск клиентов, объектов, договоров..."
            class="w-full pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent shadow-sm"
          />
          <button v-if="searchQuery" @click="closeSearch" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Выпадающие результаты -->
        <div
          v-if="searchFocused && searchQuery.length >= 1"
          class="absolute top-full mt-1 left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-50 flex flex-col"
          style="max-height: 420px"
        >
          <div v-if="searchLoading" class="px-4 py-3 text-sm text-gray-500 text-center">Поиск...</div>
          <div v-else-if="searchResults.length === 0" class="px-4 py-3 text-sm text-gray-500 text-center">Ничего не найдено</div>
          <div v-else class="flex flex-col min-h-0">
            <div class="overflow-y-auto" style="max-height: 360px">
            <div
              v-for="r in searchResults" :key="`${r.type}-${r.id}`"
              @mousedown.prevent="navigateTo(r.url)"
              @touchstart.prevent="navigateTo(r.url)"
              class="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <div class="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center"
                :class="{
                  'bg-blue-100': r.type === 'client',
                  'bg-green-100': r.type === 'site',
                  'bg-purple-100': r.type === 'contract',
                }"
              >
                <Users v-if="r.type === 'client'" class="w-4 h-4 text-blue-600" />
                <Building2 v-else-if="r.type === 'site'" class="w-4 h-4 text-green-600" />
                <FileText v-else class="w-4 h-4 text-purple-600" />
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-gray-900 truncate">{{ r.title }}</p>
                <p v-if="r.subtitle" class="text-xs text-gray-500 truncate">{{ r.subtitle }}</p>
              </div>
              <span class="text-xs text-gray-400 flex-shrink-0">
                {{ r.type === 'client' ? 'Клиент' : r.type === 'site' ? 'Объект' : 'Договор' }}
              </span>
            </div>
            </div>
            <div v-if="hasMoreResults" class="border-t border-gray-100 flex-shrink-0">
              <button
                @click="loadMoreSearch"
                :disabled="searchLoadingMore"
                class="w-full px-4 py-2.5 text-sm text-primary-600 hover:bg-gray-50 transition-colors font-medium disabled:opacity-50 text-center"
              >
                {{ searchLoadingMore ? 'Загрузка...' : `Показать ещё (${searchTotal - searchResults.length})` }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile overlay -->
    <div
      v-if="mobileOpen"
      class="md:hidden fixed inset-0 bg-black bg-opacity-40 z-30"
      @click="mobileOpen = false"
    />

    <!-- Sidebar -->
    <div
      class="fixed inset-y-0 left-0 bg-white border-r border-gray-200 flex flex-col z-40 transition-all duration-300 ease-in-out"
      :class="[
        collapsed ? 'w-16' : 'w-64',
        mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
      ]"
    >
      <!-- Logo + collapse toggle (desktop only) -->
      <div
        class="hidden md:flex items-center h-16 border-b border-gray-200"
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

      <!-- Mobile sidebar header -->
      <div class="md:hidden flex items-center justify-between h-14 px-4 border-b border-gray-200">
        <h1 class="text-base font-bold text-primary-600">Service System</h1>
        <button @click="mobileOpen = false" class="p-1 text-gray-400 hover:text-gray-600">
          <X class="w-5 h-5" />
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
          @click="mobileOpen = false"
        >
          <component :is="item.icon" class="flex-shrink-0 h-5 w-5" :class="collapsed ? '' : 'mr-3'" />
          <span v-if="!collapsed" class="text-sm font-medium truncate">{{ item.name }}</span>
          <!-- Tooltip in collapsed state (desktop) -->
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
        <!-- Expanded state -->
        <div v-if="!collapsed" class="hidden md:flex items-center mb-3">
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
            >{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
          </RouterLink>
        </div>

        <!-- Mobile user info -->
        <div class="md:hidden flex items-center mb-3">
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ user?.full_name }}</p>
            <p class="text-xs text-gray-500 truncate">{{ userGroupLabel }}</p>
          </div>
        </div>

        <!-- Collapsed: notifications icon (desktop) -->
        <div v-if="collapsed" class="hidden md:flex justify-center mb-2">
          <RouterLink
            to="/notifications"
            class="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg"
            title="Уведомления"
          >
            <Bell class="h-5 w-5" />
            <span
              v-if="unreadCount > 0"
              class="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold"
            >{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
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

    <!-- Main content -->
    <div
      class="transition-all duration-300 ease-in-out pt-14 md:pt-14"
      :class="collapsed ? 'md:ml-16' : 'md:ml-64'"
    >
      <main class="p-3 md:p-8">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  LayoutDashboard, Map, Calendar, Users, Building2,
  ClipboardList, AlertTriangle, ShoppingCart, LogOut, Bell, Settings, ScrollText,
  CheckSquare, BellRing, ChevronLeft, ChevronRight, FileText, Menu, X, Search,
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth.js'
import { notificationsAPI, searchAPI } from '../services/api.js'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const user = computed(() => auth.user)
const unreadCount = ref(0)

const COLLAPSED_KEY = 'sidebar_collapsed'
const collapsed = ref(localStorage.getItem(COLLAPSED_KEY) === 'true')
const mobileOpen = ref(false)

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
  { name: 'Дашборд',     href: '/dashboard', icon: LayoutDashboard, groups: ['office_group', 'admin_group'] },
  { name: 'Карта',       href: '/map',        icon: Map,             groups: ['office_group', 'admin_group', 'master_group'] },
  { name: 'Календарь',   href: '/calendar',   icon: Calendar,        groups: ['office_group', 'admin_group', 'master_group'] },
  { name: 'Мои выезды',  href: '/my-visits',  icon: ClipboardList,   groups: ['master_group'] },
  { name: 'Клиенты',     href: '/clients',    icon: Users,           groups: ['office_group', 'admin_group'] },
  { name: 'Договоры',    href: '/contracts',  icon: FileText,        groups: ['office_group', 'admin_group'] },
  { name: 'Объекты',     href: '/sites',      icon: Building2,       groups: ['office_group', 'admin_group'] },
  { name: 'Выезды',      href: '/visits',     icon: ClipboardList,   groups: ['office_group', 'admin_group'] },
  { name: 'Дефекты',     href: '/defects',    icon: AlertTriangle,   groups: ['office_group', 'admin_group'] },
  { name: 'Закупки',     href: '/purchases',  icon: ShoppingCart,    groups: ['office_group', 'admin_group'] },
  { name: 'Задачи',      href: '/tasks',      icon: CheckSquare,     groups: ['office_group', 'admin_group'] },
  { name: 'Напоминания', href: '/reminders',  icon: BellRing,        groups: ['office_group', 'admin_group'] },
  { name: 'Журнал',      href: '/logs',       icon: ScrollText,      groups: ['office_group', 'admin_group'] },
  { name: 'Админ',       href: '/admin',      icon: Settings,        groups: ['admin_group'] },
]

const filteredNav = computed(() =>
  allNav.filter((item) => item.groups.some((g) => auth.groups.includes(g)))
)

async function fetchUnread() {
  try {
    const res = await notificationsAPI.getUnreadCount()
    unreadCount.value = res.data.count
  } catch {}
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

// ── Глобальный поиск ──────────────────────────────────────────────────────
const SEARCH_LIMIT = 5
const searchQuery = ref('')
const searchResults = ref([])
const searchTotal = ref(0)
const searchLoading = ref(false)
const searchLoadingMore = ref(false)
const searchFocused = ref(false)
const searchWrapRef = ref(null)
const mobileSearchWrapRef = ref(null)

const hasMoreResults = computed(() => searchResults.value.length < searchTotal.value)

let searchTimeout = null

function onSearchInput() {
  clearTimeout(searchTimeout)
  if (searchQuery.value.length < 1) {
    searchResults.value = []
    searchTotal.value = 0
    return
  }
  searchLoading.value = true
  searchTimeout = setTimeout(async () => {
    try {
      const res = await searchAPI.search(searchQuery.value, { limit: SEARCH_LIMIT, offset: 0 })
      searchResults.value = res.data.results
      searchTotal.value = res.data.clients_total + res.data.sites_total + res.data.contracts_total
    } catch {
      searchResults.value = []
      searchTotal.value = 0
    } finally {
      searchLoading.value = false
    }
  }, 300)
}

async function loadMoreSearch() {
  if (searchLoadingMore.value || !hasMoreResults.value) return
  searchLoadingMore.value = true
  try {
    const res = await searchAPI.search(searchQuery.value, { limit: SEARCH_LIMIT, offset: searchResults.value.length })
    searchResults.value.push(...res.data.results)
    searchTotal.value = res.data.clients_total + res.data.sites_total + res.data.contracts_total
  } catch {} finally {
    searchLoadingMore.value = false
  }
}

function closeSearch() {
  searchQuery.value = ''
  searchResults.value = []
  searchTotal.value = 0
  searchFocused.value = false
}

function navigateTo(url) {
  closeSearch()
  router.push(url)
}

function onClickOutside(e) {
  const inDesktop = searchWrapRef.value && searchWrapRef.value.contains(e.target)
  const inMobile = mobileSearchWrapRef.value && mobileSearchWrapRef.value.contains(e.target)
  if (!inDesktop && !inMobile) {
    searchFocused.value = false
  }
}

let pollInterval = null

onMounted(() => {
  fetchUnread()
  pollInterval = setInterval(fetchUnread, 30000)
  document.addEventListener('mousedown', onClickOutside)
})

onUnmounted(() => {
  clearInterval(pollInterval)
  document.removeEventListener('mousedown', onClickOutside)
})

watch(() => route.path, fetchUnread)
</script>
