export const statuses = { new: 'Новая', in_progress: 'В работе', closed: 'Закрыта', spam: 'Спам' }
export const categories = { boiler: 'Котельные', gas: 'Газовое оборудование', heat: 'Тепловые пункты', other: 'Другое' }
export const workTypes = { maintenance: 'Техобслуживание', diagnostics: 'Диагностика', repair: 'Ремонт', commissioning: 'Пусконаладка', verification: 'Поверка', emergency: 'Аварийный выезд', consultation: 'Консультация', other: 'Другое' }
export const customerTypes = { private: 'Частный заказчик', legal: 'Юридическое лицо', budget: 'Бюджетная организация', other: 'Другое' }
export const formats = { single: 'Разовый выезд', contract: 'По договору', undecided: 'Пока не определились' }
export const intents = { general: 'Обращение', documents: 'Запрос документов', verification: 'Поверка' }
export const dateLabel = value => value ? new Date(value).toLocaleString('ru-RU', { timeZone: 'Europe/Moscow', dateStyle: 'short', timeStyle: 'short' }) : '—'
export const errorMessage = error => typeof error.response?.data?.detail === 'string' ? error.response.data.detail : error.response?.status === 422 ? 'Проверьте заполнение полей.' : 'Не удалось выполнить запрос. Повторите попытку.'
