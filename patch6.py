with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

old_start = '        <!-- Users — admin only -->'
old_end   = '      </div>\n    </section>\n\n  </main>'

idx_start = h.find(old_start)
idx_end   = h.find(old_end, idx_start) + len(old_end)

if idx_start == -1 or idx_end == -1:
    print('NOT FOUND: admin section markers')
else:
    NEW = '''        <!-- Users — admin only -->
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
            <div class="card-foot" style="gap:8px;justify-content:flex-end">
              <button class="btn btn-primary" onclick="openNewUserModal()">+ New User</button>
            </div>
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
            <div class="card-foot" style="gap:8px;justify-content:flex-end">
              <button class="btn btn-primary" onclick="openNewBrandModal()">+ New Brand</button>
            </div>
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
            <div class="card-foot" style="gap:8px;">
              <input id="new-status-input" placeholder="New status…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
              <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('status')">Add</button>
            </div>
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
            <div class="card-foot" style="gap:8px;">
              <input id="new-order-status-input" placeholder="New order status…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
              <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('order_status')">Add</button>
            </div>
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
            <div class="card-foot" style="gap:8px;">
              <input id="new-region-input" placeholder="New region…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
              <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('region')">Add</button>
            </div>
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
            <div class="card-foot" style="gap:8px;">
              <input id="new-tag-input" placeholder="New tag…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
              <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('tag')">Add</button>
            </div>
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
            <div class="card-foot" style="gap:8px;">
              <input id="new-country-input" placeholder="New country…" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;flex:1;"/>
              <button class="btn btn-primary" style="padding:6px 12px" onclick="addRefItem('country')">Add</button>
            </div>
          </div>
        </div>

      </div>
    </section>

  </main>'''

    h = h[:idx_start] + NEW + h[idx_end:]
    print('OK: admin section updated — actions inside collapsible body')

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved.')
