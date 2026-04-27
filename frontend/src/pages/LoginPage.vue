<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-full mb-4">
          <LogIn class="w-8 h-8 text-white" />
        </div>
        <h1 class="text-3xl font-bold text-gray-900">Service System v2</h1>
        <p class="text-gray-600 mt-2">Система учета выездов</p>
      </div>

      <!-- Login Form -->
      <div class="bg-white rounded-lg shadow-xl p-8">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {{ error }}
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Логин</label>
            <input v-model="username" type="text" class="input" placeholder="Введите логин" required autofocus autocomplete="username" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Пароль</label>
            <input v-model="password" type="password" class="input" placeholder="••••••••" required autocomplete="current-password" />
          </div>

          <button type="submit" :disabled="loading" class="w-full btn btn-primary py-3 text-base disabled:opacity-50 disabled:cursor-not-allowed">
            {{ loading ? 'Вход...' : 'Войти' }}
          </button>
        </form>

      </div>

      <p class="text-center text-sm text-gray-600 mt-6">© 2026 Service System v2</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { LogIn } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth.js'
import { useConfigStore } from '../stores/config.js'

const router = useRouter()
const auth = useAuthStore()
const config = useConfigStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    const user = await auth.login(username.value, password.value)
    await config.loadAll()
    const groups = user.groups || []
    if (groups.includes('master_group') && !groups.includes('office_group') && !groups.includes('admin_group')) {
      router.push('/my-visits')
    } else {
      router.push('/dashboard')
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Неверный логин или пароль'
  } finally {
    loading.value = false
  }
}
</script>
