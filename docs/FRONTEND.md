# Frontend Documentation — service-system-v2

## Stack

- **Vue 3** (Composition API, `<script setup>`)
- **Pinia** — state management
- **Vue Router 4** — client-side routing with navigation guards
- **Vite** — build tool
- **Axios** — HTTP client

Dev server: `npm run dev` → `http://localhost:3001`

---

## Project Structure

```
frontend/src/
├── components/
│   └── Layout.vue          # Main app shell: sidebar nav, header, slot
├── pages/                  # One component per route
│   ├── LoginPage.vue
│   ├── DashboardPage.vue
│   ├── MapPage.vue
│   ├── CalendarPage.vue
│   ├── ClientsPage.vue
│   ├── SitesPage.vue
│   ├── VisitsPage.vue
│   ├── MyVisitsPage.vue    # Master-only visit view
│   ├── DefectsPage.vue
│   ├── PurchasesPage.vue
│   ├── NotificationsPage.vue
│   ├── LogsPage.vue        # Audit log viewer
│   └── AdminPage.vue       # Admin panel (users, groups, config)
├── stores/
│   ├── auth.js             # Auth state (token, user, groups)
│   └── config.js           # Reference data (statuses, types, priorities)
├── services/
│   └── api.js              # Axios instance + all API method groups
└── router/
    └── index.js            # Routes + navigation guard
```

---

## Stores

### `useAuthStore` (`stores/auth.js`)

Persists token and user object in `localStorage`.

| State/Computed | Type | Description |
|---|---|---|
| `token` | `ref<string\|null>` | JWT token from login |
| `user` | `ref<object\|null>` | Full user object including `groups: string[]` |
| `isAuthenticated` | `computed<bool>` | `true` if both token and user are set |
| `groups` | `computed<string[]>` | Shorthand for `user.groups` |

| Method | Description |
|---|---|
| `login(email, password)` | Calls `POST /api/auth/login`, stores token + user |
| `logout()` | Clears token and user from memory and localStorage |
| `fetchMe()` | Refreshes user from `GET /api/auth/me`; calls `logout()` on error |
| `hasGroup(sysname)` | Returns `true` if user belongs to the given permission group |

**Usage example:**
```js
const auth = useAuthStore()
if (auth.hasGroup('admin_group')) { /* show admin link */ }
```

---

### `useConfigStore` (`stores/config.js`)

Loads all reference data from the API once per session (on first authenticated navigation).

| State | Type | Description |
|---|---|---|
| `visitStatuses` | `ref<array>` | `[{ sysname, display_name }]` |
| `visitTypes` | `ref<array>` | Same structure |
| `priorities` | `ref<array>` | Same structure |
| `defectStatuses` | `ref<array>` | Same structure |
| `defectActionTypes` | `ref<array>` | Same structure |
| `attachmentKinds` | `ref<array>` | Same structure |
| `purchaseStatuses` | `ref<array>` | Same structure |
| `serviceFrequencies` | `ref<array>` | Same structure |
| `loaded` | `ref<bool>` | `true` after first successful `loadAll()` |

| Method | Description |
|---|---|
| `loadAll()` | Fetches all 8 config endpoints in parallel; idempotent (skips if `loaded`) |
| `visitStatusLabel(sysname)` | Returns `display_name` or fallback to `sysname` |
| `visitTypeLabel(sysname)` | Same for visit types |
| `priorityLabel(sysname)` | Same for priorities |
| `defectStatusLabel(sysname)` | Same for defect statuses |
| `defectActionLabel(sysname)` | Same for defect action types |
| `purchaseStatusLabel(sysname)` | Same for purchase statuses |
| `serviceFrequencyLabel(sysname)` | Same for service frequencies |

**Usage example:**
```js
const config = useConfigStore()
const label = config.visitStatusLabel('in_progress') // → "В работе"
```

---

## Router (`router/index.js`)

### Routes

| Path | Component | Groups |
|------|-----------|--------|
| `/login` | `LoginPage.vue` | public |
| `/dashboard` | `DashboardPage.vue` | `office_group`, `admin_group` |
| `/map` | `MapPage.vue` | `office_group`, `admin_group` |
| `/calendar` | `CalendarPage.vue` | any authenticated |
| `/clients` | `ClientsPage.vue` | `office_group`, `admin_group` |
| `/sites` | `SitesPage.vue` | `office_group`, `admin_group` |
| `/visits` | `VisitsPage.vue` | `office_group`, `admin_group` |
| `/my-visits` | `MyVisitsPage.vue` | `master_group` |
| `/defects` | `DefectsPage.vue` | `office_group`, `admin_group` |
| `/purchases` | `PurchasesPage.vue` | `office_group`, `admin_group` |
| `/notifications` | `NotificationsPage.vue` | any authenticated |
| `/logs` | `LogsPage.vue` | `office_group`, `admin_group` |
| `/admin` | `AdminPage.vue` | `admin_group` |
| `/` | redirect | → `/dashboard` or `/my-visits` based on group |

