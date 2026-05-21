with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

# ── 1. Replace entire admin section with consistent structure ──
OLD_ADMIN = '''    <!-- ===== ADMIN ===== -->
    <section class="view" id="view-admin" data-screen-label="Admin">
      <div class="page-head"><div><h1 class="page-title">Administration</h1><div class="page-sub">Users, brands, regions, tags and countries</div></div></div>
      <div class="page-body">'''

NEW_ADMIN_OPEN = '''    <!-- ===== ADMIN ===== -->
    <section class="view" id="view-admin" data-screen-label="Admin">
      <div class="page-head"><div><h1 class="page-title">Administration</h1><div class="page-sub">Users, brands, regions, tags and countries</div></div></div>
      <div class="page-body">'''

# Find and replace the entire admin body content
old_body_start = '        <!-- Users — admin only -->'
old_body_end   = '      </div>\n    </section>\n\n  </main>'

idx_start = h.find(old_body_start)
idx_end   = h.find(old_body_end, idx_start) + len(old_body_end)

if idx_start == -1 or idx_end == -1:
    print('NOT FOUND: admin body markers')
else:
    NEW_ADMIN_BODY = '''        <!-- Users — admin only -->
        <div class="card" id="admin-users-card" style="margin-bottom:16px;display:none">
          <div class="card-head" style="cursor:pointer" onclick="toggleSection('admin-users-body')">
            <div><div class="card-title">Users</div><div class="card-sub" id="admin-meta">Manage CRM access and roles</div></div>
            <span id="admin-users-chevron" style="color:var(--warm-grey)">▶</span>
          </div>
          <div id="admin-users-body" style="display:none">
            <div class="card-body" style="padding:0">
              <table class="data"><thead><tr>
                <th>Name</th><th>Email</th><th>Role</th><th style="width:140px"></th>
              </tr></thead>
              <tbody id="admin-users-tbody"><tr><td colspan="4" style="text-align:center;padding:30px;color:var(--warm-grey);">Loading…</td></tr></tbody>
              </table>
            </div>
          </div>
          <div class="card-foot" style="gap:8px;justify-content:flex-end">
            <button class="btn btn-primary" onclick="openNewUserModal()">+ New User</button>
          </div>
        </div>

        <!-- Brands -->
        <div class="card" style="margin-bottom:16px;">
          <div class="card-head" style="cursor:pointer" onclick="toggleSection('admin-brands-body')">
            <div><div class="card-title">Brands</div><div class="card-sub">Add or deactivate brands</div></div>
            <span id="admin-brands-chevron" style="color:var(--warm-grey)">▶</span>
          </div>
          <div id="admin-brands-body" style="display:none">
            <div class="card-body" style="padding:0">
              <table class="data"><thead><tr><th>Brand Name</th><th>Status</th><th>Notes</th><th style="width:80px"></th></tr></thead>
              <tbody id="admin-brands-tbody"><tr><td colspan="4" style="text-align:center;padding:30px;color:var(--warm-grey);">Loading…</td></tr></tbody>
              </table>
            </div>
          </div>
          <div class="card-foot" style="gap:8px;justify-content:flex-end">
            <button class="btn btn-primary" onclick="openNewBrandModal()">+ New Brand</button>
          </div>
        </div>

        <!-- Pipeline Statuses -->
        <div class="card" style="margin-bottom:16px;">
          <div class="card-head" style="cursor:pointer" onclick="toggleSection('admin-statuses-body')">
            <div><div class="card-title">Pipeline Statuses</div><div class="card-sub">Manage available deal statuses</div></div>
            <span id="admin-statuses-chevron" style="color:var(--warm-grey)">▶</span>
          </div>
          <div id="admin-statuses-body" style="display:none">
            <div style="padding:0 20px" id="admin-statuses-list"></div>
          </div>
          <div class="card-foot" style="gap:8px;">
            <input id="new-status-input" placeholder="New status…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
            <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('status')">Add</button>
          </div>
        </div>

        <!-- Order Statuses -->
        <div class="card" style="margin-bottom:16px;">
          <div class="card-head" style="cursor:pointer" onclick="toggleSection('admin-order-statuses-body')">
            <div><div class="card-title">Order Statuses</div><div class="card-sub">Manage available order statuses</div></div>
            <span id="admin-order-statuses-chevron" style="color:var(--warm-grey)">▶</span>
          </div>
          <div id="admin-order-statuses-body" style="display:none">
            <div style="padding:0 20px" id="admin-order-statuses-list"></div>
          </div>
          <div class="card-foot" style="gap:8px;">
            <input id="new-order-status-input" placeholder="New order status…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
            <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('order_status')">Add</button>
          </div>
        </div>

        <!-- Sales Regions -->
        <div class="card" style="margin-bottom:16px;">
          <div class="card-head" style="cursor:pointer" onclick="toggleSection('admin-regions-body')">
            <div><div class="card-title">Sales Regions</div><div class="card-sub">Manage available sales regions</div></div>
            <span id="admin-regions-chevron" style="color:var(--warm-grey)">▶</span>
          </div>
          <div id="admin-regions-body" style="display:none">
            <div style="padding:0 20px" id="admin-regions-list"></div>
          </div>
          <div class="card-foot" style="gap:8px;">
            <input id="new-region-input" placeholder="New region…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
            <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('region')">Add</button>
          </div>
        </div>

        <!-- Contact Tags -->
        <div class="card" style="margin-bottom:16px;">
          <div class="card-head" style="cursor:pointer" onclick="toggleSection('admin-tags-body')">
            <div><div class="card-title">Contact Tags</div><div class="card-sub">Manage available contact tags</div></div>
            <span id="admin-tags-chevron" style="color:var(--warm-grey)">▶</span>
          </div>
          <div id="admin-tags-body" style="display:none">
            <div style="padding:0 20px" id="admin-tags-list"></div>
          </div>
          <div class="card-foot" style="gap:8px;">
            <input id="new-tag-input" placeholder="New tag…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
            <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('tag')">Add</button>
          </div>
        </div>

        <!-- Countries -->
        <div class="card" style="margin-bottom:16px;">
          <div class="card-head" style="cursor:pointer" onclick="toggleSection('admin-countries-body')">
            <div><div class="card-title">Countries</div><div class="card-sub">Manage available countries</div></div>
            <span id="admin-countries-chevron" style="color:var(--warm-grey)">▶</span>
          </div>
          <div id="admin-countries-body" style="display:none">
            <div style="padding:8px 20px;max-height:300px;overflow-y:auto" id="admin-countries-list"></div>
          </div>
          <div class="card-foot" style="gap:8px;">
            <input id="new-country-input" placeholder="New country…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
            <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('country')">Add</button>
          </div>
        </div>

      </div>
    </section>

  </main>'''

    h = h[:idx_start] + NEW_ADMIN_BODY + h[idx_end:]
    print('OK: admin section rewritten')

