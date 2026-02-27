<template>
  <Layout>
    <div>
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">Администрирование</h1>
        <p class="text-gray-600 mt-1">Управление пользователями, группами прав и справочниками</p>
      </div>

      <!-- Tabs -->
      <div class="border-b border-gray-200 mb-6">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            class="py-3 px-1 border-b-2 text-sm font-medium transition-colors"
            :class="activeTab === tab.id
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Users tab -->
      <div v-if="activeTab === 'users'">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-semibold text-gray-900">Пользователи</h2>
          <button @click="openUserCreate" class="btn btn-primary flex items-center">
            <Plus class="w-4 h-4 mr-2" /> Добавить
          </button>
        </div>

        <div v-if="usersLoading" class="flex justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>

        <div v-else class="card overflow-hidden p-0">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="text-left px-4 py-3 font-medium text-gray-600">Имя</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600">Группы</th>
                <th class="text-left px-4 py-3 font-medium text-gray-600">Статус</th>
                <th class="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="u in adminUsers" :key="u.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 font-medium text-gray-900">{{ u.full_name }}</td>
                <td class="px-4 py-3 text-gray-600">{{ u.email }}</td>
                <td class="px-4 py-3">
                  <span
                    v-for="g in u.groups" :key="g"
                    class="inline-block px-2 py-0.5 rounded-full text-xs bg-primary-100 text-primary-700 mr-1"
                  >{{ g }}</span>
                </td>
                <td class="px-4 py-3">
                  <span
                    class="px-2 py-0.5 rounded-full text-xs"
                    :class="u.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
                  >{{ u.is_active ? 'Активен' : 'Отключён' }}</span>
                </td>
                <td class="px-4 py-3 text-right">
                  <button @click="openUserEdit(u)" class="text-gray-400 hover:text-gray-700 mr-3">
                    <Pencil class="w-4 h-4" />
                  </button>
                  <button @click="openUserGroups(u)" class="text-gray-400 hover:text-blue-600">
                    <Shield class="w-4 h-4" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Permission groups tab -->
      <div v-if="activeTab === 'groups'">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-semibold text-gray-900">Группы прав</h2>
          <button @click="openGroupCreate" class="btn btn-primary flex items-center">
            <Plus class="w-4 h-4 mr-2" /> Добавить
          </button>
        </div>

        <div v-if="groupsLoading" class="flex justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>

        <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div v-for="g in permissionGroups" :key="g.id" class="card">
            <div class="flex justify-between items-start mb-3">
              <div>
                <h3 class="font-semibold text-gray-900">{{ g.display_name }}</h3>
                <p class="text-xs text-gray-500">{{ g.sysname }} → {{ g.default_redirect }}</p>
              </div>
              <div class="flex gap-2">
                <button @click="openPermEdit(g)" class="text-gray-400 hover:text-primary-600" title="Редактировать права">
                  <Key class="w-4 h-4" />
                </button>
                <button @click="openGroupEdit(g)" class="text-gray-400 hover:text-gray-700" title="Изменить группу">
                  <Pencil class="w-4 h-4" />
                </button>
              </div>
            </div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="p in g.permissions" :key="p.sysname"
                class="px-2 py-0.5 rounded text-xs bg-primary-50 text-primary-700"
              >{{ p.display_name }}</span>
              <span v-if="!g.permissions.length" class="text-xs text-gray-400">Нет прав</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Config tab -->
      <div v-if="activeTab === 'config'">
        <div class="mb-4">
          <h2 class="text-xl font-semibold text-gray-900 mb-3">Справочники</h2>
          <div class="flex flex-wrap gap-2 mb-4">
            <button
              v-for="res in configResources"
              :key="res.key"
              @click="activeConfig = res.key"
              class="px-3 py-1.5 text-sm rounded-lg transition-colors"
              :class="activeConfig === res.key
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            >{{ res.label }}</button>
          </div>
        </div>

        <div v-if="activeConfig" class="card">
          <div class="flex justify-between items-center mb-4">
            <h3 class="font-semibold text-gray-900">
              {{ configResources.find(r => r.key === activeConfig)?.label }}
            </h3>
            <button @click="openConfigCreate" class="btn btn-primary flex items-center text-sm">
              <Plus class="w-4 h-4 mr-1" /> Добавить
            </button>
          </div>

          <div v-if="configLoading" class="flex justify-center py-8">
            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
          </div>

          <table v-else class="w-full text-sm">
            <thead class="border-b border-gray-200">
              <tr>
                <th class="text-left pb-2 font-medium text-gray-600">sysname</th>
                <th class="text-left pb-2 font-medium text-gray-600">Название</th>
                <th class="pb-2"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="item in configItems" :key="item.id" class="hover:bg-gray-50">
                <td class="py-2 pr-4 text-gray-500 font-mono text-xs">{{ item.sysname }}</td>
                <td class="py-2 pr-4 text-gray-900">{{ item.display_name }}</td>
                <td class="py-2 text-right">
                  <button @click="openConfigEdit(item)" class="text-gray-400 hover:text-gray-700 mr-2">
                    <Pencil class="w-4 h-4" />
                  </button>
                  <button @click="deleteConfigItem(item)" class="text-gray-400 hover:text-red-600">
                    <Trash2 class="w-4 h-4" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- User create/edit modal -->
    <div v-if="userModal.open" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold mb-4">{{ userModal.isEdit ? 'Изменить пользователя' : 'Новый пользователь' }}</h3>
        <div class="space-y-3">
          <input v-if="!userModal.isEdit" v-model="userForm.email" type="email" placeholder="Email" class="input" />
          <input v-if="!userModal.isEdit" v-model="userForm.password" type="password" placeholder="Пароль" class="input" />
          <input v-model="userForm.full_name" type="text" placeholder="Полное имя" class="input" />
          <input v-model="userForm.phone" type="text" placeholder="Телефон" class="input" />
          <label v-if="userModal.isEdit" class="flex items-center gap-2 text-sm">
            <input v-model="userForm.is_active" type="checkbox" />
            Активен
          </label>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="saveUser" class="btn btn-primary flex-1">Сохранить</button>
          <button @click="userModal.open = false" class="btn flex-1">Отмена</button>
        </div>
      </div>
    </div>

    <!-- User groups modal -->
    <div v-if="groupAssignModal.open" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold mb-2">Группы: {{ groupAssignModal.user?.full_name }}</h3>
        <div class="space-y-2 mb-4">
          <label v-for="g in permissionGroups" :key="g.sysname" class="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              :checked="groupAssignModal.userGroups.includes(g.sysname)"
              @change="toggleUserGroup(g.sysname, $event.target.checked)"
            />
            {{ g.display_name }} ({{ g.sysname }})
          </label>
        </div>
        <button @click="groupAssignModal.open = false" class="btn w-full">Закрыть</button>
      </div>
    </div>

    <!-- Group create/edit modal -->
    <div v-if="groupModal.open" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold mb-4">{{ groupModal.isEdit ? 'Изменить группу' : 'Новая группа' }}</h3>
        <div class="space-y-3">
          <input v-if="!groupModal.isEdit" v-model="groupForm.sysname" type="text" placeholder="sysname" class="input" />
          <input v-model="groupForm.display_name" type="text" placeholder="Название" class="input" />
          <input v-model="groupForm.default_redirect" type="text" placeholder="Редирект (напр. /dashboard)" class="input" />
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="saveGroup" class="btn btn-primary flex-1">Сохранить</button>
          <button @click="groupModal.open = false" class="btn flex-1">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Permission editing modal for group -->
    <div v-if="permEditModal.open" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg max-h-[80vh] flex flex-col">
        <h3 class="text-lg font-semibold mb-1">Права группы: {{ permEditModal.group?.display_name }}</h3>
        <p class="text-xs text-gray-500 mb-4">Отметьте нужные права и снимите лишние</p>

        <div class="overflow-y-auto flex-1 space-y-4">
          <div v-for="(perms, resource) in permsByResource" :key="resource">
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              {{ RESOURCE_LABELS[resource] || resource }}
            </p>
            <div class="space-y-1 pl-1">
              <label
                v-for="p in perms"
                :key="p.sysname"
                class="flex items-center gap-2 text-sm cursor-pointer select-none"
              >
                <input
                  type="checkbox"
                  :checked="permEditModal.groupPerms.includes(p.sysname)"
                  @change="toggleGroupPerm(p.sysname, $event.target.checked)"
                  class="accent-primary-600"
                />
                <span class="text-gray-800">{{ p.display_name }}</span>
                <span class="text-gray-400 font-mono text-xs ml-auto">{{ p.sysname }}</span>
              </label>
            </div>
          </div>
        </div>

        <div class="mt-5 flex justify-end">
          <button @click="permEditModal.open = false" class="btn btn-primary">Готово</button>
        </div>
      </div>
    </div>

    <!-- Config item create/edit modal -->
    <div v-if="configModal.open" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold mb-4">{{ configModal.isEdit ? 'Изменить запись' : 'Новая запись' }}</h3>
        <div class="space-y-3">
          <input v-if="!configModal.isEdit" v-model="configForm.sysname" type="text" placeholder="sysname" class="input" />
          <input v-model="configForm.display_name" type="text" placeholder="Название" class="input" />
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="saveConfigItem" class="btn btn-primary flex-1">Сохранить</button>
          <button @click="configModal.open = false" class="btn flex-1">Отмена</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Plus, Pencil, Trash2, Shield, Key } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import { adminAPI, configAPI } from '../services/api.js'