### Navigation Guard (`beforeEach`)

1. Public routes (`meta.public`) → pass through
2. Unauthenticated → redirect `/login`
3. First navigation: call `config.loadAll()` to preload reference data
4. `meta.allowedGroups` check: if user has none of the allowed groups, redirect to group-appropriate default page
5. Root `/` redirect: masters without office/admin go to `/my-visits`; others go to `/dashboard`

---

## API Service (`services/api.js`)

Axios instance with base URL from `VITE_API_URL` env var (default: `http://localhost:8000/api`).

**Interceptors:**
- **Request**: attaches `Authorization: Bearer <token>` from `localStorage`
- **Response**: on `401`, clears localStorage and redirects to `/login`

### API Groups

#### `authAPI`
```js
authAPI.login(email, password)         // POST /auth/login
authAPI.getMe()                        // GET  /auth/me
authAPI.changePassword(current, new)   // PUT  /auth/change-password
```

#### `usersAPI`
```js
usersAPI.getAll(params)   // GET /users
usersAPI.getMasters()     // GET /users/masters
usersAPI.create(data)     // POST /users
usersAPI.update(id, data) // PUT  /users/{id}
```

#### `clientsAPI`
```js
clientsAPI.getAll(params)    // GET    /clients
clientsAPI.getById(id)       // GET    /clients/{id}
clientsAPI.create(data)      // POST   /clients
clientsAPI.update(id, data)  // PUT    /clients/{id}
clientsAPI.delete(id)        // DELETE /clients/{id}
```

#### `sitesAPI`
Same CRUD pattern: `getAll`, `getById`, `create`, `update`, `delete` on `/sites`.

#### `visitsAPI`
```js
visitsAPI.getAll(params)       // GET  /visits
visitsAPI.getCalendar(s, e)    // GET  /visits/calendar?start=&end=
visitsAPI.getById(id)          // GET  /visits/{id}
visitsAPI.create(data)         // POST /visits
visitsAPI.update(id, data)     // PUT  /visits/{id}
visitsAPI.complete(id, data)   // POST /visits/{id}/complete
visitsAPI.delete(id)           // DELETE /visits/{id}
```

#### `defectsAPI`
```js
defectsAPI.getAll(params)    // GET  /defects
defectsAPI.create(data)      // POST /defects
defectsAPI.update(id, data)  // PUT  /defects/{id}
```

#### `purchasesAPI`
```js
purchasesAPI.getAll(params)    // GET  /purchases
purchasesAPI.create(data)      // POST /purchases
purchasesAPI.update(id, data)  // PUT  /purchases/{id}
```

#### `attachmentsAPI`
```js
attachmentsAPI.getAll(visitId)  // GET  /attachments?visit_id=
attachmentsAPI.upload(formData) // POST /attachments (multipart)
```

#### `notificationsAPI`
```js
notificationsAPI.getAll()       // GET /notifications
notificationsAPI.markAsRead(id) // PUT /notifications/{id}/read
notificationsAPI.markAsUnread(id) // PUT /notifications/{id}/unread
```

#### `dashboardAPI`
```js
dashboardAPI.getStats()  // GET /dashboard/stats
```

#### `configAPI`
```js
configAPI.getVisitStatuses()            // GET /config/visit-statuses
configAPI.getVisitTypes()               // GET /config/visit-types
configAPI.getPriorities()               // GET /config/priorities
configAPI.getDefectStatuses()           // GET /config/defect-statuses
configAPI.getDefectActionTypes()        // GET /config/defect-action-types
configAPI.getAttachmentKinds()          // GET /config/attachment-kinds
configAPI.getPurchaseStatuses()         // GET /config/purchase-statuses
configAPI.getServiceFrequencies()       // GET /config/service-frequencies
configAPI.getEntityTypes()              // GET /config/entity-types
configAPI.createItem(resource, data)    // POST /config/{resource}
configAPI.updateItem(resource, sn, d)   // PUT  /config/{resource}/{sysname}
configAPI.deleteItem(resource, sn)      // DELETE /config/{resource}/{sysname}
```