# ── 2. Remove two icon-btn buttons (Inbox + Notifications) from topbar ──
old_icons = (
    '        <button class="icon-btn" title="Inbox">\n'
    '          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"></polyline><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path></svg>\n'
    '          <span class="dot"></span>\n'
    '        </button>\n'
    '        <button class="icon-btn" title="Notifications">\n'
    '          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>\n'
    '        </button>\n'
)
if old_icons in h:
    h = h.replace(old_icons, '')
    print('OK: icon buttons removed')
else:
    print('NOT FOUND: icon buttons')

# ── 3. Remove Board View button from pipeline page-actions ──
old_board_btn = (
    '          <button id="pipeline-board-btn" class="btn btn-secondary" onclick="toggleBoardView()">\n'
    '            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>\n'
    '            Board view\n'
    '          </button>\n'
)
if old_board_btn in h:
    h = h.replace(old_board_btn, '')
    print('OK: board view button removed')
else:
    print('NOT FOUND: board view button')

# Also remove the pipeline-board div
old_board_div = '        <div id="pipeline-board" style="display:none;overflow-x:auto;padding:8px 0 16px;flex-wrap:nowrap;align-items:flex-start"></div>\n'
if old_board_div in h:
    h = h.replace(old_board_div, '')
    print('OK: pipeline-board div removed')
else:
    print('NOT FOUND: pipeline-board div')

# ── 4. Replace logout click listener with confirmation popup ──
old_logout_listener = "document.getElementById('logout-btn')?.addEventListener('click', logout);"
new_logout_listener = (
    "document.getElementById('logout-btn')?.addEventListener('click', function() {\n"
    "  var popup = document.createElement('div');\n"
    "  popup.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999';\n"
    "  popup.innerHTML = '<div style=\"background:#fff;border-radius:12px;padding:28px 32px;min-width:280px;box-shadow:0 8px 32px rgba(0,0,0,.18);text-align:center\">'\n"
    "    + '<div style=\"font-family:Playfair Display,serif;font-size:17px;color:var(--navy);font-weight:700;margin-bottom:8px\">Sign out?</div>'\n"
    "    + '<div style=\"font-size:13px;color:var(--warm-grey);margin-bottom:24px\">You will need to sign in again to access the CRM.</div>'\n"
    "    + '<div style=\"display:flex;gap:10px;justify-content:center\">'\n"
    "    + '<button onclick=\"this.closest(\\'[style*=inset]\\').remove()\" style=\"padding:8px 20px;border:1px solid var(--line);border-radius:8px;background:#fff;font:inherit;font-size:13px;cursor:pointer\">Cancel</button>'\n"
    "    + '<button onclick=\"logout()\" style=\"padding:8px 20px;background:var(--navy);color:#fff;border:none;border-radius:8px;font:inherit;font-size:13px;cursor:pointer\">Sign out</button>'\n"
    "    + '</div></div>';\n"
    "  document.body.appendChild(popup);\n"
    "});"
)
if old_logout_listener in h:
    h = h.replace(old_logout_listener, new_logout_listener)
    print('OK: logout confirmation added')
else:
    print('NOT FOUND: logout listener')

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved.')