const activeTab = ref('users')
const tabs = [
  { id: 'users',  label: 'Пользователи' },
  { id: 'groups', label: 'Группы прав' },
  { id: 'config', label: 'Справочники' },
]

// ─── Users ──────────────────────────────────────────────────────────────────

const adminUsers = ref([])
const usersLoading = ref(false)

async function loadUsers() {
  usersLoading.value = true
  try {
    const res = await adminAPI.getUsers()
    adminUsers.value = res.data
  } finally {
    usersLoading.value = false
  }
}

const userModal = ref({ open: false, isEdit: false, userId: null })
const userForm = ref({ email: '', password: '', full_name: '', phone: '', is_active: true })

function openUserCreate() {
  userForm.value = { email: '', password: '', full_name: '', phone: '', is_active: true }
  userModal.value = { open: true, isEdit: false, userId: null }
}

function openUserEdit(u) {
  userForm.value = { full_name: u.full_name, phone: u.phone || '', is_active: u.is_active }
  userModal.value = { open: true, isEdit: true, userId: u.id }
}

async function saveUser() {
  if (userModal.value.isEdit) {
    await adminAPI.updateUser(userModal.value.userId, userForm.value)
  } else {
    await adminAPI.createUser(userForm.value)
  }
  userModal.value.open = false
  await loadUsers()
}

