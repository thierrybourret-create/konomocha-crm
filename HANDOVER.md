# Kizuna CRM — Handover Document
**Version:** v2.10  
**Date:** 21 May 2026  
**Revert tag:** `v2.10-stable`  
**Author:** Thierry Bourret / Claude Code

---

## 1. Overview

**Kizuna (絆)** is a bespoke CRM for Konomocha, managing sales pipeline, orders, commissions, and staff bonuses. It is a single-server FastAPI + vanilla-JS application hosted on a VPS.

---

## 2. Infrastructure

| Item | Value |
|------|-------|
| VPS host | `vps.konomocha.com` |
| SSH user | `thierry` |
| App root | `/home/thierry/konomocha-crm` |
| Frontend | `/home/thierry/konomocha-crm/static/index.html` |
| Python venv | `/home/thierry/konomocha-crm/venv` |
| Process manager | systemd → uvicorn (`app.main:app`) |
| Port | 443 (HTTPS via nginx reverse proxy) |
| API base path | `/crm/api/` |
| Database | PostgreSQL (local, user `thierry`) |
| Git remote | `git@github.com:tbourret/konomocha-crm.git` |
| Branch | `main` |

**Do not touch:**
- `/home/thierry/ako-sila/` (separate inventory app)
- `app/config.py`, `.env`
- Inventory backend on port 8000 (PM2 `inventory-backend`)

---

## 3. Deployment

### Backend patch (new endpoint / model change)
```bash
# 1. Write patch script to /tmp/patchXX.py on VPS
scp patchXX_be.py thierry@vps.konomocha.com:/tmp/

# 2. Run in venv on VPS
ssh thierry@vps.konomocha.com \
  "cd /home/thierry/konomocha-crm && source venv/bin/activate && python3 /tmp/patchXX_be.py"

# 3. Reload uvicorn
ssh thierry@vps.konomocha.com \
  "pgrep -f 'uvicorn app.main' | head -1 | xargs kill -HUP"
```

### Frontend patch (index.html)
```bash
# 1. SCP index.html locally
scp thierry@vps.konomocha.com:"/home/thierry/konomocha-crm/static/index.html" /tmp/patch_fe.html

# 2. Apply string replacements in Python, then JS syntax check:
node --check /tmp/patch_fe.js

# 3. SCP back
scp /tmp/patch_fe.html thierry@vps.konomocha.com:"/home/thierry/konomocha-crm/static/index.html"

# 4. Reload uvicorn (as above)
```

### Git commit after changes
```bash
ssh thierry@vps.konomocha.com \
  "cd /home/thierry/konomocha-crm && git add -A && git commit -m 'vX.Y: description' && git push"
```

---

## 4. Revert to v2.10-stable

```bash
ssh thierry@vps.konomocha.com \
  "cd /home/thierry/konomocha-crm && \
   git checkout v2.10-stable -- . && \
   git commit -m 'revert: back to v2.10-stable' && \
   git push && \
   pgrep -f 'uvicorn app.main' | head -1 | xargs kill -HUP"
```

---

## 5. Application Structure

```
konomocha-crm/
├── app/
│   ├── main.py                  # FastAPI app, router registration
│   ├── config.py                # DB URL, secret key (do not edit)
│   ├── constants.py             # Financial year helpers, pipeline probabilities fallback
│   ├── models/
│   │   └── models.py            # SQLAlchemy ORM models
│   └── routers/
│       ├── auth.py              # POST /login
│       ├── users.py             # GET/PUT /users
│       ├── contacts.py          # CRUD /contacts, notes, tasks, attachments, email logs
│       ├── pipeline.py          # CRUD /pipeline, forecast report
│       ├── orders.py            # CRUD /orders, mark-bonus-paid
│       ├── reports.py           # Commission forecast, bonus-summary
│       ├── brands.py            # CRUD /brands
│       ├── admin.py             # Admin settings (regions, tags, countries)
│       └── admin_stages.py      # CRUD /admin/stages (pipeline/order stage management)
├── static/
│   └── index.html               # Entire frontend (HTML + CSS + JS, ~243 KB)
├── alembic/                     # DB migrations
└── requirements.txt
```

---

## 6. Database Schema

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| name | varchar | Display name |
| email | varchar | Login email |
| hashed_password | varchar | bcrypt |
| role | varchar | `admin` or `agent` |
| is_active | boolean | |
| created_at | timestamp | |

**Current users:**
| id | name | role |
|----|------|------|
| 1 | Thierry Bourret | admin |
| 2 | Zeal Ornopia | agent |
| 3 | Ernalou Aguirre | agent |

---

### `contacts`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| name | varchar | |
| company | varchar | |
| email | varchar | |
| phone | varchar | |
| country | varchar | |
| address | varchar | |
| tags | varchar | Comma-separated |
| notes | text | |
| source | varchar | |
| job_title | varchar | |
| owner_id | integer FK → users.id | Assigned agent |
| created_at / updated_at | timestamp | |

