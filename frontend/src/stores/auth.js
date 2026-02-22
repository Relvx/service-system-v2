import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../services/api.js'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const role = computed(() => user.value?.role || null)

  async function login(email, password) {
    const res = await authAPI.login(email, password)
    token.value = res.data.token
    user.value = res.data.user
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    return user.value
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function fetchMe() {
    try {
      const res = await authAPI.getMe()
      user.value = res.data
      localStorage.setItem('user', JSON.stringify(res.data))
    } catch {
      logout()
    }
  }

  return { token, user, isAuthenticated, role, login, logout, fetchMe }
})