// Groups assignment for a user
const groupAssignModal = ref({ open: false, user: null, userGroups: [] })

function openUserGroups(u) {
  groupAssignModal.value = { open: true, user: u, userGroups: [...u.groups] }
}

async function toggleUserGroup(groupSysname, checked) {
  const userId = groupAssignModal.value.user.id
  if (checked) {
    await adminAPI.addUserToGroup(userId, groupSysname)
    groupAssignModal.value.userGroups.push(groupSysname)
  } else {
    await adminAPI.removeUserFromGroup(userId, groupSysname)
    groupAssignModal.value.userGroups = groupAssignModal.value.userGroups.filter(g => g !== groupSysname)
  }
  await loadUsers()
  // Update user in modal to reflect changes
  const updated = adminUsers.value.find(u => u.id === userId)
  if (updated) groupAssignModal.value.user = updated
}

// ─── Permission Groups ───────────────────────────────────────────────────────

const permissionGroups = ref([])
const groupsLoading = ref(false)

async function loadGroups() {
  groupsLoading.value = true
  try {
    const res = await adminAPI.getPermissionGroups()
    permissionGroups.value = res.data
  } finally {
    groupsLoading.value = false
  }
}

const groupModal = ref({ open: false, isEdit: false, sysname: null })
const groupForm = ref({ sysname: '', display_name: '', default_redirect: '/dashboard' })

function openGroupCreate() {
  groupForm.value = { sysname: '', display_name: '', default_redirect: '/dashboard' }
  groupModal.value = { open: true, isEdit: false, sysname: null }
}

function openGroupEdit(g) {
  groupForm.value = { display_name: g.display_name, default_redirect: g.default_redirect }
  groupModal.value = { open: true, isEdit: true, sysname: g.sysname }
}

async function saveGroup() {
  if (groupModal.value.isEdit) {
    await adminAPI.updatePermissionGroup(groupModal.value.sysname, groupForm.value)
  } else {
    await adminAPI.createPermissionGroup(groupForm.value)
  }
  groupModal.value.open = false
  await loadGroups()
}

// ─── All permissions + group permission editing ───────────────────────────────

const allPermissions = ref([])

