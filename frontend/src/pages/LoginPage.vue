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
            <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input v-model="email" type="email" class="input" placeholder="your@email.com" required autofocus />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Пароль</label>
            <input v-model="password" type="password" class="input" placeholder="••••••••" required />
          </div>

          <button type="submit" :disabled="loading" class="w-full btn btn-primary py-3 text-base disabled:opacity-50 disabled:cursor-not-allowed">
            {{ loading ? 'Вход...' : 'Войти' }}
          </button>
        </form>

        <!-- Test Accounts -->
        <div class="mt-6 pt-6 border-t border-gray-200">
          <p class="text-sm text-gray-600 mb-3 text-center">Тестовые аккаунты:</p>
          <div class="space-y-2">
            <button
              v-for="acc in testAccounts"
              :key="acc.email"
              type="button"
              @click="email = acc.email; password = acc.password"
              class="w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <div class="font-medium text-gray-900">{{ acc.role }}</div>
              <div class="text-gray-500">{{ acc.email }}</div>
            </button>
          </div>
        </div>
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

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const testAccounts = [
  { email: 'admin@system.local', password: 'admin123', role: 'Администратор' },
  { email: 'master1@system.local', password: 'admin123', role: 'Мастер' },
  { email: 'office1@system.local', password: 'admin123', role: 'Офис' },
]

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    const user = await auth.login(email.value, password.value)
    await config.loadAll()
    const groups = user.groups || []
    if (groups.includes('master_group') && !groups.includes('office_group') && !groups.includes('admin_group')) {
      router.push('/my-visits')
    } else {
      router.push('/dashboard')
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Неверный email или пароль'
  } finally {
    loading.value = false
  }
}
</script>
