<template>
  <Layout>
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>

    <div v-else-if="client">
      <!-- Шапка -->
      <div class="flex items-start justify-between flex-wrap gap-y-3 mb-6">
        <div class="flex items-center gap-3 min-w-0">
          <button @click="$router.back()" class="text-gray-500 hover:text-gray-700 flex-shrink-0">
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div class="min-w-0">
            <h1 class="text-xl md:text-3xl font-bold text-gray-900 break-words">{{ client.name }}</h1>
            <p v-if="client.inn" class="text-gray-500 mt-0.5 text-sm">ИНН: {{ client.inn }}<span v-if="client.kpp"> / КПП: {{ client.kpp }}</span></p>
          </div>
          <span v-if="client.is_archived" class="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full flex-shrink-0">Архив</span>
          <span v-else-if="!client.is_active" class="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full flex-shrink-0">Неактивен</span>
        </div>
        <div class="flex items-center gap-2 flex-wrap flex-shrink-0">
          <template v-if="canManage && !client.is_archived">
            <button @click="toggleActive" :disabled="toggling" class="btn btn-secondary text-xs disabled:opacity-50">
              {{ client.is_active ? 'Деактивировать' : 'Активировать' }}
            </button>
          </template>
          <template v-if="(auth.hasGroup('admin_group') || auth.hasGroup('office_group')) && client.is_archived">
            <button @click="handleUnarchive" :disabled="toggling" class="btn btn-secondary text-xs disabled:opacity-50">
              Восстановить
            </button>
          </template>
          <button v-if="!client.is_archived" @click="openEdit" class="btn btn-secondary flex items-center">
            <Edit class="w-4 h-4 mr-2" />Редактировать
          </button>
          <button
            v-if="auth.hasGroup('admin_group') || auth.hasGroup('office_group')"
            @click="deleteClientConfirm = true"
            class="btn flex items-center text-red-600 border border-red-200 hover:bg-red-50"
            title="Удалить клиента"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Вкладки -->
      <div class="border-b mb-6 overflow-x-auto">
        <nav class="flex gap-6 min-w-max">
          <button
            v-for="tab in tabs" :key="tab.key"
            @click="activeTab = tab.key"
            class="pb-3 text-sm font-medium border-b-2 transition-colors"
            :class="activeTab === tab.key
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'"
          >
            {{ tab.label }}
            <span v-if="tab.count !== undefined" class="ml-1 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">{{ tab.count }}</span>
          </button>
        </nav>
      </div>

      <!-- Основное -->
      <div v-if="activeTab === 'main'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card space-y-4">
          <h3 class="font-semibold text-gray-900">Основная информация</h3>
          <div><p class="text-sm text-gray-500">Название</p><p class="text-gray-900">{{ client.name }}</p></div>
          <div v-if="client.inn"><p class="text-sm text-gray-500">ИНН</p><p class="text-gray-900">{{ client.inn }}</p></div>
          <div v-if="client.kpp"><p class="text-sm text-gray-500">КПП</p><p class="text-gray-900">{{ client.kpp }}</p></div>
          <div v-if="client.notes"><p class="text-sm text-gray-500">Заметки</p><p class="text-gray-900 whitespace-pre-wrap">{{ client.notes }}</p></div>
        </div>

        <div class="card space-y-4">
          <h3 class="font-semibold text-gray-900">Юридические реквизиты</h3>
          <div v-if="client.legal">
            <div v-if="client.legal.legal_address"><p class="text-sm text-gray-500">Юр. адрес</p><p class="text-gray-900">{{ client.legal.legal_address }}</p></div>
            <div v-if="client.legal.bank" class="mt-3"><p class="text-sm text-gray-500">Банк</p><p class="text-gray-900">{{ client.legal.bank }}</p></div>
            <div v-if="client.legal.bik" class="mt-3"><p class="text-sm text-gray-500">БИК</p><p class="text-gray-900">{{ client.legal.bik }}</p></div>
            <div v-if="client.legal.account" class="mt-3"><p class="text-sm text-gray-500">Р/С</p><p class="text-gray-900">{{ client.legal.account }}</p></div>
          </div>
          <p v-else class="text-sm text-gray-400">Реквизиты не заполнены</p>
          <button @click="openLegalModal" class="btn btn-secondary text-sm">
            {{ client.legal ? 'Редактировать реквизиты' : 'Добавить реквизиты' }}
          </button>
        </div>
      </div>

      <!-- Контакты -->
      <div v-if="activeTab === 'contacts'">
        <div class="flex justify-end mb-4">
          <button @click="openContactCreate" class="btn btn-primary flex items-center">
            <Plus class="w-4 h-4 mr-2" />Добавить контакт
          </button>
        </div>
        <div v-if="client.contact_persons.length === 0" class="text-center py-12 card">
          <User class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-500">Контактные лица не добавлены</p>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="c in client.contact_persons" :key="c.id" class="card">
            <div class="flex items-start justify-between mb-2">
              <div>
                <p class="font-semibold text-gray-900">{{ c.full_name }}</p>
                <p v-if="c.position" class="text-sm text-gray-500">{{ c.position }}</p>
              </div>
              <span v-if="c.is_primary" class="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">Основной</span>
            </div>
            <div v-if="c.phone" class="flex items-center text-sm text-gray-600 mb-1"><Phone class="w-4 h-4 mr-2" />{{ c.phone }}</div>
            <div v-if="c.email" class="flex items-center text-sm text-gray-600 mb-3"><Mail class="w-4 h-4 mr-2" />{{ c.email }}</div>
            <div class="flex gap-2 border-t pt-3">
              <button @click="openContactEdit(c)" class="flex-1 btn btn-secondary text-sm py-1.5 flex items-center justify-center">
                <Edit class="w-3.5 h-3.5 mr-1" />Изменить
              </button>
              <button @click="contactDeleteConfirm = c" class="btn bg-red-50 text-red-600 hover:bg-red-100 text-sm py-1.5 px-3">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Объекты -->
      <div v-if="activeTab === 'sites'">
        <div class="flex justify-end mb-4">
          <button @click="openSiteCreate" class="btn btn-primary flex items-center">
            <Plus class="w-4 h-4 mr-2" />Добавить объект
          </button>
        </div>
        <div v-if="client.sites.length === 0" class="text-center py-12 card">
          <Building2 class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-500">Объекты не найдены</p>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <router-link
            v-for="s in client.sites" :key="s.id"
            :to="`/sites/${s.id}`"
            class="card hover:shadow-md transition-shadow block"
          >
            <div class="flex items-center mb-2">
              <div class="w-9 h-9 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                <Building2 class="w-4 h-4 text-green-600" />
              </div>
              <div>
                <p class="font-semibold text-gray-900 text-sm">{{ s.title }}</p>
                <p v-if="s.service_frequency" class="text-xs text-gray-500">{{ cfg.serviceFrequencyLabel(s.service_frequency) }}</p>
              </div>
            </div>
            <div class="flex items-start text-sm text-gray-600">
              <MapPin class="w-4 h-4 mr-1.5 mt-0.5 flex-shrink-0" />{{ s.address }}
            </div>
          </router-link>
        </div>
      </div>

      <!-- Договоры -->
      <div v-if="activeTab === 'contracts'">
        <div class="flex justify-end mb-4">
          <button @click="openContractCreate" class="btn btn-primary flex items-center">
            <Plus class="w-4 h-4 mr-2" />Новый договор
          </button>
        </div>
        <div v-if="contractsLoading" class="flex justify-center py-10">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
        <div v-else-if="contracts.length === 0" class="text-center py-12 card">
          <FileText class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-500">Договоры не найдены</p>
        </div>
        <div v-else class="space-y-3">
          <router-link
            v-for="c in contracts" :key="c.id"
            :to="`/contracts/${c.id}`"
            class="card hover:shadow-md transition-shadow block"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FileText class="w-4 h-4 text-blue-600" />
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <p class="font-semibold text-gray-900">{{ c.contract_number || 'Без номера' }}</p>
                    <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="contractStatusClass(c.status)">
                      {{ contractStatusLabel(c.status) }}
                    </span>
                  </div>
                  <p v-if="c.subject" class="text-sm text-gray-500 mt-0.5">{{ c.subject }}</p>
                </div>
              </div>
              <div class="text-right text-sm text-gray-500">
                <p v-if="c.contract_date">{{ formatDate(c.contract_date) }}</p>
                <p class="text-xs text-gray-400 mt-0.5">{{ c.sites_count }} {{ sitesWord(c.sites_count) }}</p>
                <p v-if="c.amount" class="font-medium text-gray-700 mt-1">{{ formatAmount(c.amount) }} ₽</p>
              </div>
            </div>
          </router-link>
        </div>
      </div>

      <!-- Фотографии -->
      <div v-if="activeTab === 'photos'">
        <div v-if="photosLoading && photos.length === 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <div v-for="i in 10" :key="i" class="aspect-square bg-gray-200 rounded-lg animate-pulse" />
        </div>
        <div v-else-if="!photosLoading && photos.length === 0" class="text-center py-16 card">
          <Images class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-500">Фотографий выездов нет</p>
        </div>
        <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <div
            v-for="item in photos" :key="item.id"
            @click="selectedPhoto = item"
            class="group relative aspect-square bg-gray-100 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary-400 transition-all"
          >
            <img :src="item.file_url" :alt="item.file_name || 'Фото'" class="w-full h-full object-cover" loading="lazy" />
            <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-end">
              <div class="p-2 text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity w-full">
                <p v-if="item.site_title" class="truncate font-medium">{{ item.site_title }}</p>
                <p v-if="item.visit_date" class="opacity-80">{{ formatPhotoDate(item.visit_date) }}</p>
              </div>
            </div>
          </div>
        </div>
        <div v-if="photos.length < photosTotal" class="mt-6 flex justify-center">
          <button @click="loadPhotos(false)" :disabled="photosLoading" class="btn btn-secondary disabled:opacity-50">
            {{ photosLoading ? 'Загрузка...' : `Показать ещё (${photosTotal - photos.length})` }}
          </button>
        </div>
      </div>

      <!-- Файлы -->
      <div v-if="activeTab === 'files'">
        <AttachmentsTab entity-type="client" :entity-id="client.id" />
      </div>

      <!-- История выездов -->
      <div v-if="activeTab === 'visits'">
        <div class="flex justify-end mb-4">
          <button @click="openHistoricalVisitModal" class="btn btn-secondary flex items-center text-sm">
            <Plus class="w-4 h-4 mr-2" />Внести исторический
          </button>
        </div>
        <div v-if="client.recent_visits.length === 0" class="text-center py-12 card">
          <Calendar class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-500">Выездов не найдено</p>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="v in client.recent_visits"
            :key="v.id"
            class="card cursor-pointer hover:shadow-md transition-shadow"
            @click="openVisitDetail(v)"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3 flex-wrap">
                <p class="font-medium text-gray-900">{{ v.site_title }}</p>
                <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="statusClass(v.status)">
                  {{ cfg.visitStatusLabel(v.status) }}
                </span>
                <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="priorityClass(v.priority)">
                  {{ cfg.priorityLabel(v.priority) }}
                </span>
              </div>
              <div class="flex items-center gap-3 text-sm text-gray-500 flex-shrink-0">
                <span>{{ formatDate(v.planned_date) }}</span>
                <span v-if="v.master_name">{{ v.master_name }}</span>
                <button
                  v-if="auth.hasGroup('admin_group') || auth.hasGroup('office_group')"
                  @click.stop="visitDeleteConfirm = v"
                  class="p-1 text-gray-400 hover:text-red-600 transition-colors"
                  title="Удалить выезд"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Photo Modal -->
    <div v-if="selectedPhoto" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80" @click.self="selectedPhoto = null">
      <div class="relative max-w-4xl w-full mx-4 flex flex-col md:flex-row bg-white rounded-xl overflow-hidden shadow-2xl max-h-[90vh]">
        <button @click="selectedPhoto = null" class="absolute top-3 right-3 z-10 w-8 h-8 flex items-center justify-center rounded-full bg-black bg-opacity-40 text-white hover:bg-opacity-60">
          <X class="w-4 h-4" />
        </button>
        <div class="flex-1 bg-black flex items-center justify-center min-h-48">
          <img :src="selectedPhoto.file_url" :alt="selectedPhoto.file_name || 'Фото'" class="max-h-[60vh] md:max-h-[80vh] max-w-full object-contain" />
        </div>
        <div class="w-full md:w-64 flex-shrink-0 p-5 flex flex-col gap-3 overflow-y-auto">
          <div v-if="selectedPhoto.visit_date" class="flex items-start gap-3">
            <Calendar class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div><p class="text-xs text-gray-500">Дата выезда</p><p class="text-sm font-medium">{{ formatPhotoDate(selectedPhoto.visit_date) }}</p></div>
          </div>
          <div v-if="selectedPhoto.site_title" class="flex items-start gap-3">
            <Building2 class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div><p class="text-xs text-gray-500">Объект</p><p class="text-sm font-medium">{{ selectedPhoto.site_title }}</p></div>
          </div>
          <div class="mt-auto pt-4 border-t flex flex-col gap-2">
            <router-link v-if="selectedPhoto.visit_id" :to="`/visits?open_visit=${selectedPhoto.visit_id}`" @click="selectedPhoto = null" class="w-full text-center px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700">
              Перейти к выезду
            </router-link>
            <a :href="selectedPhoto.file_url" target="_blank" rel="noopener" class="w-full text-center px-4 py-2 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50">
              Открыть оригинал
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Client Modal -->
    <div v-if="editModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 md:p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">Редактировать клиента</h2>
          <button @click="editModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleEditSave" class="p-4 md:p-6 space-y-4">
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Название *</label><input v-model="editForm.name" required class="input" /></div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div><label class="block text-sm font-medium text-gray-700 mb-1">ИНН</label><input v-model="editForm.inn" class="input" /></div>
            <div><label class="block text-sm font-medium text-gray-700 mb-1">КПП</label><input v-model="editForm.kpp" class="input" /></div>
          </div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label><textarea v-model="editForm.notes" class="input" rows="3" /></div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="editModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Legal Modal -->
    <div v-if="legalModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 md:p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">Юридические реквизиты</h2>
          <button @click="legalModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleLegalSave" class="p-4 md:p-6 space-y-4">
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Юридический адрес</label><textarea v-model="legalForm.legal_address" class="input" rows="2" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Банк</label><input v-model="legalForm.bank" class="input" placeholder="ПАО Сбербанк" /></div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div><label class="block text-sm font-medium text-gray-700 mb-1">БИК</label><input v-model="legalForm.bik" class="input" placeholder="044525225" /></div>
            <div><label class="block text-sm font-medium text-gray-700 mb-1">Расчётный счёт</label><input v-model="legalForm.account" class="input" placeholder="40702810..." /></div>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="legalModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Contact Create/Edit Modal -->
    <div v-if="contactModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 md:p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">{{ editingContact ? 'Редактировать контакт' : 'Добавить контакт' }}</h2>
          <button @click="contactModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleContactSave" class="p-4 md:p-6 space-y-4">
          <div><label class="block text-sm font-medium text-gray-700 mb-1">ФИО *</label><input v-model="contactForm.full_name" required class="input" placeholder="Иванов Иван Иванович" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Должность</label><input v-model="contactForm.position" class="input" placeholder="Директор" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Телефон</label><input v-model="contactForm.phone" class="input" placeholder="+7-900-000-00-00" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Email</label><input v-model="contactForm.email" type="email" class="input" placeholder="ivan@company.ru" /></div>
          <label class="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
            <input type="checkbox" v-model="contactForm.is_primary" class="rounded" />
            Основной контакт
          </label>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="contactModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">{{ saving ? 'Сохранение...' : (editingContact ? 'Сохранить' : 'Добавить') }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Site Create Modal -->
    <div v-if="siteModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 md:p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">Добавить объект</h2>
          <button @click="siteModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleSiteCreate" class="p-4 md:p-6 space-y-4">
          <div class="text-sm text-gray-500 bg-gray-50 rounded p-3">
            Клиент: <span class="font-medium text-gray-900">{{ client.name }}</span>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
            <input v-model="siteForm.title" class="input" :class="{ 'border-red-400': siteErrors.title }" placeholder="Котельная №1" @input="delete siteErrors.title" />
            <p v-if="siteErrors.title" class="text-red-600 text-xs mt-1">{{ siteErrors.title }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Адрес *</label>
            <input v-model="siteForm.address" class="input" :class="{ 'border-red-400': siteErrors.address }" placeholder="г. Москва, ул. Ленина, д. 1" @input="delete siteErrors.address" />
            <p v-if="siteErrors.address" class="text-red-600 text-xs mt-1">{{ siteErrors.address }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Частота обслуживания</label>
            <select v-model="siteForm.service_frequency" class="input">
              <option value="">Не указано</option>
              <option v-for="f in cfg.serviceFrequencies" :key="f.sysname" :value="f.sysname">{{ f.display_name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Контакт на месте</label>
            <input v-model="siteForm.onsite_contact" class="input" placeholder="Иванов И.И., тел. 8-999-000-00-00" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Доступ</label>
            <textarea v-model="siteForm.access_notes" class="input" rows="2" placeholder="Ключ у охранника..." />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="siteModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="siteSaving" class="btn btn-primary disabled:opacity-50">
              {{ siteSaving ? 'Сохранение...' : 'Создать объект' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Contract Create Modal -->
    <div v-if="contractCreateModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
        <div class="flex items-center justify-between p-4 md:p-6 border-b flex-shrink-0">
          <h2 class="text-xl font-semibold text-gray-900">Новый договор</h2>
          <button @click="contractCreateModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleContractCreate" class="p-4 md:p-6 space-y-4 overflow-y-auto flex-1">
          <div class="text-sm text-gray-500 bg-gray-50 rounded p-3">
            Клиент: <span class="font-medium text-gray-900">{{ client.name }}</span>
          </div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Номер договора</label><input v-model="contractForm.contract_number" class="input" placeholder="0817/2 от 17.08.2006" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Дата договора</label><input v-model="contractForm.contract_date" type="date" class="input" /></div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Предмет договора</label><input v-model="contractForm.subject" class="input" placeholder="ТО газового оборудования" /></div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div><label class="block text-sm font-medium text-gray-700 mb-1">Сумма договора</label><input v-model="contractForm.amount" type="number" step="0.01" class="input" /></div>
            <div><label class="block text-sm font-medium text-gray-700 mb-1">Сумма акта</label><input v-model="contractForm.act_amount" type="number" step="0.01" class="input" /></div>
          </div>
          <div><label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label><textarea v-model="contractForm.notes" class="input" rows="2" /></div>

          <!-- Расписание -->
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <button
              type="button"
              @click="contractScheduleEnabled = !contractScheduleEnabled"
              class="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              :class="contractScheduleEnabled ? 'bg-blue-50 text-blue-700 hover:bg-blue-50' : ''"
            >
              <span class="flex items-center gap-2">
                <CalendarDays class="w-4 h-4" />
                Добавить в расписание
              </span>
              <span class="text-xs px-2 py-0.5 rounded-full" :class="contractScheduleEnabled ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'">
                {{ contractScheduleEnabled ? 'Включено' : 'Выключено' }}
              </span>
            </button>
            <div v-if="contractScheduleEnabled" class="px-4 pb-4 pt-3 space-y-3 border-t border-gray-100">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Год</label>
                <select v-model="contractScheduleYear" class="input text-sm">
                  <option v-for="y in SCHEDULE_YEARS" :key="y" :value="y">{{ y }}</option>
                </select>
              </div>
              <div>
                <div class="flex items-center justify-between mb-2">
                  <label class="text-xs font-medium text-gray-600">Месяцы</label>
                  <div class="flex gap-2 text-xs text-blue-600">
                    <button type="button" @click="contractScheduleMonths = [1,2,3,4,5,6,7,8,9,10,11,12]" class="hover:underline">Все</button>
                    <span class="text-gray-300">|</span>
                    <button type="button" @click="contractScheduleMonths = []" class="hover:underline">Сбросить</button>
                  </div>
                </div>
                <div class="grid grid-cols-3 gap-1.5">
                  <label
                    v-for="(name, idx) in MONTH_NAMES"
                    :key="idx + 1"
                    class="flex items-center gap-2 px-2.5 py-1.5 rounded-md border cursor-pointer text-sm transition-colors"
                    :class="contractScheduleMonths.includes(idx + 1)
                      ? 'bg-blue-50 border-blue-300 text-blue-700'
                      : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
                  >
                    <input type="checkbox" :value="idx + 1" v-model="contractScheduleMonths" class="rounded border-gray-300 text-blue-600 w-3.5 h-3.5" />
                    {{ name }}
                  </label>
                </div>
                <p v-if="contractScheduleMonths.length" class="text-xs text-gray-500 mt-1.5">Выбрано: {{ contractScheduleMonths.length }} мес.</p>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Заметка для всех месяцев (необязательно)</label>
                <textarea v-model="contractScheduleNote" class="input text-sm" rows="2" placeholder="ТО, осмотр, плановый визит..." />
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="contractCreateModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="contractSaving" class="btn btn-primary disabled:opacity-50">{{ contractSaving ? 'Сохранение...' : 'Создать' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Client Confirm -->
    <div v-if="deleteClientConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4">
        <h3 class="text-lg font-semibold mb-2 text-red-700">Удалить клиента?</h3>
        <p class="text-sm text-gray-600 mb-1">Клиент <strong>{{ client.name }}</strong> будет удалён безвозвратно.</p>
        <p class="text-xs text-gray-400 mb-5">Все связанные данные (объекты, договоры, выезды) также будут удалены.</p>
        <div class="flex gap-3">
          <button @click="handleDeleteClient" :disabled="deletingClient" class="btn bg-red-600 text-white hover:bg-red-700 flex-1 disabled:opacity-50">
            {{ deletingClient ? 'Удаление...' : 'Удалить' }}
          </button>
          <button @click="deleteClientConfirm = false" class="btn btn-secondary flex-1">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Contact Delete Confirm -->
    <div v-if="contactDeleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-4 md:p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Удалить контакт?</h2>
        <p class="text-gray-600 mb-6">Контакт <strong>{{ contactDeleteConfirm.full_name }}</strong> будет удалён.</p>
        <div class="flex justify-end gap-3">
          <button @click="contactDeleteConfirm = null" class="btn btn-secondary">Отмена</button>
          <button @click="handleContactDelete" class="btn bg-red-600 text-white hover:bg-red-700">Удалить</button>
        </div>
      </div>
    </div>

    <!-- Historical Visit Modal -->
    <div v-if="historicalVisitModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 md:p-6 border-b">
          <h2 class="text-xl font-semibold text-gray-900">Внести исторический выезд</h2>
          <button @click="historicalVisitModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <form @submit.prevent="handleHistoricalVisitSave" class="p-4 md:p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Дата выезда *</label>
            <input v-model="historicalVisitForm.planned_date" type="date" required class="input" :class="{ 'border-red-400': historicalVisitErrors.planned_date }" @change="delete historicalVisitErrors.planned_date" />
            <p v-if="historicalVisitErrors.planned_date" class="text-red-600 text-xs mt-1">{{ historicalVisitErrors.planned_date }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Договор</label>
            <select v-model="historicalVisitForm.contract_id" class="input" @change="onHistoricalContractChange">
              <option value="">— Без договора (все объекты) —</option>
              <option v-for="c in contracts" :key="c.id" :value="c.id">
                {{ c.contract_number || 'Без номера' }}{{ c.contract_date ? ' от ' + formatDate(c.contract_date) : '' }}{{ c.subject ? ' — ' + c.subject : '' }}
              </option>
            </select>
            <p v-if="historicalVisitSitesLoading" class="text-xs text-gray-400 mt-1">Загрузка объектов...</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Объект *</label>
            <select v-model="historicalVisitForm.site_id" required class="input" :class="{ 'border-red-400': historicalVisitErrors.site_id }" @change="delete historicalVisitErrors.site_id">
              <option value="">— Выберите объект —</option>
              <option v-for="s in historicalVisitSites" :key="s.id" :value="s.id">{{ s.title }}</option>
            </select>
            <p v-if="historicalVisitErrors.site_id" class="text-red-600 text-xs mt-1">{{ historicalVisitErrors.site_id }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Мастера *</label>
            <div
              class="border rounded-lg max-h-36 overflow-y-auto divide-y divide-gray-100"
              :class="historicalVisitErrors.master_ids ? 'border-red-400' : 'border-gray-200'"
            >
              <label
                v-for="u in masters"
                :key="u.id"
                class="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-gray-50"
              >
                <input type="checkbox" :value="u.id" v-model="historicalVisitForm.master_ids" class="rounded flex-shrink-0" @change="delete historicalVisitErrors.master_ids" />
                <span class="text-sm text-gray-900">{{ u.full_name || u.username }}</span>
              </label>
              <div v-if="!masters.length" class="px-3 py-2 text-sm text-gray-400">Нет мастеров</div>
            </div>
            <p v-if="historicalVisitErrors.master_ids" class="text-red-600 text-xs mt-1">{{ historicalVisitErrors.master_ids }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Тип(ы) выезда</label>
            <div class="border border-gray-200 rounded-lg divide-y divide-gray-100">
              <label
                v-for="vt in cfg.visitTypes"
                :key="vt.sysname"
                class="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-gray-50"
              >
                <input type="checkbox" :value="vt.sysname" v-model="historicalVisitForm.visit_types" class="rounded flex-shrink-0" />
                <span class="text-sm text-gray-900">{{ vt.display_name }}</span>
              </label>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Итог работы</label>
            <textarea v-model="historicalVisitForm.work_summary" class="input" rows="3" placeholder="Описание выполненных работ..." />
          </div>
          <label class="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
            <input type="checkbox" v-model="historicalVisitForm.defects_present" class="rounded" />
            Обнаружены дефекты
          </label>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="historicalVisitModalOpen = false" class="btn btn-secondary">Отмена</button>
            <button type="submit" :disabled="historicalVisitSaving" class="btn btn-primary disabled:opacity-50">
              {{ historicalVisitSaving ? 'Сохранение...' : 'Внести выезд' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Visit Detail Modal -->
    <div v-if="detailVisit" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 flex flex-col max-h-[90vh]">
        <div class="flex items-center justify-between p-4 md:p-6 border-b flex-shrink-0">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">{{ detailVisit.site_title }}</h2>
            <p class="text-sm text-gray-500 mt-0.5">{{ formatDate(detailVisit.planned_date) }}</p>
          </div>
          <button @click="detailVisit = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
        </div>
        <div class="flex border-b flex-shrink-0">
          <button @click="detailTab = 'info'" class="flex-1 py-2.5 text-sm font-medium transition-colors"
            :class="detailTab === 'info' ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500 hover:text-gray-700'">Информация</button>
          <button @click="detailTab = 'files'" class="flex-1 py-2.5 text-sm font-medium transition-colors"
            :class="detailTab === 'files' ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500 hover:text-gray-700'">Файлы и фото</button>
        </div>
        <div class="overflow-y-auto flex-1">
          <div v-if="detailTab === 'info'" class="p-4 md:p-6 space-y-4">
            <div class="flex gap-2 flex-wrap">
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="statusClass(detailVisit.status)">{{ cfg.visitStatusLabel(detailVisit.status) }}</span>
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">{{ cfg.visitTypeLabel(detailVisit.visit_type) }}</span>
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="priorityClass(detailVisit.priority)">{{ cfg.priorityLabel(detailVisit.priority) }}</span>
            </div>
            <div><p class="text-sm text-gray-500">Объект</p><p class="text-gray-900">{{ detailVisit.site_title }}</p></div>
            <div v-if="detailVisit.site_address"><p class="text-sm text-gray-500">Адрес</p><p class="text-gray-900">{{ detailVisit.site_address }}</p></div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div><p class="text-sm text-gray-500">Дата</p><p class="text-gray-900">{{ formatDate(detailVisit.planned_date) }}</p></div>
              <div><p class="text-sm text-gray-500">Время</p><p class="text-gray-900">{{ detailVisit.planned_time_from?.slice(0,5) || '—' }} — {{ detailVisit.planned_time_to?.slice(0,5) || '—' }}</p></div>
            </div>
            <div><p class="text-sm text-gray-500">Мастер</p><p class="text-gray-900">{{ detailVisit.master_name || 'Не назначен' }}</p></div>
            <div v-if="detailVisit.office_notes" class="bg-primary-50 rounded p-3">
              <p class="text-xs font-medium text-primary-700 mb-1">Заметка офиса</p>
              <p class="text-primary-900">{{ detailVisit.office_notes }}</p>
            </div>
            <template v-if="detailVisit.work_summary">
              <div class="border-t pt-3">
                <p class="text-sm text-gray-500 mb-1">Итог работ</p>
                <p class="text-gray-900 whitespace-pre-wrap">{{ detailVisit.work_summary }}</p>
              </div>
              <div v-if="detailVisit.defects_present" class="text-orange-700 bg-orange-50 rounded p-2 text-xs">
                ⚠ Обнаружены дефекты<span v-if="detailVisit.defects_summary">: {{ detailVisit.defects_summary }}</span>
              </div>
              <div v-if="detailVisit.recommendations">
                <p class="text-sm text-gray-500">Рекомендации</p>
                <p class="text-gray-900">{{ detailVisit.recommendations }}</p>
              </div>
            </template>
          </div>
          <div v-else class="p-4 md:p-6">
            <AttachmentsTab entity-type="visit" :entity-id="detailVisit.id" />
          </div>
        </div>
        <div class="flex justify-between p-4 md:p-6 border-t flex-shrink-0">
          <button
            v-if="auth.hasGroup('admin_group') || auth.hasGroup('office_group')"
            @click="visitDeleteConfirm = detailVisit; detailVisit = null"
            class="btn bg-red-50 text-red-600 hover:bg-red-100 flex items-center gap-1.5"
          >
            <Trash2 class="w-4 h-4" />Удалить
          </button>
          <button @click="detailVisit = null" class="btn btn-primary ml-auto">Закрыть</button>
        </div>
      </div>
    </div>

    <!-- Visit Delete Confirm -->
    <div v-if="visitDeleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-4 md:p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-2">Удалить выезд?</h2>
        <p class="text-gray-600 mb-1">
          <span class="font-medium">{{ visitDeleteConfirm.site_title }}</span>
        </p>
        <p class="text-gray-500 text-sm mb-6">{{ formatDate(visitDeleteConfirm.planned_date) }}<span v-if="visitDeleteConfirm.master_name"> · {{ visitDeleteConfirm.master_name }}</span></p>
        <p class="text-red-600 text-sm mb-6">Это действие нельзя отменить.</p>
        <div class="flex justify-end gap-3">
          <button @click="visitDeleteConfirm = null" class="btn btn-secondary">Отмена</button>
          <button @click="handleVisitDelete" :disabled="visitDeleting" class="btn bg-red-600 text-white hover:bg-red-700 disabled:opacity-50">
            {{ visitDeleting ? 'Удаление...' : 'Удалить' }}
          </button>
        </div>
      </div>
    </div>

  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Edit, Plus, X, Phone, Mail, Building2, MapPin, Calendar, User, Trash2, FileText, Images, Clock, CalendarDays } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import AttachmentsTab from '../components/AttachmentsTab.vue'
import { useConfigStore } from '../stores/config.js'
import { useAuthStore } from '../stores/auth.js'
import { clientsAPI, sitesAPI, contractsAPI, visitsAPI, usersAPI, attachmentsAPI, scheduleAPI } from '../services/api.js'
import { useEscClose } from '../composables/useEscClose.js'

const route = useRoute()
const router = useRouter()
const cfg = useConfigStore()
const auth = useAuthStore()

const client = ref(null)
const loading = ref(true)
const activeTab = ref('main')
const saving = ref(false)
const toggling = ref(false)

const canManage = auth.hasGroup('admin_group') || auth.hasGroup('office_group')

// Edit client
const editModalOpen = ref(false)
const editForm = ref({})
const originalEditForm = ref(null)

// Legal
const legalModalOpen = ref(false)
const legalForm = ref({ legal_address: '', bank: '', bik: '', account: '' })

// Site create
const siteModalOpen = ref(false)
const siteSaving = ref(false)
const siteForm = ref({ title: '', address: '', service_frequency: 'monthly', onsite_contact: '', access_notes: '' })
const siteErrors = ref({})

// Contracts
const contracts = ref([])
const contractsLoading = ref(false)
const contractCreateModalOpen = ref(false)
const contractForm = ref({ contract_number: '', contract_date: '', subject: '', amount: '', act_amount: '', notes: '' })
const contractSaving = ref(false)

// Удаление клиента
const deleteClientConfirm = ref(false)
const deletingClient = ref(false)

async function handleDeleteClient() {
  deletingClient.value = true
  try {
    await clientsAPI.delete(client.value.id)
    router.push('/clients')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    deletingClient.value = false
  }
}

// Schedule при создании договора
const contractScheduleEnabled = ref(false)
const contractScheduleYear = ref(new Date().getFullYear())
const contractScheduleMonths = ref([])
const contractScheduleNote = ref('')
const MONTH_NAMES = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
const SCHEDULE_YEARS = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() + i)

// Photos tab
const photos = ref([])
const photosTotal = ref(0)
const photosLoading = ref(false)
const selectedPhoto = ref(null)
const PHOTOS_LIMIT = 20

async function loadPhotos(reset = false) {
  if (photosLoading.value) return
  photosLoading.value = true
  try {
    const offset = reset ? 0 : photos.value.length
    const res = await attachmentsAPI.getGallery({ client_id: client.value.id, limit: PHOTOS_LIMIT, offset })
    if (reset) photos.value = res.data.items
    else photos.value.push(...res.data.items)
    photosTotal.value = res.data.total
  } catch { /* ignore */ } finally { photosLoading.value = false }
}

function formatPhotoDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

// Visit detail
const detailVisit = ref(null)
const detailTab = ref('info')

async function openVisitDetail(v) {
  detailTab.value = 'info'
  try {
    const res = await visitsAPI.getById(v.id)
    detailVisit.value = res.data
  } catch {
    detailVisit.value = v
  }
}

// Historical visit
const historicalVisitModalOpen = ref(false)
const historicalVisitSaving = ref(false)
const historicalVisitSitesLoading = ref(false)
const historicalVisitForm = ref({
  planned_date: '',
  contract_id: '',
  site_id: '',
  master_ids: [],
  visit_types: ['maintenance'],
  work_summary: '',
  defects_present: false,
})
const historicalVisitErrors = ref({})
const historicalVisitSites = ref([])  // объекты для выбора (всё или по договору)
const masters = ref([])

function openHistoricalVisitModal() {
  // Если 1 договор — подставляем автоматически
  const autoContract = contracts.value.length === 1 ? contracts.value[0].id : ''
  historicalVisitForm.value = {
    planned_date: '',
    contract_id: autoContract,
    site_id: '',
    master_ids: [],
    visit_types: ['maintenance'],
    work_summary: '',
    defects_present: false,
  }
  historicalVisitErrors.value = {}
  historicalVisitSites.value = client.value?.sites || []
  historicalVisitModalOpen.value = true
  // Если автоматически подставили договор — загрузим его объекты
  if (autoContract) loadContractSites(autoContract)
}

async function onHistoricalContractChange() {
  historicalVisitForm.value.site_id = ''
  delete historicalVisitErrors.value.site_id
  const cid = historicalVisitForm.value.contract_id
  if (!cid) {
    historicalVisitSites.value = client.value?.sites || []
    return
  }
  await loadContractSites(cid)
}

async function loadContractSites(contractId) {
  historicalVisitSitesLoading.value = true
  try {
    const res = await contractsAPI.getById(contractId)
    historicalVisitSites.value = res.data.sites || []
  } catch {
    historicalVisitSites.value = client.value?.sites || []
  } finally {
    historicalVisitSitesLoading.value = false
  }
}

async function handleHistoricalVisitSave() {
  const e = {}
  if (!historicalVisitForm.value.planned_date) e.planned_date = 'Укажите дату'
  if (!historicalVisitForm.value.site_id) e.site_id = 'Выберите объект'
  if (!historicalVisitForm.value.master_ids.length) e.master_ids = 'Выберите хотя бы одного мастера'
  historicalVisitErrors.value = e
  if (Object.keys(e).length) return
  historicalVisitSaving.value = true
  const visitTypes = historicalVisitForm.value.visit_types.length ? historicalVisitForm.value.visit_types : ['maintenance']
  try {
    await visitsAPI.create({
      planned_date: historicalVisitForm.value.planned_date,
      site_id: historicalVisitForm.value.site_id,
      master_ids: historicalVisitForm.value.master_ids,
      visit_types: visitTypes,
      visit_type: visitTypes[0],
      contract_id: historicalVisitForm.value.contract_id || null,
      status: 'done',
      work_summary: historicalVisitForm.value.work_summary || null,
      defects_present: historicalVisitForm.value.defects_present,
      priority: 'medium',
    })
    historicalVisitModalOpen.value = false
    await loadClient()
  } catch (err) {
    alert('Ошибка: ' + (err.response?.data?.detail || err.message))
  } finally {
    historicalVisitSaving.value = false
  }
}

// Visit delete
const visitDeleteConfirm = ref(null)
const visitDeleting = ref(false)

async function handleVisitDelete() {
  visitDeleting.value = true
  try {
    await visitsAPI.delete(visitDeleteConfirm.value.id)
    visitDeleteConfirm.value = null
    await loadClient()
  } catch (err) {
    alert('Ошибка: ' + (err.response?.data?.detail || err.message))
  } finally {
    visitDeleting.value = false
  }
}

// Contacts
const contactModalOpen = ref(false)
const editingContact = ref(null)
const contactDeleteConfirm = ref(null)
const contactForm = ref({ full_name: '', position: '', phone: '', email: '', is_primary: false })

useEscClose([
  { isOpen: () => deleteClientConfirm.value,           close: () => { deleteClientConfirm.value = false } },
  { isOpen: () => editModalOpen.value,                 close: () => { editModalOpen.value = false } },
  { isOpen: () => legalModalOpen.value,                close: () => { legalModalOpen.value = false } },
  { isOpen: () => siteModalOpen.value,                 close: () => { siteModalOpen.value = false } },
  { isOpen: () => contractCreateModalOpen.value,       close: () => { contractCreateModalOpen.value = false } },
  { isOpen: () => contactModalOpen.value,              close: () => { contactModalOpen.value = false } },
  { isOpen: () => !!contactDeleteConfirm.value,        close: () => { contactDeleteConfirm.value = null } },
  { isOpen: () => historicalVisitModalOpen.value,      close: () => { historicalVisitModalOpen.value = false } },
  { isOpen: () => !!detailVisit.value,                 close: () => { detailVisit.value = null } },
  { isOpen: () => !!visitDeleteConfirm.value,          close: () => { visitDeleteConfirm.value = null } },
])

const tabs = computed(() => [
  { key: 'main', label: 'Основное' },
  { key: 'contacts', label: 'Контакты', count: client.value?.contact_persons?.length ?? 0 },
  { key: 'sites', label: 'Объекты', count: client.value?.sites?.length ?? 0 },
  { key: 'contracts', label: 'Договоры', count: contracts.value?.length ?? 0 },
  { key: 'visits', label: 'История выездов', count: client.value?.recent_visits?.length ?? 0 },
  { key: 'photos', label: 'Фотографии' },
  { key: 'files', label: 'Файлы' },
])

async function loadClient() {
  loading.value = true
  try {
    const res = await clientsAPI.getById(route.params.id)
    client.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadContracts() {
  contractsLoading.value = true
  try {
    const res = await contractsAPI.getByClient(route.params.id)
    contracts.value = res.data
  } finally {
    contractsLoading.value = false
  }
}

function openContractCreate() {
  contractForm.value = { contract_number: '', contract_date: '', subject: '', amount: '', act_amount: '', notes: '' }
  contractScheduleEnabled.value = false
  contractScheduleYear.value = new Date().getFullYear()
  contractScheduleMonths.value = []
  contractScheduleNote.value = ''
  contractCreateModalOpen.value = true
}

async function handleContractCreate() {
  contractSaving.value = true
  try {
    const payload = { ...contractForm.value, client_id: client.value.id }
    if (!payload.contract_date) delete payload.contract_date
    if (!payload.amount) delete payload.amount
    if (!payload.act_amount) delete payload.act_amount
    const res = await contractsAPI.create(payload)
    const newId = res.data.id
    if (contractScheduleEnabled.value && contractScheduleMonths.value.length) {
      const note = contractScheduleNote.value.trim() || null
      for (const month of contractScheduleMonths.value) {
        await scheduleAPI.upsertCell(newId, contractScheduleYear.value, month, note)
      }
    }
    contractCreateModalOpen.value = false
    await loadContracts()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    contractSaving.value = false
  }
}

function contractStatusClass(s) {
  const m = { active: 'bg-green-100 text-green-700', closed: 'bg-gray-200 text-gray-600', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-600'
}
function contractStatusLabel(s) {
  const m = { active: 'Активен', closed: 'Закрыт', cancelled: 'Отменён' }
  return m[s] || s
}
function sitesWord(n) {
  if (n % 10 === 1 && n % 100 !== 11) return 'объект'
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return 'объекта'
  return 'объектов'
}
function formatAmount(v) { return Number(v).toLocaleString('ru-RU') }

async function toggleActive() {
  toggling.value = true
  try {
    await clientsAPI.update(client.value.id, { is_active: !client.value.is_active })
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    toggling.value = false
  }
}

async function handleUnarchive() {
  toggling.value = true
  try {
    await clientsAPI.unarchive(client.value.id)
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    toggling.value = false
  }
}

function openEdit() {
  editForm.value = {
    name: client.value.name,
    inn: client.value.inn || '',
    kpp: client.value.kpp || '',
    notes: client.value.notes || '',
  }
  originalEditForm.value = { ...editForm.value }
  editModalOpen.value = true
}

async function handleEditSave() {
  if (JSON.stringify(editForm.value) === JSON.stringify(originalEditForm.value)) {
    editModalOpen.value = false
    return
  }
  saving.value = true
  try {
    await clientsAPI.update(client.value.id, editForm.value)
    editModalOpen.value = false
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function openLegalModal() {
  legalForm.value = {
    legal_address: client.value.legal?.legal_address || '',
    bank: client.value.legal?.bank || '',
    bik: client.value.legal?.bik || '',
    account: client.value.legal?.account || '',
  }
  legalModalOpen.value = true
}

async function handleLegalSave() {
  saving.value = true
  try {
    await clientsAPI.upsertLegal(client.value.id, legalForm.value)
    legalModalOpen.value = false
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function openSiteCreate() {
  siteForm.value = { title: '', address: '', service_frequency: 'monthly', onsite_contact: '', access_notes: '' }
  siteErrors.value = {}
  siteModalOpen.value = true
}

async function handleSiteCreate() {
  const e = {}
  if (!siteForm.value.title.trim()) e.title = 'Введите название'
  if (!siteForm.value.address.trim()) e.address = 'Введите адрес'
  siteErrors.value = e
  if (Object.keys(e).length) return
  siteSaving.value = true
  try {
    await sitesAPI.create({
      title: siteForm.value.title.trim(),
      address: siteForm.value.address.trim(),
      client_id: client.value.id,
      service_frequency: siteForm.value.service_frequency || null,
      onsite_contact: siteForm.value.onsite_contact || null,
      access_notes: siteForm.value.access_notes || null,
    })
    siteModalOpen.value = false
    await loadClient()
  } catch (err) {
    alert('Ошибка: ' + (err.response?.data?.detail || err.message))
  } finally {
    siteSaving.value = false
  }
}

function openContactCreate() {
  editingContact.value = null
  contactForm.value = { full_name: '', position: '', phone: '', email: '', is_primary: false }
  contactModalOpen.value = true
}

function openContactEdit(c) {
  editingContact.value = c
  contactForm.value = { full_name: c.full_name, position: c.position || '', phone: c.phone || '', email: c.email || '', is_primary: c.is_primary }
  contactModalOpen.value = true
}

async function handleContactSave() {
  saving.value = true
  try {
    if (editingContact.value) {
      await clientsAPI.updateContact(client.value.id, editingContact.value.id, contactForm.value)
    } else {
      await clientsAPI.addContact(client.value.id, contactForm.value)
    }
    contactModalOpen.value = false
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleContactDelete() {
  try {
    await clientsAPI.deleteContact(client.value.id, contactDeleteConfirm.value.id)
    contactDeleteConfirm.value = null
    await loadClient()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

function statusClass(s) {
  const m = { planned: 'bg-blue-100 text-blue-700', in_progress: 'bg-green-100 text-green-700', done: 'bg-gray-400 text-white', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-700'
}
function priorityClass(p) {
  const m = { low: 'bg-gray-100 text-gray-600', medium: 'bg-yellow-100 text-yellow-700', high: 'bg-orange-100 text-orange-700', urgent: 'bg-red-100 text-red-700' }
  return m[p] || 'bg-gray-100 text-gray-700'
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }

async function initPage() {
  if (route.query.tab) activeTab.value = route.query.tab
  loadClient(); loadContracts()
  try {
    const res = await usersAPI.getMasters()
    masters.value = res.data
  } catch { /* ignore */ }
}

onMounted(initPage)

watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) initPage()
})

watch(activeTab, (tab) => {
  if (tab === 'photos' && photos.value.length === 0) loadPhotos(true)
})
</script>