async function loadPermissions() {
  const res = await adminAPI.getPermissions()
  allPermissions.value = res.data
}

const RESOURCE_LABELS = {
  visits:    'Выезды',
  clients:   'Клиенты',
  sites:     'Объекты',
  defects:   'Дефекты',
  purchases: 'Закупки',
  users:     'Пользователи',
  reports:   'Отчёты',
  config:    'Справочники',
  admin:     'Администрирование',
}

const permsByResource = computed(() => {
  const grouped = {}
  for (const p of allPermissions.value) {
    const r = p.resource || 'other'
    if (!grouped[r]) grouped[r] = []
    grouped[r].push(p)
  }
  return grouped
})

const permEditModal = ref({ open: false, group: null, groupPerms: [] })

function openPermEdit(g) {
  permEditModal.value = {
    open: true,
    group: g,
    groupPerms: g.permissions.map((p) => p.sysname),
  }
}

async function toggleGroupPerm(permSysname, checked) {
  const groupSysname = permEditModal.value.group.sysname
  if (checked) {
    await adminAPI.addPermissionToGroup(groupSysname, permSysname)
    permEditModal.value.groupPerms.push(permSysname)
  } else {
    await adminAPI.removePermissionFromGroup(groupSysname, permSysname)
    permEditModal.value.groupPerms = permEditModal.value.groupPerms.filter((s) => s !== permSysname)
  }
  await loadGroups()
  // Sync updated group into modal
  const updated = permissionGroups.value.find((g) => g.sysname === groupSysname)
  if (updated) {
    permEditModal.value.group = updated
    permEditModal.value.groupPerms = updated.permissions.map((p) => p.sysname)
  }
}

// ─── Config ──────────────────────────────────────────────────────────────────

const activeConfig = ref(null)
const configItems = ref([])
const configLoading = ref(false)

const configResources = [
  { key: 'visit-statuses',      label: 'Статусы выездов' },
  { key: 'visit-types',         label: 'Типы выездов' },
  { key: 'priorities',          label: 'Приоритеты' },
  { key: 'defect-statuses',     label: 'Статусы дефектов' },
  { key: 'defect-action-types', label: 'Типы действий по дефектам' },
  { key: 'attachment-kinds',    label: 'Виды вложений' },
  { key: 'purchase-statuses',   label: 'Статусы закупок' },
  { key: 'service-frequencies', label: 'Частота обслуживания' },
]

async function loadConfigItems() {
  if (!activeConfig.value) return
  configLoading.value = true
  try {
    const methodMap = {
      'visit-statuses':      configAPI.getVisitStatuses,
      'visit-types':         configAPI.getVisitTypes,
      'priorities':          configAPI.getPriorities,
      'defect-statuses':     configAPI.getDefectStatuses,
      'defect-action-types': configAPI.getDefectActionTypes,
      'attachment-kinds':    configAPI.getAttachmentKinds,
      'purchase-statuses':   configAPI.getPurchaseStatuses,
      'service-frequencies': configAPI.getServiceFrequencies,
    }
    const fn = methodMap[activeConfig.value]
    if (fn) {
      const res = await fn()
      configItems.value = res.data
    }
  } finally {
    configLoading.value = false
  }
}

watch(activeConfig, loadConfigItems)

const configModal = ref({ open: false, isEdit: false, sysname: null })
const configForm = ref({ sysname: '', display_name: '' })

function openConfigCreate() {
  configForm.value = { sysname: '', display_name: '' }
  configModal.value = { open: true, isEdit: false, sysname: null }
}

function openConfigEdit(item) {
  configForm.value = { display_name: item.display_name }
  configModal.value = { open: true, isEdit: true, sysname: item.sysname }
}

async function saveConfigItem() {
  if (configModal.value.isEdit) {
    await configAPI.updateItem(activeConfig.value, configModal.value.sysname, configForm.value)
  } else {
    await configAPI.createItem(activeConfig.value, configForm.value)
  }
  configModal.value.open = false
  await loadConfigItems()
}

async function deleteConfigItem(item) {
  if (!confirm(`Удалить "${item.display_name}"?`)) return
  await configAPI.deleteItem(activeConfig.value, item.sysname)
  await loadConfigItems()
}

// ─── Initial load ─────────────────────────────────────────────────────────────

onMounted(async () => {
  await Promise.all([loadUsers(), loadGroups(), loadPermissions()])
})
</script>
