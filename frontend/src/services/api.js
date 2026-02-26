import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  getMe: () => api.get('/auth/me'),
  changePassword: (current_password, new_password) =>
    api.put('/auth/change-password', { current_password, new_password }),
}

export const usersAPI = {
  getAll: (params) => api.get('/users', { params }),
  getMasters: () => api.get('/users/masters'),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
}

export const clientsAPI = {
  getAll: (params) => api.get('/clients', { params }),
  getById: (id) => api.get(`/clients/${id}`),
  create: (data) => api.post('/clients', data),
  update: (id, data) => api.put(`/clients/${id}`, data),
  delete: (id) => api.delete(`/clients/${id}`),
}

export const sitesAPI = {
  getAll: (params) => api.get('/sites', { params }),
  getById: (id) => api.get(`/sites/${id}`),
  create: (data) => api.post('/sites', data),
  update: (id, data) => api.put(`/sites/${id}`, data),
  delete: (id) => api.delete(`/sites/${id}`),
}

export const visitsAPI = {
  getAll: (params) => api.get('/visits', { params }),
  getCalendar: (start, end) => api.get('/visits/calendar', { params: { start, end } }),
  getById: (id) => api.get(`/visits/${id}`),
  create: (data) => api.post('/visits', data),
  update: (id, data) => api.put(`/visits/${id}`, data),
  complete: (id, data) => api.post(`/visits/${id}/complete`, data),
  delete: (id) => api.delete(`/visits/${id}`),
}

export const defectsAPI = {
  getAll: (params) => api.get('/defects', { params }),
  create: (data) => api.post('/defects', data),
  update: (id, data) => api.put(`/defects/${id}`, data),
}

export const purchasesAPI = {
  getAll: (params) => api.get('/purchases', { params }),
  create: (data) => api.post('/purchases', data),
  update: (id, data) => api.put(`/purchases/${id}`, data),
}

export const attachmentsAPI = {
  getAll: (visitId) => api.get('/attachments', { params: { visit_id: visitId } }),
  upload: (data) => api.post('/attachments', data),
}

export const notificationsAPI = {
  getAll: () => api.get('/notifications'),
  markAsRead: (id) => api.put(`/notifications/${id}/read`),
  markAsUnread: (id) => api.put(`/notifications/${id}/unread`),
}

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
}

export const configAPI = {
  getVisitStatuses: () => api.get('/config/visit-statuses'),
  getVisitTypes: () => api.get('/config/visit-types'),
  getPriorities: () => api.get('/config/priorities'),
  getDefectStatuses: () => api.get('/config/defect-statuses'),
  getDefectActionTypes: () => api.get('/config/defect-action-types'),
  getAttachmentKinds: () => api.get('/config/attachment-kinds'),
  getPurchaseStatuses: () => api.get('/config/purchase-statuses'),
  getServiceFrequencies: () => api.get('/config/service-frequencies'),
  // Admin CRUD
  createItem: (resource, data) => api.post(`/config/${resource}`, data),
  updateItem: (resource, sysname, data) => api.put(`/config/${resource}/${sysname}`, data),
  deleteItem: (resource, sysname) => api.delete(`/config/${resource}/${sysname}`),
}

export const adminAPI = {
  // Users
  getUsers: () => api.get('/admin/users'),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  addUserToGroup: (userId, groupSysname) =>
    api.post(`/admin/users/${userId}/groups/${groupSysname}`),
  removeUserFromGroup: (userId, groupSysname) =>
    api.delete(`/admin/users/${userId}/groups/${groupSysname}`),

  // Permission groups
  getPermissionGroups: () => api.get('/admin/permission-groups'),
  createPermissionGroup: (data) => api.post('/admin/permission-groups', data),
  updatePermissionGroup: (sysname, data) => api.put(`/admin/permission-groups/${sysname}`, data),
  deletePermissionGroup: (sysname) => api.delete(`/admin/permission-groups/${sysname}`),

  // Permissions
  getPermissions: () => api.get('/admin/permissions'),
  addPermissionToGroup: (groupSysname, permSysname) =>
    api.post(`/admin/permission-groups/${groupSysname}/permissions/${permSysname}`),
  removePermissionFromGroup: (groupSysname, permSysname) =>
    api.delete(`/admin/permission-groups/${groupSysname}/permissions/${permSysname}`),
}

export default api
