import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useConfigStore } from '../stores/config.js'

const routes = [
  { path: '/login', component: () => import('../pages/LoginPage.vue'), meta: { public: true } },
  {
    path: '/dashboard',
    component: () => import('../pages/DashboardPage.vue'),
    meta: { requiresAuth: true, allowedRoles: ['office', 'admin'] },
  },
  {
    path: '/map',
    component: () => import('../pages/MapPage.vue'),
    meta: { requiresAuth: true, allowedRoles: ['office', 'admin'] },
  },
  {
    path: '/calendar',
    component: () => import('../pages/CalendarPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/clients',
    component: () => import('../pages/ClientsPage.vue'),
    meta: { requiresAuth: true, allowedRoles: ['office', 'admin'] },
  },
  {
    path: '/sites',
    component: () => import('../pages/SitesPage.vue'),
    meta: { requiresAuth: true, allowedRoles: ['office', 'admin'] },
  },
  {
    path: '/visits',
    component: () => import('../pages/VisitsPage.vue'),
    meta: { requiresAuth: true, allowedRoles: ['office', 'admin'] },
  },
  {
    path: '/my-visits',
    component: () => import('../pages/MyVisitsPage.vue'),
    meta: { requiresAuth: true, allowedRoles: ['master'] },
  },
  {
    path: '/defects',
    component: () => import('../pages/DefectsPage.vue'),
    meta: { requiresAuth: true, allowedRoles: ['office', 'admin'] },
  },
  {
    path: '/purchases',
    component: () => import('../pages/PurchasesPage.vue'),
    meta: { requiresAuth: true, allowedRoles: ['office', 'admin'] },
  },
  {
    path: '/notifications',
    component: () => import('../pages/NotificationsPage.vue'),
    meta: { requiresAuth: true },
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

  const role = auth.role
  if (to.meta.allowedRoles && !to.meta.allowedRoles.includes(role)) {
    // redirect to role default
    const roleConfig = config.roles.find((r) => r.code === role)
    return roleConfig?.default_redirect || '/notifications'
  }

  // Root redirect by role
  if (to.path === '/') {
    const roleConfig = config.roles.find((r) => r.code === role)
    return roleConfig?.default_redirect || '/notifications'
  }

  return true
})

export default router