---

### `pipeline_entries`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| contact_id | integer FK → contacts.id | |
| brand_id | integer FK → brands.id | |
| potential_value | numeric | |
| next_action | varchar | |
| fob_date | date | |
| status | varchar | Pipeline stage name |
| owner_id | integer FK → users.id | |
| notes | text | |
| created_at / updated_at | timestamp | |

---

### `pipeline_notes`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| pipeline_id | integer FK → pipeline_entries.id | |
| body | text | |
| author_id | integer FK → users.id | |
| created_at / updated_at | timestamp | |
| updated_by_id | integer FK → users.id | |

---

### `orders`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| contact_id | integer FK → contacts.id | |
| brand_id | integer FK → brands.id | |
| order_date | date | |
| order_value | numeric | Total order value |
| currency | varchar | e.g. `USD` |
| gross_commission_rate | numeric | e.g. 0.12 for 12% |
| testing_cost_deduction | numeric | Absolute $ deducted |
| net_commission | numeric | `order_value × rate − deduction` |
| bonus_amount | numeric | `net_commission × 0.05` (agents only; NULL for admin) |
| status | varchar | Order lifecycle stage (see §8) |
| owner_id | integer FK → users.id | Agent who owns the order |
| notes | text | |
| po_date | date | PO received |
| pi_date | date | Proforma invoice |
| deposit_date | date | |
| fob_date | date | |
| ship_date | date | |
| fully_paid_date | date | |
| commission_invoiced_date | date | |
| commission_paid_date | date | |
| bonus_paid_date | date | Set when bonus paid to staff |
| created_at / updated_at | timestamp | |

---

### `brands`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| name | varchar | |
| notes | text | |
| is_active | boolean | |
| created_at | timestamp | |

---

### `app_stages`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| stage_type | varchar | `pipeline` or `order` |
| name | varchar | Key/code (e.g. `commission_paid`) |
| label | varchar | Display label (e.g. `Commission Paid`) |
| probability | integer | 0–100, used in pipeline forecast |
| position | integer | Sort order |

**Pipeline stages (v2.10):** Prospect, Contacted, Sampling, Sample Approved, Negotiating, Committed, On Hold

**Order stages (v2.10):**
| Stage | Probability |
|-------|-------------|
| PO Received | 60% |
| Deposit Paid | 70% |
| Shipped | 80% |
| Fully Paid | 90% |
| Commission Invoiced | 95% |
| Commission Paid | 100% |
| Bonus Paid | 100% |

---

### `contact_notes`
| Column | Type |
|--------|------|
| id | integer PK |
| contact_id | integer FK |
| body | text |
| author_id | integer FK → users.id |
| created_at | timestamp |

---

### `contact_tasks`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| contact_id | integer FK | |
| title | varchar | |
| due_date | date | |
| completed | boolean | |
| completed_at | timestamp | |
| assigned_to_id | integer FK → users.id | |
| created_by_id | integer FK → users.id | |
| created_at | timestamp | |

---

### `contact_attachments`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| contact_id | integer FK | |
| filename | varchar | Original filename |
| stored_name | varchar | UUID-based stored name |
| file_size | integer | Bytes |
| uploaded_by_id | integer FK → users.id | |
| created_at | timestamp | |

---

### `email_logs`
| Column | Type | Notes |
|--------|------|-------|
| id | integer PK | |
| contact_id | integer FK | |
| direction | varchar | `inbound` or `outbound` |
| sent_at | timestamp | |
| subject | varchar | |
| body_snippet | text | |
| from_address | varchar | |
| to_address | varchar | |
| bcc_address | varchar | |
| raw_message_id | varchar | Gmail message ID |
| logged_by_id | integer FK → users.id | |
| created_at | timestamp | |

---

## 7. API Endpoints

### Auth
| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/login` | `{email, password}` → `{access_token, token_type}` |

### Users
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/users/me` | Current user |
| GET | `/api/users` | Admin only |
| PUT | `/api/users/{id}` | Admin only |

### Contacts
| Method | Path |
|--------|------|
| GET | `/api/contacts` |
| POST | `/api/contacts` |
| GET | `/api/contacts/{id}` |
| PUT | `/api/contacts/{id}` |
| DELETE | `/api/contacts/{id}` |
| GET/POST | `/api/contacts/{id}/notes` |
| GET/POST | `/api/contacts/{id}/tasks` |
| PUT | `/api/contacts/{id}/tasks/{tid}` |
| GET/POST | `/api/contacts/{id}/attachments` |
| GET/POST | `/api/contacts/{id}/email-logs` |

