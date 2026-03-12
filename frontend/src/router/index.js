import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useConfigStore } from '../stores/config.js'

const routes = [
  { path: '/login', component: () => import('../pages/LoginPage.vue'), meta: { public: true } },
  {
    path: '/dashboard',
    component: () => import('../pages/DashboardPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  {
    path: '/map',
    component: () => import('../pages/MapPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group', 'master_group'] },
  },
  {
    path: '/calendar',
    component: () => import('../pages/CalendarPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/clients',
    component: () => import('../pages/ClientsPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  {
    path: '/clients/:id',
    component: () => import('../pages/ClientDetailPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  {
    path: '/sites',
    component: () => import('../pages/SitesPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  {
    path: '/sites/:id',
    component: () => import('../pages/SiteDetailPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  {
    path: '/visits',
    component: () => import('../pages/VisitsPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  {
    path: '/my-visits',
    component: () => import('../pages/MyVisitsPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['master_group'] },
  },
  {
    path: '/defects',
    component: () => import('../pages/DefectsPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  {
    path: '/purchases',
    component: () => import('../pages/PurchasesPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  {
    path: '/notifications',
    component: () => import('../pages/NotificationsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks',
    component: () => import('../pages/TasksPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['office_group', 'admin_group'] },
  },
  {
    path: '/logs',
    component: () => import('../pages/LogsPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['admin_group', 'office_group'] },
  },
  {
    path: '/admin',
    component: () => import('../pages/AdminPage.vue'),
    meta: { requiresAuth: true, allowedGroups: ['admin_group'] },
  },
  { path: '/', redirect: () => '/dashboard' },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  const config = useConfigStore()

  if (to.meta.public) return true

  if (!auth.isAuthenticated) {
    return '/login'
  }

  // Load config on first authenticated navigation
  if (!config.loaded) {
    await config.loadAll()
  }

  const userGroups = auth.groups
  if (to.meta.allowedGroups && !to.meta.allowedGroups.some((g) => userGroups.includes(g))) {
    // Redirect to default page for first group, or notifications
    if (userGroups.includes('master_group')) return '/my-visits'
    if (userGroups.includes('office_group')) return '/dashboard'
    return '/notifications'
  }

  // Root redirect based on groups
  if (to.path === '/') {
    if (userGroups.includes('master_group') && !userGroups.includes('office_group') && !userGroups.includes('admin_group')) {
      return '/my-visits'
    }
    return '/dashboard'
  }

  return true
})

export default router
