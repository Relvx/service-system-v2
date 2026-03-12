<template>
  <Layout>
    <div class="max-w-2xl">
      <h1 class="text-3xl font-bold text-gray-900 mb-8">Напоминания</h1>

      <!-- Общие напоминания -->
      <div class="card mb-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Globe class="w-5 h-5 text-primary-600" />
          Общие
          <span class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-normal">видны всем сотрудникам офиса</span>
        </h2>

        <!-- Add form -->
        <form @submit.prevent="addReminder(false)" class="flex gap-2 mb-4">
          <input
            v-model="newShared"
            class="input flex-1"
            placeholder="Новое общее напоминание..."
          />
          <button type="submit" :disabled="!newShared.trim()" class="btn btn-primary disabled:opacity-50">
            <Plus class="w-4 h-4" />
          </button>
        </form>

        <div v-if="shared.length === 0" class="text-sm text-gray-400 py-2">Нет общих напоминаний</div>
        <ul v-else class="space-y-2">
          <li
            v-for="r in shared" :key="r.id"
            class="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0"
          >
            <span class="flex-1 text-gray-800 text-sm">{{ r.text }}</span>
            <span class="text-xs text-gray-400 flex-shrink-0 mt-0.5">{{ r.created_by_name }}</span>
            <button
              @click="deleteReminder(r.id)"
              class="text-gray-300 hover:text-red-500 transition-colors flex-shrink-0"
              title="Удалить"
            >
              <X class="w-4 h-4" />
            </button>
          </li>
        </ul>
      </div>

      <!-- Личные напоминания -->
      <div class="card">
        <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Lock class="w-5 h-5 text-amber-500" />
          Личные
          <span class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-normal">видны только вам</span>
        </h2>

        <!-- Add form -->
        <form @submit.prevent="addReminder(true)" class="flex gap-2 mb-4">
          <input
            v-model="newPersonal"
            class="input flex-1"
            placeholder="Новое личное напоминание..."
          />
          <button type="submit" :disabled="!newPersonal.trim()" class="btn btn-primary disabled:opacity-50">
            <Plus class="w-4 h-4" />
          </button>
        </form>

        <div v-if="personal.length === 0" class="text-sm text-gray-400 py-2">Нет личных напоминаний</div>
        <ul v-else class="space-y-2">
          <li
            v-for="r in personal" :key="r.id"
            class="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0"
          >
            <span class="flex-1 text-gray-800 text-sm">{{ r.text }}</span>
            <button
              @click="deleteReminder(r.id)"
              class="text-gray-300 hover:text-red-500 transition-colors flex-shrink-0"
              title="Удалить"
            >
              <X class="w-4 h-4" />
            </button>
          </li>
        </ul>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, X, Globe, Lock } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { remindersAPI } from '../services/api.js'

const reminders = ref([])
const newShared = ref('')
const newPersonal = ref('')

const shared = computed(() => reminders.value.filter(r => !r.is_personal))
const personal = computed(() => reminders.value.filter(r => r.is_personal))

async function load() {
  const res = await remindersAPI.getAll()
  reminders.value = res.data
}

async function addReminder(isPersonal) {
  const text = isPersonal ? newPersonal.value.trim() : newShared.value.trim()
  if (!text) return
  try {
    await remindersAPI.create({ text, is_personal: isPersonal })
    if (isPersonal) newPersonal.value = ''
    else newShared.value = ''
    await load()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function deleteReminder(id) {
  try {
    await remindersAPI.delete(id)
    await load()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(load)
</script>