### Pipeline
| Method | Path |
|--------|------|
| GET | `/api/pipeline` |
| POST | `/api/pipeline` |
| GET | `/api/pipeline/{id}` |
| PUT | `/api/pipeline/{id}` |
| DELETE | `/api/pipeline/{id}` |
| GET/POST | `/api/pipeline/{id}/notes` |

### Orders
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/orders` | |
| POST | `/api/orders` | |
| GET | `/api/orders/{id}` | |
| PUT | `/api/orders/{id}` | |
| DELETE | `/api/orders/{id}` | |
| PUT | `/api/orders/mark-bonus-paid` | Admin only; `{order_ids: [1,2,...]}` → `{updated: N}` |

### Reports
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/reports/commission-forecast` | Pipeline forecast |
| GET | `/api/reports/my-bonus` | Agent's own bonus (uses auth token) |
| GET | `/api/reports/bonus-summary` | Admin only; `?quarter=Q1&fy=2026` optional |

**bonus-summary response shape:**
```json
{
  "quarter": "Q1 FY2026-27",
  "staff": [
    {
      "owner_id": 2,
      "owner_name": "Zeal Ornopia",
      "orders": [
        {
          "order_id": 12,
          "contact_name": "Acme Ltd",
          "brand_name": "Marbz",
          "net_commission": 2000.00,
          "bonus_amount": 100.00,
          "status": "commission_paid",
          "bonus_paid": false,
          "commission_paid_date": "2026-05-15",
          "bonus_paid_date": null
        }
      ],
      "total_bonus_earned": 100.00,
      "total_bonus_paid": 0.00,
      "total_bonus_outstanding": 100.00
    }
  ],
  "grand_total_earned": 100.00,
  "grand_total_paid": 0.00,
  "grand_total_outstanding": 100.00
}
```

### Brands
| Method | Path |
|--------|------|
| GET | `/api/brands` |
| POST | `/api/brands` |
| PUT | `/api/brands/{id}` |
| DELETE | `/api/brands/{id}` |

### Admin
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/admin/settings` | Regions, tags, countries |
| PUT | `/api/admin/settings` | |
| GET | `/api/admin/stages` | `{pipeline: [...], order: [...]}` |
| POST | `/api/admin/stages` | `{stage_type, name, label, probability}` |
| PUT | `/api/admin/stages/{id}` | Partial update |
| DELETE | `/api/admin/stages/{id}` | |

---

## 8. Order Lifecycle

```
po_received → deposit_paid → shipped → fully_paid → commission_invoiced → commission_paid → bonus_paid
```

| Status | Meaning |
|--------|---------|
| `po_received` | Purchase order received from buyer |
| `deposit_paid` | Deposit paid by buyer |
| `shipped` | Goods shipped; commission not yet due |
| `fully_paid` | Buyer paid in full; commission invoice not yet sent |
| `commission_invoiced` | Commission invoice sent; awaiting payment from principal |
| `commission_paid` | Commission received from principal; **bonus owed to agent** |
| `bonus_paid` | Bonus paid to agent; closed |

**Bonus rules:**
- `bonus_amount = net_commission × 0.05`
- Bonus is owed when status = `commission_paid`
- Bonus is paid when `bonus_paid_date` is set (via Mark Bonus Paid button)
- `total_bonus_earned` = sum of bonus_amount where status in (`commission_paid`, `bonus_paid`)
- `total_bonus_outstanding` = earned − paid
- Orders at `commission_invoiced` are shown separately as "awaiting principal payment" — not yet in earned
- Thierry's orders have `bonus_amount = NULL` (admin, no bonus entitlement)

---

## 9. Financial Year Logic

**April–March financial year:**
- Q1 = Apr / May / Jun
- Q2 = Jul / Aug / Sep
- Q3 = Oct / Nov / Dec
- Q4 = Jan / Feb / Mar

**Helpers in `app/constants.py`:**
```python
quarter_of(date)              # → (fy_start_year, q_number)
quarter_label(fy, q)          # → "Q1 FY2026-27"
quarter_date_range(fy, q)     # → (start_date, end_date)
```

**Commission lag:** `commission_due_date = ship_date + 30 days`

**Pipeline probability fallback:** If `app_stages` table is empty for pipeline, `get_db_probabilities(db)` falls back to `PIPELINE_PROBABILITIES` dict in `app/constants.py`.

---

## 10. Frontend Architecture

**Single file:** `static/index.html` (~243 KB, vanilla JS, no build step, no npm)

**Auth pattern:**
- JWT stored in `localStorage('crm_token')`
- Globals: `TOKEN` (string), `CURRENT_USER` (`{id, name, role, is_admin}`)
- Set at login, read on page load

**Navigation:**
- `activate(viewName)` → shows correct section, calls `loadView(viewName)`
- View loaders: `loadContacts()`, `loadOrders()`, `loadDashboard()`, `loadAdmin()`, etc.

**API calls:**
```js
apiFetch('/reports/bonus-summary')                          // GET
apiFetch('/orders/mark-bonus-paid', {method:'PUT', body:JSON.stringify({order_ids:[1,2]})})
```

**Key globals:**
- `_stageProbs` — `{stageName: stageObject}` — populated by `loadStageProbs()`
- `_stageList` — `{pipeline: [...], order: [...]}` — populated by `loadStageProbs()`
- `BRANDS` — array of brand objects
- `CONTACTS` — array of contact objects (cached)

**Dashboard widget pattern:**
```
loadDashboard()
  ├── if (!d.is_admin) → show #agent-bonus-widget, loadMyBonus()
  └── if (d.is_admin)  → show #admin-bonus-widget, loadAdminBonusWidget()
