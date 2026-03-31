<template>
  <Layout>
    <div>
      <div class="flex items-center justify-between flex-wrap gap-y-3 mb-6">
        <div>
          <h1 class="text-xl md:text-3xl font-bold text-gray-900">Выезды</h1>
          <p class="text-gray-600 mt-1">Всего: {{ total }}</p>
        </div>
        <button @click="openCreate" class="btn btn-primary flex items-center">
          <Plus class="w-5 h-5 mr-2" />Создать выезд
        </button>
      </div>

      <!-- Filters -->
      <div class="card mb-4">
        <button class="md:hidden w-full flex items-center justify-between text-sm font-medium text-gray-700 mb-2" @click="filtersOpen = !filtersOpen">
          <span class="flex items-center gap-2"><Filter class="w-4 h-4" />Фильтры<span v-if="hasActiveFilters" class="w-2 h-2 bg-primary-500 rounded-full inline-block"></span></span>
          <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="filtersOpen ? 'rotate-180' : ''" />
        </button>
        <div :class="filtersOpen ? 'flex' : 'hidden md:flex'" class="flex-wrap gap-3 items-end">
          <!-- Статус -->
          <div class="min-w-[150px]">
            <label class="block text-xs text-gray-400 mb-1">Статус</label>
            <select v-model="filters.status" class="input text-sm">
              <option value="">Все статусы</option>
              <option v-for="s in cfg.visitStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
            </select>
          </div>
          <!-- Приоритет -->
          <div class="min-w-[140px]">
            <label class="block text-xs text-gray-400 mb-1">Приоритет</label>
            <select v-model="filters.priority" class="input text-sm">
              <option value="">Все приоритеты</option>
              <option v-for="p in cfg.priorities" :key="p.sysname" :value="p.sysname">{{ p.display_name }}</option>
            </select>
          </div>
          <!-- Мастер -->
          <div class="min-w-[160px]">
            <label class="block text-xs text-gray-400 mb-1">Мастер</label>
            <select v-model="filters.master_id" class="input text-sm">
              <option value="">Все мастера</option>
              <option v-for="m in masters" :key="m.id" :value="m.id">{{ m.full_name }}</option>
            </select>
          </div>
          <!-- Дата с -->
          <div>
            <label class="block text-xs text-gray-400 mb-1">Дата с</label>
            <input v-model="filters.date_from" type="date" class="input text-sm" />
          </div>
          <!-- Дата по -->
          <div>
            <label class="block text-xs text-gray-400 mb-1">Дата по</label>
            <input v-model="filters.date_to" type="date" class="input text-sm" />
          </div>
          <!-- Архивные -->
          <label v-if="auth.hasGroup('admin_group')" class="flex items-center gap-2 cursor-pointer text-sm text-gray-600 whitespace-nowrap pb-1">
            <input type="checkbox" v-model="showArchived" class="rounded" />
            Архивные
          </label>
          <!-- Сброс -->
          <button
            v-if="hasActiveFilters"
            @click="resetFilters"
            class="btn btn-secondary text-sm flex items-center gap-1 pb-1"
          >
            <X class="w-4 h-4" />Сбросить
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <DataTable
        v-else
        :columns="columns"
        :rows="visits"
        storage-key="visits_table"
        :row-class="() => 'cursor-pointer'"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :loading="loading"
        @row-click="openDetail"
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
        @reload="loadVisits"
      >
        <template #planned_date="{ row }">
          <span class="whitespace-nowrap">{{ formatDate(row.planned_date) }}</span>
          <span v-if="row.planned_time_from" class="text-gray-500 text-xs block">{{ row.planned_time_from.slice(0,5) }}</span>
        </template>

        <template #status="{ row }">
          <div class="flex flex-col gap-1">
            <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full w-fit" :class="statusClass(row.status)">
              {{ cfg.visitStatusLabel(row.status) }}
            </span>
            <span v-if="row.is_archived" class="inline-flex px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded-full w-fit">Архив</span>
          </div>
        </template>

        <template #priority="{ row }">
          <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="priorityClass(row.priority)">
            {{ cfg.priorityLabel(row.priority) }}
          </span>
        </template>

        <template #visit_type="{ row }">
          <span class="text-gray-700">{{ cfg.visitTypeLabel(row.visit_type) }}</span>
        </template>

        <template #actions="{ row }">
          <div class="flex items-center gap-2" @click.stop>
            <template v-if="!row.is_archived">
              <button @click="openEdit(row)" class="text-gray-500 hover:text-primary-600" title="Редактировать">
                <Pencil class="w-4 h-4" />
              </button>
              <button
                v-if="canCancel(row) && (auth.hasGroup('office_group') || auth.hasGroup('admin_group'))"
                @click="cancelConfirm = row"
                class="text-red-500 hover:text-red-700"
                title="Отменить выезд"
              >
                <Ban class="w-4 h-4" />
              </button>
              <button @click="archiveConfirm = row" class="text-amber-600 hover:text-amber-800" title="В архив">
                <Archive class="w-4 h-4" />
              </button>
            </template>
            <template v-else>
              <button v-if="auth.hasGroup('admin_group')" @click="handleUnarchive(row)" class="text-green-600 hover:text-green-800" title="Восстановить">
                <ArchiveRestore class="w-4 h-4" />
              </button>
            </template>
          </div>
        </template>

        <template #empty>
          <div class="flex flex-col items-center gap-2">
            <Calendar class="w-12 h-12 text-gray-300" />
            <span>Выезды не найдены</span>
          </div>
        </template>
      </DataTable>

      <!-- Detail Modal -->
      <div v-if="detailVisit" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 flex flex-col max-h-[90vh]">
          <!-- Header: фиксированный -->
          <div class="flex items-center justify-between p-4 md:p-6 border-b flex-shrink-0">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">{{ detailVisit.site_title }}</h2>
              <p v-if="detailVisit.client_name" class="text-sm text-gray-500 mt-0.5">{{ detailVisit.client_name }}</p>
            </div>
            <button @click="detailVisit = null" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <!-- Tabs: фиксированные -->
          <div class="flex border-b flex-shrink-0">
            <button
              @click="detailTab = 'info'"
              class="flex-1 py-2.5 text-sm font-medium transition-colors"
              :class="detailTab === 'info' ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500 hover:text-gray-700'"
            >Информация</button>
            <button
              @click="detailTab = 'files'"
              class="flex-1 py-2.5 text-sm font-medium transition-colors"
              :class="detailTab === 'files' ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500 hover:text-gray-700'"
            >Файлы и фото</button>
          </div>
          <!-- Контент: скроллируется -->
          <div class="overflow-y-auto flex-1">
            <!-- Info tab -->
            <div v-if="detailTab === 'info'" class="p-4 md:p-6 space-y-4">
              <div class="flex gap-2 flex-wrap">
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="statusClass(detailVisit.status)">{{ cfg.visitStatusLabel(detailVisit.status) }}</span>
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">{{ cfg.visitTypeLabel(detailVisit.visit_type) }}</span>
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full" :class="priorityClass(detailVisit.priority)">{{ cfg.priorityLabel(detailVisit.priority) }}</span>
              </div>
              <div><p class="text-sm text-gray-500">Адрес</p><p class="text-gray-900">{{ detailVisit.site_address }}</p></div>
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
            <!-- Files tab -->
            <div v-else class="p-4 md:p-6">
              <AttachmentsTab entity-type="visit" :entity-id="detailVisit.id" />
            </div>
          </div>
          <!-- Footer: фиксированный -->
          <div class="flex justify-between items-center p-4 md:p-6 border-t flex-shrink-0">
            <button
              v-if="detailVisit.status === 'done' || detailVisit.status === 'closed'"
              @click="openDefectCreate(detailVisit)"
              class="btn btn-secondary flex items-center text-yellow-700 border-yellow-300 hover:bg-yellow-50"
            >
              <AlertTriangle class="w-4 h-4 mr-2" />Добавить дефект
            </button>
            <div v-else />
            <div class="flex gap-3">
              <button v-if="!detailVisit.is_archived" @click="openEdit(detailVisit)" class="btn btn-secondary flex items-center"><Pencil class="w-4 h-4 mr-2" />Редактировать</button>
              <button @click="detailVisit = null" class="btn btn-primary">Закрыть</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Create / Edit Modal -->
      <div v-if="modalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-4 md:p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">{{ editing ? 'Редактировать выезд' : 'Создать выезд' }}</h2>
            <button @click="closeModal" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleSave" class="p-4 md:p-6 space-y-4">
            <!-- CREATE: клиент + мультивыбор объектов -->
            <template v-if="!editing">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Клиент *</label>
                <div class="relative">
                  <input
                    v-model="clientQuery"
                    type="text"
                    class="input pr-8"
                    :class="{ 'border-red-400': errors.client }"
                    placeholder="Начните вводить название..."
                    @focus="clientDropdownOpen = true"
                    @input="onClientQueryInput"
                    @keydown.escape="clientDropdownOpen = false"
                    autocomplete="off"
                  />
                  <ChevronDown class="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                  <div
                    v-if="clientDropdownOpen && filteredClients.length"
                    class="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
                  >
                    <button
                      v-for="c in filteredClients"
                      :key="c.id"
                      type="button"
                      class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
                      @click="selectClient(c); delete errors.client"
                    >{{ c.name }}</button>
                  </div>
                </div>
                <p v-if="errors.client" class="text-red-600 text-xs mt-1">{{ errors.client }}</p>
              </div>

              <!-- Договор (появляется после выбора клиента) -->
              <div v-if="selectedClient">
                <label class="block text-sm font-medium text-gray-700 mb-1">Договор</label>
                <select v-model="selectedContractId" class="input" @change="onContractChange">
                  <option value="">— Без договора (все объекты) —</option>
                  <option v-for="c in clientContracts" :key="c.id" :value="c.id">
                    {{ c.contract_number || 'Без номера' }}{{ c.subject ? ' — ' + c.subject : '' }}
                  </option>
                </select>
              </div>

              <!-- Объекты (появляются после выбора клиента) -->
              <div v-if="selectedClient">
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Объекты * <span class="text-gray-400 font-normal">(выбрано: {{ selectedSiteIds.length }})</span>
                </label>
                <div v-if="clientSitesLoading" class="text-sm text-gray-400 py-2">Загрузка объектов...</div>
                <template v-else>
                  <div v-if="clientSites.length" class="border border-gray-200 rounded-lg max-h-44 overflow-y-auto divide-y divide-gray-100">
                    <label
                      v-for="s in clientSites"
                      :key="s.id"
                      class="flex items-start gap-3 px-3 py-2 cursor-pointer hover:bg-gray-50"
                      @click.prevent="toggleSite(s.id); delete errors.sites"
                    >
                      <input type="checkbox" :checked="selectedSiteIds.includes(s.id)" class="mt-0.5 rounded flex-shrink-0" readonly />
                      <div class="min-w-0">
                        <p class="text-sm font-medium text-gray-900 truncate">{{ s.title }}</p>
                        <p class="text-xs text-gray-500 truncate">{{ s.address }}</p>
                      </div>
                    </label>
                  </div>
                  <p v-else class="text-sm text-gray-400 py-2">Нет объектов</p>
                </template>
                <p v-if="errors.sites" class="text-red-600 text-xs mt-1">{{ errors.sites }}</p>
              </div>
            </template>

            <!-- EDIT: обычный select объекта -->
            <div v-else>
              <label class="block text-sm font-medium text-gray-700 mb-1">Объект *</label>
              <select v-model="form.site_id" class="input" :class="{ 'border-red-400': errors.site_id }" @change="delete errors.site_id">
                <option value="">Выберите объект</option>
                <option v-for="s in sites" :key="s.id" :value="s.id">{{ s.title }} — {{ s.address }}</option>
              </select>
              <p v-if="errors.site_id" class="text-red-600 text-xs mt-1">{{ errors.site_id }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Мастер</label>
              <select v-model="form.assigned_user_id" class="input">
                <option value="">Не назначен</option>
                <option v-for="m in masters" :key="m.id" :value="m.id">{{ m.full_name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Дата *</label>
              <input v-model="form.planned_date" type="date" class="input" :class="{ 'border-red-400': errors.planned_date }" @input="delete errors.planned_date" />
              <p v-if="errors.planned_date" class="text-red-600 text-xs mt-1">{{ errors.planned_date }}</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div><label class="block text-sm font-medium text-gray-700 mb-1">Время с</label><input v-model="form.planned_time_from" type="time" class="input" /></div>
              <div><label class="block text-sm font-medium text-gray-700 mb-1">Время до</label><input v-model="form.planned_time_to" type="time" class="input" /></div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Тип</label>
                <select v-model="form.visit_type" class="input">
                  <option v-for="t in cfg.visitTypes" :key="t.sysname" :value="t.sysname">{{ t.display_name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Приоритет</label>
                <select v-model="form.priority" class="input">
                  <option v-for="p in cfg.priorities" :key="p.sysname" :value="p.sysname">{{ p.display_name }}</option>
                </select>
              </div>
            </div>
            <div v-if="editing">
              <label class="block text-sm font-medium text-gray-700 mb-1">Статус</label>
              <select v-model="form.status" class="input">
                <option v-for="s in cfg.visitStatuses" :key="s.sysname" :value="s.sysname">{{ s.display_name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Заметки</label>
              <textarea v-model="form.office_notes" class="input" rows="3" placeholder="Дополнительная информация..." />
            </div>
            <div class="flex justify-end gap-3 pt-4">
              <button type="button" @click="closeModal" class="btn btn-secondary">Отмена</button>
              <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
                {{ saving ? 'Сохранение...' : editing ? 'Сохранить' : selectedSiteIds.length > 1 ? `Создать ${selectedSiteIds.length} выезда` : 'Создать выезд' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Archive Confirm -->
      <div v-if="archiveConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-4 md:p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Отправить в архив?</h2>
          <p class="text-gray-600 mb-1">Выезд <strong>{{ archiveConfirm.site_title }}</strong> будет скрыт из основного списка.</p>
          <p class="text-sm text-gray-500 mb-6">Все данные сохранятся.</p>
          <div class="flex justify-end gap-3">
            <button @click="archiveConfirm = null" class="btn btn-secondary">Отмена</button>
            <button @click="handleArchive" class="btn bg-amber-600 text-white hover:bg-amber-700">В архив</button>
          </div>
        </div>
      </div>

      <!-- Defect Create Modal -->
      <div v-if="defectModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between p-4 md:p-6 border-b">
            <h2 class="text-xl font-semibold text-gray-900">Добавить дефект</h2>
            <button @click="defectModalOpen = false" class="text-gray-400 hover:text-gray-600"><X class="w-6 h-6" /></button>
          </div>
          <form @submit.prevent="handleDefectSave" class="p-4 md:p-6 space-y-4">
            <div class="text-sm text-gray-500 bg-gray-50 rounded-lg p-3">
              Объект: <span class="font-medium text-gray-900">{{ defectForm._site_title }}</span><br />
              Выезд от <span class="font-medium text-gray-900">{{ formatDate(defectForm._planned_date) }}</span>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Название *</label>
              <input v-model="defectForm.title" required class="input" placeholder="Краткое описание проблемы" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Описание</label>
              <textarea v-model="defectForm.description" class="input" rows="3" placeholder="Подробное описание..." />
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Приоритет</label>
                <select v-model="defectForm.priority" class="input">
                  <option v-for="p in cfg.priorities" :key="p.sysname" :value="p.sysname">{{ p.display_name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Тип действия</label>
                <select v-model="defectForm.action_type" class="input">
                  <option v-for="a in cfg.defectActionTypes" :key="a.sysname" :value="a.sysname">{{ a.display_name }}</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Необходимые запчасти</label>
              <input v-model="defectForm.suggested_parts" class="input" placeholder="Перечень запчастей..." />
            </div>
            <!-- Photo transfer from visit -->
            <div v-if="visitPhotos.length > 0">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Фото из выезда
                <span class="text-gray-400 font-normal">(все выбраны — нажмите на фото чтобы снять выбор)</span>
              </label>
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <label
                  v-for="photo in visitPhotos"
                  :key="photo.id"
                  class="relative cursor-pointer group"
                >
                  <input
                    type="checkbox"
                    class="sr-only"
                    :checked="selectedPhotos.includes(photo.id)"
                    @change="selectedPhotos.includes(photo.id) ? selectedPhotos.splice(selectedPhotos.indexOf(photo.id), 1) : selectedPhotos.push(photo.id)"
                  />
                  <img :src="photo.file_url" class="w-full h-24 object-cover rounded-lg border-2 transition-colors"
                    :class="selectedPhotos.includes(photo.id) ? 'border-primary-500' : 'border-gray-200'" />
                  <div v-if="selectedPhotos.includes(photo.id)"
                    class="absolute inset-0 bg-primary-500 bg-opacity-20 rounded-lg flex items-center justify-center">
                    <div class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                      <span class="text-white text-xs font-bold">✓</span>
                    </div>
                  </div>
                </label>
              </div>
              <p v-if="selectedPhotos.length > 0" class="text-xs text-primary-600 mt-1">Выбрано: {{ selectedPhotos.length }}</p>
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="defectModalOpen = false" class="btn btn-secondary">Отмена</button>
              <button type="submit" :disabled="saving" class="btn btn-primary disabled:opacity-50">
                {{ saving ? 'Сохранение...' : 'Создать дефект' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Cancel Confirm -->
      <div v-if="cancelConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-4 md:p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Отменить выезд?</h2>
          <p class="text-gray-600 mb-1">Выезд на объект <strong>{{ cancelConfirm.site_title }}</strong> будет переведён в статус «Отменён».</p>
          <p class="text-sm text-gray-500 mb-6">Это действие нельзя отменить.</p>
          <div class="flex justify-end gap-3">
            <button @click="cancelConfirm = null" class="btn btn-secondary">Назад</button>
            <button @click="handleCancel" class="btn bg-red-600 text-white hover:bg-red-700">Отменить выезд</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Plus, Calendar, MapPin, User, X, Eye, Pencil, Archive, ArchiveRestore, Ban, Image as ImageIcon, AlertTriangle, ChevronDown, Filter } from 'lucide-vue-next'
import Layout from '../components/Layout.vue'
import DataTable from '../components/DataTable.vue'
import AttachmentsTab from '../components/AttachmentsTab.vue'
import { useConfigStore } from '../stores/config.js'
import { useAuthStore } from '../stores/auth.js'
import { visitsAPI, sitesAPI, usersAPI, clientsAPI, contractsAPI, attachmentsAPI, defectsAPI } from '../services/api.js'
import { useEscClose } from '../composables/useEscClose.js'

const route = useRoute()
const cfg = useConfigStore()
const auth = useAuthStore()

const visits = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const filtersOpen = ref(false)
const loading = ref(true)
const filters = ref({ status: '', priority: '', date_from: '', date_to: '', master_id: '' })
const showArchived = ref(false)

const hasActiveFilters = computed(() =>
  filters.value.status || filters.value.priority || filters.value.date_from ||
  filters.value.date_to || filters.value.master_id || showArchived.value
)

function resetFilters() {
  filters.value = { status: '', priority: '', date_from: '', date_to: '', master_id: '' }
  showArchived.value = false
  page.value = 1
  loadVisits()
}
const modalOpen = ref(false)
const detailVisit = ref(null)
const detailTab = ref('info')
const editing = ref(null)
const saving = ref(false)
const archiveConfirm = ref(null)
const cancelConfirm = ref(null)
const defectModalOpen = ref(false)
const defectForm = ref({ title: '', description: '', priority: 'medium', action_type: 'repair', suggested_parts: '', visit_id: null, site_id: null, _site_title: '', _planned_date: '' })
const sites = ref([])
const masters = ref([])
const attachments = ref([])
const errors = ref({})
const visitPhotos = ref([])
const selectedPhotos = ref([])

useEscClose([
  { isOpen: () => !!detailVisit.value,     close: () => { detailVisit.value = null } },
  { isOpen: () => modalOpen.value,         close: () => { closeModal() } },
  { isOpen: () => !!archiveConfirm.value,  close: () => { archiveConfirm.value = null } },
  { isOpen: () => !!cancelConfirm.value,   close: () => { cancelConfirm.value = null } },
  { isOpen: () => defectModalOpen.value,   close: () => { defectModalOpen.value = false } },
])

// Реактивный пересчёт при изменении фильтров
watch(filters, () => { page.value = 1; loadVisits() }, { deep: true })
watch(showArchived, () => { page.value = 1; loadVisits() })

// Create form: client search + multi-site
const allClients = ref([])
const clientQuery = ref('')
const clientDropdownOpen = ref(false)
const selectedClient = ref(null)
const clientContracts = ref([])
const selectedContractId = ref('')
const clientSites = ref([])
const clientSitesLoading = ref(false)
const selectedSiteIds = ref([])

const filteredClients = computed(() => allClients.value)

let clientSearchTimer = null
async function onClientQueryInput() {
  clientDropdownOpen.value = true
  selectedClient.value = null
  clientContracts.value = []
  selectedContractId.value = ''
  clientSites.value = []
  selectedSiteIds.value = []
  clearTimeout(clientSearchTimer)
  clientSearchTimer = setTimeout(async () => {
    const q = clientQuery.value.trim()
    const res = await clientsAPI.getAll({ active_only: true, limit: 50, search: q || undefined })
    allClients.value = res.data.items
  }, 250)
}

async function selectClient(client) {
  selectedClient.value = client
  clientQuery.value = client.name
  clientDropdownOpen.value = false
  selectedSiteIds.value = []
  selectedContractId.value = ''
  clientContracts.value = []
  clientSites.value = []
  // Загружаем договоры клиента
  try {
    const cr = await contractsAPI.getByClient(client.id)
    clientContracts.value = cr.data?.items ?? cr.data ?? []
    // Если 1 договор — подставляем автоматически
    if (clientContracts.value.length === 1) {
      selectedContractId.value = clientContracts.value[0].id
      await onContractChange()
      return
    }
  } catch {
    clientContracts.value = []
  }
  // По умолчанию (без договора) — все объекты клиента
  await loadSitesByContract('')
}

async function onContractChange() {
  selectedSiteIds.value = []
  await loadSitesByContract(selectedContractId.value)
}

async function loadSitesByContract(contractId) {
  clientSitesLoading.value = true
  try {
    if (contractId) {
      const res = await contractsAPI.getById(contractId)
      clientSites.value = res.data.sites || []
    } else {
      const res = await sitesAPI.getAll({ client_id: selectedClient.value.id, active_only: true, limit: 500 })
      clientSites.value = res.data.items
    }
  } catch {
    clientSites.value = []
  } finally {
    clientSitesLoading.value = false
  }
}

function toggleSite(id) {
  const idx = selectedSiteIds.value.indexOf(id)
  if (idx === -1) selectedSiteIds.value.push(id)
  else selectedSiteIds.value.splice(idx, 1)
}

const columns = [
  { key: 'planned_date', label: 'Дата',       width: 130 },
  { key: 'site_title',   label: 'Объект',     width: 200 },
  { key: 'site_address', label: 'Адрес',      width: 200, defaultVisible: false },
  { key: 'master_name',  label: 'Мастер',     width: 160 },
  { key: 'visit_type',   label: 'Тип',        width: 130 },
  { key: 'status',       label: 'Статус',     width: 140 },
  { key: 'priority',     label: 'Приоритет',  width: 130, defaultVisible: false },
  { key: 'actions',      label: 'Действия',   width: 110, sortable: false },
]

const form = ref({
  site_id: '', assigned_user_id: '', planned_date: '', planned_time_from: '',
  planned_time_to: '', visit_type: 'maintenance', priority: 'medium',
  office_notes: '', status: 'planned',
})
const originalForm = ref(null)

function buildVisitParams() {
  const params = {}
  if (filters.value.status) params.status = filters.value.status
  if (filters.value.priority) params.priority = filters.value.priority
  if (filters.value.date_from) params.date_from = filters.value.date_from
  if (filters.value.date_to) params.date_to = filters.value.date_to
  if (filters.value.master_id) params.master_id = filters.value.master_id
  if (showArchived.value) params.show_archived = true
  return params
}

async function loadVisits() {
  loading.value = true
  try {
    const res = await visitsAPI.getAll({
      ...buildVisitParams(),
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    })
    visits.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onPageChange(p) { page.value = p; loadVisits() }
function onPageSizeChange(s) { pageSize.value = s; page.value = 1; loadVisits() }

async function loadFormData() {
  const [cr, mr] = await Promise.all([clientsAPI.getAll({ active_only: true, limit: 50 }), usersAPI.getMasters()])
  allClients.value = cr.data.items
  masters.value = mr.data
}

function canCancel(visit) {
  return visit.status === 'planned' || visit.status === 'in_progress'
}

async function handleCancel() {
  try {
    await visitsAPI.cancel(cancelConfirm.value.id)
    cancelConfirm.value = null
    await loadVisits()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

function validate() {
  const e = {}
  if (editing.value) {
    if (!form.value.site_id) e.site_id = 'Выберите объект'
  } else {
    if (!selectedClient.value) e.client = 'Выберите клиента'
    if (selectedSiteIds.value.length === 0) e.sites = 'Выберите хотя бы один объект'
  }
  if (!form.value.planned_date) e.planned_date = 'Укажите дату'
  errors.value = e
  return Object.keys(e).length === 0
}

function openCreate() {
  editing.value = null
  errors.value = {}
  form.value = { site_id: '', assigned_user_id: '', planned_date: '', planned_time_from: '', planned_time_to: '', visit_type: 'maintenance', priority: 'medium', office_notes: '', status: 'planned' }
  clientQuery.value = ''
  selectedClient.value = null
  clientContracts.value = []
  selectedContractId.value = ''
  clientSites.value = []
  selectedSiteIds.value = []
  clientSitesLoading.value = false
  clientDropdownOpen.value = false
  loadFormData()
  modalOpen.value = true
}

async function openEdit(v) {
  editing.value = v
  errors.value = {}
  form.value = {
    site_id: v.site_id || '', assigned_user_id: v.assigned_user_id || '',
    planned_date: v.planned_date?.slice(0, 10) || '', planned_time_from: v.planned_time_from?.slice(0, 5) || '',
    planned_time_to: v.planned_time_to?.slice(0, 5) || '', visit_type: v.visit_type || 'maintenance',
    priority: v.priority || 'medium', office_notes: v.office_notes || '', status: v.status || 'planned',
  }
  originalForm.value = { ...form.value }
  detailVisit.value = null
  // Загружаем только если ещё не загружено
  const tasks = []
  if (!sites.value.length) tasks.push(sitesAPI.getAll({ active_only: true }).then(r => { sites.value = r.data }))
  if (!masters.value.length) tasks.push(usersAPI.getMasters().then(r => { masters.value = r.data }))
  if (tasks.length) await Promise.all(tasks)
  modalOpen.value = true
}

async function openDetail(v) {
  detailTab.value = 'info'
  try {
    const vr = await visitsAPI.getById(v.id)
    detailVisit.value = vr.data
  } catch {
    detailVisit.value = v
  }
}

async function handleSave() {
  if (!validate()) return
  saving.value = true
  try {
    const base = {
      assigned_user_id: form.value.assigned_user_id || null,
      planned_date: form.value.planned_date,
      planned_time_from: form.value.planned_time_from || null,
      planned_time_to: form.value.planned_time_to || null,
      visit_type: form.value.visit_type,
      priority: form.value.priority,
      office_notes: form.value.office_notes || null,
    }
    if (editing.value) {
      if (JSON.stringify(form.value) === JSON.stringify(originalForm.value)) {
        closeModal()
        return
      }
      await visitsAPI.update(editing.value.id, { ...base, site_id: form.value.site_id, status: form.value.status })
    } else {
      await Promise.all(selectedSiteIds.value.map(sid => visitsAPI.create({ ...base, site_id: sid })))
    }
    closeModal()
    await loadVisits()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleArchive() {
  try {
    await visitsAPI.archive(archiveConfirm.value.id)
    archiveConfirm.value = null
    await loadVisits()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleUnarchive(v) {
  try {
    await visitsAPI.unarchive(v.id)
    await loadVisits()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

async function openDefectCreate(v) {
  defectForm.value = {
    title: '', description: '', priority: 'medium', action_type: 'repair', suggested_parts: '',
    visit_id: v.id, site_id: v.site_id,
    _site_title: v.site_title, _planned_date: v.planned_date,
  }
  selectedPhotos.value = []
  try {
    const res = await attachmentsAPI.getByVisit(v.id)
    visitPhotos.value = res.data.filter(a =>
      /\.(jpg|jpeg|png|gif|webp|heic|bmp|tiff)(\?|$)/i.test(a.file_url) ||
      a.file_url.includes('/image/upload/')
    )
    // Автовыбор всех фото
    selectedPhotos.value = visitPhotos.value.map(p => p.id)
  } catch {
    visitPhotos.value = []
  }
  defectModalOpen.value = true
}

async function handleDefectSave() {
  saving.value = true
  try {
    const defectRes = await defectsAPI.create({
      visit_id: defectForm.value.visit_id,
      site_id: defectForm.value.site_id,
      title: defectForm.value.title,
      description: defectForm.value.description || null,
      priority: defectForm.value.priority,
      action_type: defectForm.value.action_type,
      suggested_parts: defectForm.value.suggested_parts || null,
    })
    const defectId = defectRes.data.id
    // Copy selected photos to the new defect
    if (selectedPhotos.value.length > 0) {
      const photos = visitPhotos.value.filter(p => selectedPhotos.value.includes(p.id))
      await Promise.all(photos.map(p =>
        attachmentsAPI.upload({
          defect_id: defectId,
          kind: 'defect_photo',
          file_url: p.file_url,
          file_name: p.file_name,
        })
      ))
    }
    defectModalOpen.value = false
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function closeModal() { modalOpen.value = false; editing.value = null; errors.value = {}; clientDropdownOpen.value = false }
function openUrl(url) { window.open(url, '_blank') }

function statusClass(s) {
  const m = { planned: 'bg-blue-100 text-blue-700', in_progress: 'bg-green-100 text-green-700', closed: 'bg-gray-400 text-white', done: 'bg-gray-400 text-white', cancelled: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-700'
}
function priorityClass(p) {
  const m = { low: 'bg-gray-100 text-gray-600', medium: 'bg-yellow-100 text-yellow-700', high: 'bg-orange-100 text-orange-700', urgent: 'bg-red-100 text-red-700' }
  return m[p] || 'bg-gray-100 text-gray-700'
}
function formatDate(d) { return d ? new Date(d + 'T00:00:00').toLocaleDateString('ru-RU') : '—' }

watch(visits, (vl) => {
  const id = window.history.state?.openVisitId
  if (id && vl?.length) {
    const v = vl.find((x) => x.id === id)
    if (v) openDetail(v)
  }
}, { once: true })

onMounted(async () => {
  // Init filters from URL query params (e.g. from dashboard links)
  if (route.query.status) filters.value.status = route.query.status
  if (route.query.date_from) filters.value.date_from = route.query.date_from
  if (route.query.date_to) filters.value.date_to = route.query.date_to
  await loadVisits()
  usersAPI.getMasters().then(r => { masters.value = r.data })
  if (route.query.open_create) openCreate()
  if (route.query.open_visit) {
    try {
      const vr = await visitsAPI.getById(Number(route.query.open_visit))
      detailTab.value = 'info'
      detailVisit.value = vr.data
    } catch (e) {
      console.error('Could not open visit', e)
    }
  }
})
</script>
