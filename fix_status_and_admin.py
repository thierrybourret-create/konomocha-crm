import sys
sys.path.insert(0, '/home/thierry/konomocha-crm')
from dotenv import load_dotenv
load_dotenv('/home/thierry/konomocha-crm/.env')
from app.database import SessionLocal
from sqlalchemy import text

# --- 1. Fix pipeline_entries status values (enum keys → human-readable) ---
db = SessionLocal()
db.execute(text("""
UPDATE pipeline_entries SET status = CASE status
  WHEN 'awaiting_feedback' THEN 'Awaiting Feedback'
  WHEN 'awaiting_info'     THEN 'Awaiting Info'
  WHEN 'awaiting_samples'  THEN 'Awaiting Samples'
  WHEN 'cancelled'         THEN 'Cancelled'
  WHEN 'catalogue_sent'    THEN 'Catalogue Sent'
  WHEN 'closed'            THEN 'Closed / No Action'
  WHEN 'deposit_paid'      THEN 'Deposit Paid'
  WHEN 'form_completed'    THEN 'Form Completed'
  WHEN 'in_progress'       THEN 'In Progress'
  WHEN 'on_hold'           THEN 'On Hold'
  WHEN 'order_placed'      THEN 'Order Placed'
  WHEN 'price_list_sent'   THEN 'Price List Sent'
  WHEN 'pricing_sent'      THEN 'Price List Sent'
  WHEN 'quotation_sent'    THEN 'Quotation Sent'
  WHEN 'samples_delivered' THEN 'Samples Delivered'
  WHEN 'samples_requested' THEN 'Samples Requested'
  WHEN 'samples_sent'      THEN 'Samples Sent'
  WHEN 'stalled'           THEN 'Stalled'
  ELSE status
END
"""))
db.commit()
rows = db.execute(text("SELECT DISTINCT status, count(*) FROM pipeline_entries GROUP BY status ORDER BY status")).fetchall()
print('Status values after fix:')
for r in rows:
    print(' ', r)
db.close()

# --- 2. Fix admin card layout (HTML) ---
with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

# Users card: remove button+right-div from head, add closing div for body, add card-foot
old_users_head = (
    '          <div class="card-head" style="cursor:pointer" onclick="toggleSection(\'admin-users-body\')">\n'
    '            <div><div class="card-title">Users</div><div class="card-sub" id="admin-meta">Manage CRM access and roles</div></div>\n'
    '            <div class="right">\n'
    '              <button class="btn btn-primary" onclick="event.stopPropagation();openNewUserModal()">+ New User</button>\n'
    '              <span id="admin-users-chevron" style="color:var(--warm-grey);margin-left:8px">▶</span>\n'
    '            </div>\n'
    '          </div>\n'
    '          <div id="admin-users-body" style="display:none">\n'
    '          <div class="card-body" style="padding:0">\n'
    '            <table class="data"><thead><tr>\n'
    '              <th>Name</th><th>Email</th><th>Role</th><th style="width:140px"></th>\n'
    '            </tr></thead>\n'
    '            <tbody id="admin-users-tbody"><tr><td colspan="4" style="text-align:center;padding:30px;color:var(--warm-grey);">Loading…</td></tr></tbody>\n'
    '            </table>\n'
    '          </div>\n'
    '        </div>'
)
new_users_head = (
    '          <div class="card-head" style="cursor:pointer" onclick="toggleSection(\'admin-users-body\')">\n'
    '            <div><div class="card-title">Users</div><div class="card-sub" id="admin-meta">Manage CRM access and roles</div></div>\n'
    '            <span id="admin-users-chevron" style="color:var(--warm-grey)">▶</span>\n'
    '          </div>\n'
    '          <div id="admin-users-body" style="display:none">\n'
    '          <div class="card-body" style="padding:0">\n'
    '            <table class="data"><thead><tr>\n'
    '              <th>Name</th><th>Email</th><th>Role</th><th style="width:140px"></th>\n'
    '            </tr></thead>\n'
    '            <tbody id="admin-users-tbody"><tr><td colspan="4" style="text-align:center;padding:30px;color:var(--warm-grey);">Loading…</td></tr></tbody>\n'
    '            </table>\n'
    '          </div>\n'
    '          </div>\n'
    '          <div class="card-foot" style="gap:8px;justify-content:flex-end">\n'
    '            <button class="btn btn-primary" onclick="openNewUserModal()">+ New User</button>\n'
    '          </div>'
)
if old_users_head in h:
    h = h.replace(old_users_head, new_users_head)
    print('OK: Users card fixed')
else:
    print('NOT FOUND: Users card head')

# Brands card: same pattern
old_brands_head = (
    '          <div class="card-head" style="cursor:pointer" onclick="toggleSection(\'admin-brands-body\')">\n'
    '            <div><div class="card-title">Brands</div><div class="card-sub">Add or deactivate brands</div></div>\n'
    '            <div class="right">\n'
    '              <button class="btn btn-primary" onclick="event.stopPropagation();openNewBrandModal()">+ New Brand</button>\n'
    '              <span id="admin-brands-chevron" style="color:var(--warm-grey);margin-left:8px">▶</span>\n'
    '            </div>\n'
    '          </div>\n'
    '          <div id="admin-brands-body" style="display:none">\n'
    '          <div class="card-body" style="padding:0">\n'
    '            <table class="data"><thead><tr><th>Brand Name</th><th>Status</th><th>Notes</th><th style="width:80px"></th></tr></thead>\n'
    '            <tbody id="admin-brands-tbody"><tr><td colspan="4" style="text-align:center;padding:30px;color:var(--warm-grey);">Loading…</td></tr></tbody>\n'
    '            </table>\n'
    '          </div>\n'
    '        </div>'
)
new_brands_head = (
    '          <div class="card-head" style="cursor:pointer" onclick="toggleSection(\'admin-brands-body\')">\n'
    '            <div><div class="card-title">Brands</div><div class="card-sub">Add or deactivate brands</div></div>\n'
    '            <span id="admin-brands-chevron" style="color:var(--warm-grey)">▶</span>\n'
    '          </div>\n'
    '          <div id="admin-brands-body" style="display:none">\n'
    '          <div class="card-body" style="padding:0">\n'
    '            <table class="data"><thead><tr><th>Brand Name</th><th>Status</th><th>Notes</th><th style="width:80px"></th></tr></thead>\n'
    '            <tbody id="admin-brands-tbody"><tr><td colspan="4" style="text-align:center;padding:30px;color:var(--warm-grey);">Loading…</td></tr></tbody>\n'
    '            </table>\n'
    '          </div>\n'
    '          </div>\n'
    '          <div class="card-foot" style="gap:8px;justify-content:flex-end">\n'
    '            <button class="btn btn-primary" onclick="openNewBrandModal()">+ New Brand</button>\n'
    '          </div>'
)
if old_brands_head in h:
    h = h.replace(old_brands_head, new_brands_head)
    print('OK: Brands card fixed')
else:
    print('NOT FOUND: Brands card head')

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved index.html.')