```

**Admin stage management functions:**
- `loadStageProbs()` — fetch `/api/admin/stages`, fill `_stageProbs` + `_stageList`
- `renderDbStageList(elId, stageType)` — render stage list with editable % inputs
- `updateStageProb(id, value)` — PUT `/api/admin/stages/{id}`
- `deleteStageById(id)` — DELETE `/api/admin/stages/{id}`, reload
- `addRefItem('status'|'order_status')` — POST `/api/admin/stages`

**Formatting helpers:**
- `fmtVal(n)` — `$1,234.56`
- `fmtShort(n)` — `$1.2k` / `$1.2M`
- `escHtml(s)` — escape HTML entities
- `showToast(msg)` — transient toast notification

**JS safety rules:**
- Never nest `'...'` inside `onclick="..."` HTML attributes — use `addEventListener` or DOM `.onclick`
- Use `document.createElement` + closure for dynamic event handlers with IDs
- Always run `node --check` before deploying modified index.html

---

## 11. Branding (v2.10)

| Location | Text |
|----------|------|
| Browser tab | `Kizuna — Konomocha` |
| Login heading | `Kizuna` (Playfair Display, 28px) |
| Login subtext | `絆` then `KONOMOCHA CRM · SIGN IN` |
| Sidebar wordmark | `Kizuna` + `CRM` below |
| About row | `Kizuna — Konomocha CRM` |
| JS comment | `// Kizuna (Konomocha CRM) v2.10` |

---

## 12. Version History

| Tag / Commit | Date | Description |
|---|---|---|
| `v2.10-stable` | 2026-05-21 | **Stable revert point** — Kizuna branding, admin bonus widget, DB-backed stage probabilities |
| v2.10 | 2026-05-21 | Full feature set: bonus widget, stage probability editing, Kizuna rename |
| v2.9 | 2026-05-xx | Stage management (DB-backed pipeline/order stages) |
| v2.8 | 2026-05-xx | Commission forecast improvements |
| Earlier | — | Legacy patches |

**Changes in v2.10:**
- Renamed app to Kizuna (絆)
- Admin Bonus Widget on dashboard (all staff, per-quarter view)
- Agent My Bonus widget on dashboard
- `GET /api/reports/bonus-summary` endpoint
- `PUT /api/orders/mark-bonus-paid` endpoint
- Pipeline/Order stage probabilities editable in admin UI, stored in `app_stages` table
- Removed "Order Placed" and "Deposit Paid" from pipeline (they are order statuses)
- Order stage probabilities seeded (60% → 100%)
- `app_stages` table and `/api/admin/stages` CRUD
- `renderDbStageList()` replaces localStorage-based stage list rendering

---

## 13. Common Operations

### Restart uvicorn after a backend change
```bash
ssh thierry@vps.konomocha.com \
  "pgrep -f 'uvicorn app.main' | head -1 | xargs kill -HUP"
```

### Check application logs
```bash
ssh thierry@vps.konomocha.com "journalctl -u konomocha -n 100 --no-pager"
```

### Connect to database interactively
```bash
ssh thierry@vps.konomocha.com "psql -U thierry konomocha_crm"
```

### Run Alembic migrations
```bash
ssh thierry@vps.konomocha.com \
  "cd /home/thierry/konomocha-crm && source venv/bin/activate && alembic upgrade head"
```

### Check current git status on VPS
```bash
ssh thierry@vps.konomocha.com \
  "cd /home/thierry/konomocha-crm && git log --oneline -10"
```

---

## 14. Security Notes

- All endpoints require `Authorization: Bearer <token>` except `/api/login`
- Admin-only endpoints check `current_user.role == 'admin'`; raise HTTP 403 otherwise
- Agent users see only their own pipeline entries and orders (filtered by `owner_id`)
- Bonus figures for one agent are never returned to another agent (`my-bonus` uses auth token)
- `bonus-summary` endpoint is admin-only
- Never commit `.env` or `config.py`

---

*End of handover document — Kizuna CRM v2.10 — 21 May 2026*