#### `logsAPI`
```js
logsAPI.getAll(params)  // GET /logs
```
Params: `entity_type`, `action_sysname`, `entity_id_search`, `user_name_search`, `limit`, `offset`

#### `adminAPI`
```js
// Users
adminAPI.getUsers()
adminAPI.createUser(data)
adminAPI.updateUser(id, data)
adminAPI.deleteUser(id)
adminAPI.addUserToGroup(userId, groupSysname)
adminAPI.removeUserFromGroup(userId, groupSysname)

// Permission groups
adminAPI.getPermissionGroups()
adminAPI.createPermissionGroup(data)
adminAPI.updatePermissionGroup(sysname, data)
adminAPI.deletePermissionGroup(sysname)

// Permissions
adminAPI.getPermissions()
adminAPI.addPermissionToGroup(groupSysname, permSysname)
adminAPI.removePermissionFromGroup(groupSysname, permSysname)
```

---

## Pages

### LoginPage.vue
Email/password form. On submit calls `auth.login()`, then navigates to `/dashboard` or `/my-visits` depending on groups.

### DashboardPage.vue
Stats cards (visits today, visits this week, open defects by priority, active purchases). Uses `dashboardAPI.getStats()`. Accessible to `office_group` + `admin_group`.

### MapPage.vue
2GIS map showing all sites as markers. Uses `sitesAPI.getAll()`. Accessible to `office_group` + `admin_group`.

### CalendarPage.vue
Calendar view of visits for a selected month. Uses `visitsAPI.getCalendar(start, end)`. Accessible to all authenticated users (masters see only their visits on the backend side via filtering on master_id).

### ClientsPage.vue
Table of clients with search, create, edit, delete. Uses `clientsAPI`. Accessible to `office_group` + `admin_group`.

### SitesPage.vue
Table of sites with search, client filter, create, edit, delete. Uses `sitesAPI`. Accessible to `office_group` + `admin_group`.

### VisitsPage.vue
Table of visits with filters (status, priority, master, site, date range). Create, update, complete, delete visits. Uses `visitsAPI`. Accessible to `office_group` + `admin_group`.

### MyVisitsPage.vue
Master's own visits. Same data as VisitsPage but pre-filtered by `master_id=me`. Accessible to `master_group`.

### DefectsPage.vue
Table of defects with status/priority filters. Create, update status, approve. Uses `defectsAPI`. Accessible to `office_group` + `admin_group`.

### PurchasesPage.vue
Table of purchases with status filter. Create, update, change status. Uses `purchasesAPI`. Accessible to `office_group` + `admin_group`.

### NotificationsPage.vue
List of notifications for the current user. Mark as read/unread. Uses `notificationsAPI`. Accessible to all authenticated.

### LogsPage.vue
Audit log viewer. Filters: entity type (loaded from `/config/entity-types`), action sysname (grouped `<optgroup>` by entity), entity ID search, user name search. Pagination. Click row to open detail modal. Uses `logsAPI`. Accessible to `office_group` + `admin_group`.

### AdminPage.vue
Admin control panel with three tabs:

1. **Users** — table of all users, create/edit/delete, assign/remove permission groups per user
2. **Groups** — table of permission groups, create/edit/delete, edit permissions per group (modal with checkboxes grouped by resource)
3. **Config** — tab per reference resource (visit statuses, priorities, etc.), CRUD per item

Uses `adminAPI`, `configAPI`. Accessible to `admin_group` only.

---

## Component: Layout.vue

Persistent app shell rendered for all authenticated routes.

- **Sidebar navigation**: links filtered by current user's groups
  - Dashboard, Map, Calendar (office/admin)
  - Clients, Sites, Visits, Defects, Purchases (office/admin)
  - My Visits (master)
  - Notifications (all)
  - Logs (office/admin)
  - Admin (admin only)
- **Header**: current user's name + logout button
- **`<slot />`**: renders the current page

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api` | Backend API base URL |
| `VITE_2GIS_KEY` | — | 2GIS map API key (used in MapPage) |
| `VITE_CLOUDINARY_CLOUD_NAME` | — | Cloudinary cloud name for file uploads |
| `VITE_CLOUDINARY_UPLOAD_PRESET` | — | Cloudinary upload preset |

Set in `frontend/.env`.

---

## Running

```bash
# Install dependencies
cd frontend
npm install

# Development (hot reload)
npm run dev    # → http://localhost:3001

# Production build
npm run build  # output to dist/
```
