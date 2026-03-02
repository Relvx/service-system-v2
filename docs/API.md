# API Documentation — service-system-v2

Base URL: `http://localhost:8000/api`

All endpoints (except `POST /auth/login`) require an `Authorization: Bearer <token>` header.
Unauthenticated requests return **401**. Insufficient permissions return **403**.

---

## Authentication — `/api/auth`

### POST /api/auth/login
Login with email and password.

**Body**
```json
{ "email": "admin@system.local", "password": "admin123" }
```

**Response 200**
```json
{
  "token": "<jwt>",
  "user": {
    "id": "uuid",
    "email": "admin@system.local",
    "full_name": "Администратор",
    "phone": null,
    "is_active": true,
    "groups": ["admin_group"],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

**Errors**: `401` — wrong email/password. `422` — missing fields.

---

### GET /api/auth/me
Returns the current user's profile.

**Response 200** — same `UserOut` structure as above.

---

### PUT /api/auth/change-password
Change current user's password.

**Body**
```json
{ "current_password": "old", "new_password": "new123" }
```

**Response 200** `{ "message": "Password changed successfully" }`

**Errors**: `401` — wrong current password.

---

## Clients — `/api/clients`

All endpoints require authentication. No group restriction beyond `get_current_user`.

### GET /api/clients
List clients.

**Query params**
- `search` (str) — filter by name or INN (case-insensitive, partial match)
- `active_only` (bool) — if true, return only active clients

**Response 200** — `List[ClientOut]`

`ClientOut` fields: `id`, `name`, `inn`, `kpp`, `contacts`, `contact_person`, `notes`, `is_active`, `created_at`, `updated_at`

---

### GET /api/clients/{id}
Get client by UUID. **404** if not found.

---

### POST /api/clients
Create a client. Returns **201**.

**Body** (`ClientCreate`): `name` (required), `inn`, `kpp`, `contacts`, `contact_person`, `notes`

Logs action `client_create`. Saves history snapshot.

---

### PUT /api/clients/{id}
Update client fields. Returns **200** updated `ClientOut`.

**Body** (`ClientUpdate`): all fields optional — `name`, `inn`, `kpp`, `contacts`, `contact_person`, `notes`, `is_active`

Logs `client_change_status` when `is_active` changes, else `client_update`.

---

### DELETE /api/clients/{id}
Delete client. Returns **204**. **404** if not found.

Logs `client_delete`.

---

## Sites — `/api/sites`

### GET /api/sites
List sites.

**Query params**: `search` (by title/address), `client_id` (UUID filter)

**Response 200** — `List[SiteOut]`

`SiteOut` fields: `id`, `client_id`, `title`, `address`, `latitude`, `longitude`, `access_notes`, `onsite_contact`, `service_frequency`, `is_active`, `created_at`, `updated_at`, `client_name` (joined)

---

### GET /api/sites/{id}
Get site by UUID. **404** if not found.

---

### POST /api/sites
Create site. Returns **201**.

**Body** (`SiteCreate`): `title` (required), `client_id`, `address`, `latitude`, `longitude`, `access_notes`, `onsite_contact`, `service_frequency`

Logs `site_create`.

---

### PUT /api/sites/{id}
Update site. Returns **200**.

**Body** (`SiteUpdate`): all fields optional.

Logs `site_update`.

---

### DELETE /api/sites/{id}
Delete site. Returns **204**. **404** if not found.

Logs `site_delete`.

---

## Visits — `/api/visits`

### GET /api/visits
List visits with joined site/client/master data.

**Query params**: `status`, `priority`, `master_id` (UUID), `site_id` (UUID), `date_from` (date), `date_to` (date)

Special: `status=closed` matches both `done` and `closed`.

**Response 200** — `List[VisitOut]`

`VisitOut` fields: `id`, `site_id`, `assigned_user_id`, `planned_date`, `planned_time_from`, `planned_time_to`, `visit_type`, `priority`, `status`, `work_summary`, `checklist`, `defects_present`, `defects_summary`, `recommendations`, `completed_at`, `office_notes`, `created_at`, `updated_at`, plus joined: `site_title`, `site_address`, `client_name`, `master_name`, `master_phone`, `access_notes`, `onsite_contact`, `latitude`, `longitude`, `client_contacts`, `act_photos_count`

---

### GET /api/visits/calendar
List visits in a date range.

**Query params**: `start` (date, required), `end` (date, required)

**Response 200** — `List[VisitOut]`

---

### GET /api/visits/{id}
Get single visit. **404** if not found.

---

### POST /api/visits
Create visit. Returns **201**.

**Body** (`VisitCreate`):
```json
{
  "site_id": "uuid",
  "assigned_user_id": "uuid",
  "planned_date": "2026-03-10",
  "planned_time_from": "09:00",
  "planned_time_to": "12:00",
  "visit_type": "maintenance",
  "priority": "medium",
  "work_summary": null,
  "office_notes": null
}
```
`site_id` and `assigned_user_id` are required.

Sends notification to assigned master. Logs `visit_create`.

---

### PUT /api/visits/{id}
Update visit. Returns **200**.

**Body** (`VisitUpdate`): all fields optional including `status`, `checklist`, `defects_present`, etc.

Logic:
- `assigned_user_id` changed → logs `visit_assign`
- `status` changed → logs `visit_change_status`
- otherwise → logs `visit_update`

---

### POST /api/visits/{id}/complete
Mark visit as completed (sets `status = "closed"`).

**Body** (`VisitComplete`): `work_summary`, `checklist`, `defects_present`, `defects_summary`, `recommendations`

**Response 200** — updated `VisitOut`

Logs `visit_complete`.

---

### DELETE /api/visits/{id}
Delete visit. Returns **204**. **404** if not found.

Logs `visit_delete`.

---

## Defects — `/api/defects`

### GET /api/defects
List defects with joined site/client/visit data.

**Query params**: `status`, `priority`, `site_id` (UUID), `visit_id` (UUID)

`DefectOut` fields: `id`, `visit_id`, `site_id`, `title`, `description`, `priority`, `action_type`, `suggested_parts`, `status`, `created_at`, `updated_at`, plus joined: `site_title`, `address`, `client_name`, `visit_date`, `visit_type`

---

### POST /api/defects
Create defect. Returns **201**.

**Body** (`DefectCreate`): `title` (required), `visit_id`, `site_id`, `description`, `priority` (default: `medium`), `action_type` (default: `repair`), `suggested_parts`

Logs `defect_create`.

---

### PUT /api/defects/{id}
Update defect. Returns **200**. **404** if not found.

**Body** (`DefectUpdate`): `title`, `description`, `priority`, `action_type`, `suggested_parts`, `status`

Logic:
- `status == "approved"` → logs `defect_approve`
- `status` changed → logs `defect_change_status`
- otherwise → logs `defect_update`

---

## Purchases — `/api/purchases`

### GET /api/purchases
List purchases.

**Query params**: `status`, `defect_id` (UUID), `site_id` (UUID)

`PurchaseOut` fields: `id`, `defect_id`, `site_id`, `item`, `qty`, `status`, `due_date`, `notes`, `created_at`, `updated_at`, plus joined: `defect_title`, `site_title`

---

### POST /api/purchases
Create purchase. Returns **201**.

**Body** (`PurchaseCreate`): `item` (required), `defect_id`, `site_id`, `qty` (default: `1`), `due_date`, `notes`

Logs `purchase_create`.

---

### PUT /api/purchases/{id}
Update purchase. Returns **200**. **404** if not found.

**Body** (`PurchaseUpdate`): `item`, `qty`, `status`, `due_date`, `notes`

Logic:
- `status` changed → logs `purchase_change_status`
- otherwise → logs `purchase_update`

---

## Dashboard — `/api/dashboard`

Requires groups: `admin_group` or `office_group`.

### GET /api/dashboard/stats

**Response 200**
```json
{
  "visits_today": 3,
  "visits_this_week": 12,
  "open_defects": [
    { "priority": "high", "count": 2 },
    { "priority": "medium", "count": 5 }
  ],
  "active_purchases": 7
}
```

---

## Logs — `/api/logs`

Requires groups: `admin_group` or `office_group`.

### GET /api/logs
List audit log entries.

**Query params**:
- `entity_type` (str) — e.g. `client`, `visit`, `defect`
- `action_sysname` (str) — e.g. `visit_create`, `defect_approve`
- `entity_id_search` (str) — partial search on entity UUID
- `user_name_search` (str) — partial search on user full_name
- `limit` (int, default: 50) — max entries to return
- `offset` (int, default: 0) — pagination offset

**Response 200** — `List[LogOut]`

`LogOut` fields: `id`, `user_id`, `user_name`, `action_sysname`, `entity_type`, `entity_id`, `details`, `created_at`

---

## Config (Reference Data) — `/api/config`

Read endpoints: any authenticated user. Write endpoints (POST/PUT/DELETE): `admin_group` only.

### GET /api/config/{resource}
Returns list of all items for the given resource.

Available resources and their `sysname` key values:

| URL | Resource | Example sysnames |
|-----|----------|-----------------|
| `/api/config/visit-statuses` | Visit statuses | `planned`, `in_progress`, `closed`, `cancelled` |
| `/api/config/visit-types` | Visit types | `maintenance`, `inspection`, `repair` |
| `/api/config/priorities` | Priorities | `low`, `medium`, `high`, `critical` |
| `/api/config/defect-statuses` | Defect statuses | `open`, `in_progress`, `fixed`, `cancelled` |
| `/api/config/defect-action-types` | Defect action types | `repair`, `replace`, `monitor` |
| `/api/config/attachment-kinds` | Attachment kinds | `act_photo`, `defect_photo`, `document` |
| `/api/config/purchase-statuses` | Purchase statuses | `draft`, `approved`, `ordered`, `received`, `closed`, `cancelled` |
| `/api/config/service-frequencies` | Service frequencies | `monthly`, `quarterly`, `semi_annual`, `annual` |
| `/api/config/entity-types` | Entity types | `client`, `site`, `visit`, `defect`, `purchase` |

Each item has: `sysname`, `display_name` (and `display_name_plural` for entity-types).

---

### POST /api/config/{resource}
Create a new config item. Returns **201**. **409** if `sysname` already exists.

**Body**: `{ "sysname": "new_status", "display_name": "Новый статус" }`

---

### PUT /api/config/{resource}/{sysname}
Update `display_name` of a config item. Returns **200**. **404** if not found.

**Body**: `{ "display_name": "Обновлённое название" }`

---

### DELETE /api/config/{resource}/{sysname}
Delete a config item. Returns **204**. **404** if not found.

---

## Admin — `/api/admin`

All endpoints require group: `admin_group`.

### GET /api/admin/users
List all users with their groups.

**Response 200** — `List[UserOut]` (ordered by `full_name`)

---

### POST /api/admin/users
Create user. Returns **201**. **409** if email already exists.

**Body** (`UserCreate`): `email` (required), `password` (required), `full_name`, `phone`, `groups` (list of sysnames, optional)

---

### PUT /api/admin/users/{user_id}
Update user. Returns **200**. **404** if not found.

**Body** (`UserUpdate`): `full_name`, `phone`, `is_active`

---

### DELETE /api/admin/users/{user_id}
Delete user. Returns **204**. **404** if not found.

---

### POST /api/admin/users/{user_id}/groups/{group_sysname}
Add user to permission group. Returns **201**. Idempotent.

---

### DELETE /api/admin/users/{user_id}/groups/{group_sysname}
Remove user from permission group. Returns **204**.

---

### GET /api/admin/permission-groups
List all permission groups with their permissions.

`PermissionGroupOut`: `id`, `sysname`, `display_name`, `default_redirect`, `permissions: List[PermissionOut]`

---

### POST /api/admin/permission-groups
Create permission group. Returns **201**. **409** if sysname exists.

**Body**: `{ "sysname": "new_group", "display_name": "Новая группа", "default_redirect": "/dashboard" }`

---

### PUT /api/admin/permission-groups/{sysname}
Update permission group. Returns **200**.

**Body**: `{ "display_name": "Обновлённое", "default_redirect": "/visits" }`

---

### DELETE /api/admin/permission-groups/{sysname}
Delete permission group. Returns **204**.

---

### GET /api/admin/permissions
List all available permissions.

`PermissionOut`: `id`, `sysname`, `display_name`, `resource`, `action`

---

### POST /api/admin/permission-groups/{group_sysname}/permissions/{perm_sysname}
Assign permission to group. Returns **201**. Idempotent. **404** if group or permission not found.

---

### DELETE /api/admin/permission-groups/{group_sysname}/permissions/{perm_sysname}
Remove permission from group. Returns **204**.

---

## Users — `/api/users`

### GET /api/users
List users (for selection dropdowns).

**Query params**: `search` (by full_name or email)

---

### GET /api/users/masters
List users in `master_group`.

---

## Notifications — `/api/notifications`

### GET /api/notifications
List notifications for current user.

`NotificationOut`: `id`, `user_id`, `title`, `body`, `is_read`, `created_at`

---

### PUT /api/notifications/{id}/read
Mark notification as read.

---

### PUT /api/notifications/{id}/unread
Mark notification as unread.

---

## Attachments — `/api/attachments`

### GET /api/attachments
List attachments for a visit.

**Query params**: `visit_id` (UUID, required)

---

### POST /api/attachments
Upload an attachment (multipart/form-data).

**Form fields**: `visit_id` (UUID), `kind` (e.g. `act_photo`), `file` (file upload)

---

## Log Action Sysnames

Actions logged in the audit log:

| Sysname | Description |
|---------|-------------|
| `client_create` | Client created |
| `client_update` | Client updated |
| `client_delete` | Client deleted |
| `client_change_status` | Client `is_active` changed |
| `site_create` | Site created |
| `site_update` | Site updated |
| `site_delete` | Site deleted |
| `visit_create` | Visit created |
| `visit_update` | Visit updated |
| `visit_delete` | Visit deleted |
| `visit_complete` | Visit completed |
| `visit_assign` | Master reassigned to visit |
| `visit_change_status` | Visit status changed |
| `defect_create` | Defect created |
| `defect_update` | Defect updated |
| `defect_change_status` | Defect status changed |
| `defect_approve` | Defect approved |
| `purchase_create` | Purchase created |
| `purchase_update` | Purchase updated |
| `purchase_change_status` | Purchase status changed |
