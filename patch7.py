import os

# ── 1. Write reports.py backend ──
REPORTS_PY = '''from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import Contact, PipelineEntry, Order, EmailLog
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/reports", tags=["reports"])

def _missing(db, field, source_filter=None):
    col = getattr(Contact, field)
    q = db.query(Contact)
    if source_filter == "contacts":
        q = q.filter(Contact.source != "lacrm_company_import")
    elif source_filter == "companies":
        q = q.filter(Contact.source == "lacrm_company_import")
    return q.filter(or_(col == None, col == "")).count()

@router.get("/contact-quality")
def contact_quality(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    c_total = db.query(Contact).filter(Contact.source != "lacrm_company_import").count()
    co_total = db.query(Contact).filter(Contact.source == "lacrm_company_import").count()
    c_fields  = ["email", "phone", "company", "country", "tags", "notes"]
    co_fields = ["country", "tags", "notes"]
    return {
        "contacts": {
            "total": c_total,
            "missing": {f: _missing(db, f, "contacts") for f in c_fields},
        },
        "companies": {
            "total": co_total,
            "missing": {f: _missing(db, f, "companies") for f in co_fields},
        },
    }

@router.get("/activity")
def activity_report(
    period: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    deltas = {"1d": 1, "7d": 7, "30d": 30, "90d": 90, "365d": 365}
    start = datetime.utcnow() - timedelta(days=deltas.get(period, 30))
    new_contacts  = db.query(Contact).filter(
        Contact.source != "lacrm_company_import", Contact.created_at >= start).count()
    new_companies = db.query(Contact).filter(
        Contact.source == "lacrm_company_import", Contact.created_at >= start).count()
    new_pipeline  = db.query(PipelineEntry).filter(PipelineEntry.created_at >= start).count()
    new_orders    = db.query(Order).filter(Order.created_at >= start).count()
    emails_in     = db.query(EmailLog).filter(
        EmailLog.sent_at >= start, EmailLog.direction == "inbound").count()
    emails_out    = db.query(EmailLog).filter(
        EmailLog.sent_at >= start, EmailLog.direction == "outbound").count()
    return {
        "period": period,
        "since": start.date().isoformat(),
        "new_contacts": new_contacts,
        "new_companies": new_companies,
        "new_pipeline_entries": new_pipeline,
        "new_orders": new_orders,
        "emails_inbound": emails_in,
        "emails_outbound": emails_out,
    }
'''

with open('/home/thierry/konomocha-crm/app/routers/reports.py', 'w', encoding='utf-8') as f:
    f.write(REPORTS_PY)
print('OK: reports.py written')

# ── 2. Patch main.py ──
with open('/home/thierry/konomocha-crm/app/main.py', encoding='utf-8') as f:
    m = f.read()
if 'reports' not in m:
    m = m.replace(
        'from app.routers import auth, contacts, brands, pipeline, orders, emails, users, dashboard',
        'from app.routers import auth, contacts, brands, pipeline, orders, emails, users, dashboard, reports'
    )
    m = m.replace(
        'app.include_router(dashboard.router)',
        'app.include_router(dashboard.router)\napp.include_router(reports.router)'
    )
    with open('/home/thierry/konomocha-crm/app/main.py', 'w', encoding='utf-8') as f:
        f.write(m)
    print('OK: main.py updated')
else:
    print('OK: reports already in main.py')

# ── 3. HTML changes ──
with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

# 3a. Add Reports to sidebar (before admin nav section)
old_admin_section = '        <div class="sb-section" id="admin-nav-section" style="display:none">Admin</div>'
new_sidebar_reports = (
    '      <button class="sb-item" data-view="reports">\n'
    '        <svg class="sb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>\n'
    '        <span>Reports</span>\n'
    '      </button>\n'
    '    </nav>\n\n'
    '        <div class="sb-section" id="admin-nav-section" style="display:none">Admin</div>'
)
if old_admin_section in h:
    h = h.replace(old_admin_section, new_sidebar_reports)
    print('OK: Reports added to sidebar')
else:
    print('NOT FOUND: admin-nav-section marker')

# 3b. Add 'reports' to TITLES constant
h = h.replace(
    "const TITLES = { dashboard:'Dashboard', contacts:'Contacts', companies:'Companies', pipeline:'Pipeline', brands:'Brands', orders:'Orders', email:'Email Log', admin:'Admin' };",
    "const TITLES = { dashboard:'Dashboard', contacts:'Contacts', companies:'Companies', pipeline:'Pipeline', brands:'Brands', orders:'Orders', email:'Email Log', reports:'Reports', admin:'Admin' };"
)
print('OK: TITLES updated')

# 3c. Wire loadReports on view switch
old_load_brands = "  if(view==='brands')    await loadBrands();"
new_load_brands = (
    "  if(view==='brands')    await loadBrands();\n"
    "  if(view==='reports')   await loadReports();"
)
h = h.replace(old_load_brands, new_load_brands)
print('OK: loadReports wired to view switch')

# 3d. Add Reports view section before the Admin section
old_admin_view = '    <!-- ===== ADMIN ===== -->'
NEW_REPORTS_VIEW = '''    <!-- ===== REPORTS ===== -->
    <section class="view" id="view-reports" data-screen-label="Reports">
      <div class="page-head">
        <div><h1 class="page-title">Reports</h1><div class="page-sub" id="reports-sub">Data quality and activity</div></div>
      </div>
      <div class="page-body">

        <!-- Contact Data Quality -->
        <div class="card" style="margin-bottom:16px;">
          <div class="card-head">
            <div><div class="card-title">Contact Data Quality</div><div class="card-sub">Fields missing across your contact and company records</div></div>
          </div>
          <div class="card-body">
            <div id="reports-quality-body" style="padding:20px;color:var(--warm-grey);text-align:center">Loading…</div>
          </div>
        </div>

        <!-- Activity Report — admin only -->
        <div class="card" id="reports-activity-card" style="margin-bottom:16px;display:none">
          <div class="card-head">
            <div><div class="card-title">Activity Report</div><div class="card-sub">Items created and emails logged in the selected period</div></div>
            <select id="reports-period" onchange="loadActivityReport()" style="padding:7px 12px;font:inherit;font-size:13px;color:var(--navy);border:1px solid var(--line);border-radius:8px;background:var(--white);">
              <option value="1d">Today</option>
              <option value="7d">Last 7 days</option>
              <option value="30d" selected>Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="365d">Last 12 months</option>
            </select>
          </div>
          <div class="card-body">
            <div id="reports-activity-body" style="padding:20px;color:var(--warm-grey);text-align:center">Loading…</div>
          </div>
        </div>

      </div>
    </section>

    <!-- ===== ADMIN ===== -->'''

if old_admin_view in h:
    h = h.replace(old_admin_view, NEW_REPORTS_VIEW)
    print('OK: Reports view section added')
else:
    print('NOT FOUND: admin view marker')

# 3e. Add reports JS functions before the closing script tag area
old_marker = "// ---- Brands ----"
NEW_REPORT_JS = '''// ---- Reports ----
async function loadReports() {
  await Promise.all([loadQualityReport(), loadActivityReport()]);
  var u = JSON.parse(localStorage.getItem('crm_user')||'{}');
  var ac = document.getElementById('reports-activity-card');
  if (ac) ac.style.display = (u.role==='admin') ? '' : 'none';
}

async function loadQualityReport() {
  var el = document.getElementById('reports-quality-body');
  if (!el) return;
  var d = await apiFetch('/reports/contact-quality');
  if (!d) { el.innerHTML='<span style="color:#B33A47">Failed to load.</span>'; return; }
  var fieldLabels = {email:'Email',phone:'Phone',company:'Company',country:'Country',tags:'Tags / Region',notes:'Notes'};

  function qualityTable(data, title) {
    var rows = Object.entries(data.missing).map(function([f,cnt]) {
      var pct = data.total ? Math.round(cnt/data.total*100) : 0;
      var bar = '<div style="height:6px;border-radius:3px;background:var(--line);overflow:hidden;width:120px;display:inline-block;vertical-align:middle">'
        + '<div style="height:100%;width:'+pct+'%;background:'+(pct>50?'#B33A47':pct>20?'#D97706':'#22C55E')+'"></div></div>';
      return '<tr>'
        + '<td style="padding:10px 16px;font-weight:500">'+(fieldLabels[f]||f)+'</td>'
        + '<td style="padding:10px 16px;text-align:right;font-family:JetBrains Mono,monospace">'+fmtNum(cnt)+'</td>'
        + '<td style="padding:10px 16px;text-align:right;font-family:JetBrains Mono,monospace;color:var(--warm-grey)">'+pct+'%</td>'
        + '<td style="padding:10px 16px">'+bar+'</td>'
        + '</tr>';
    }).join('');
    return '<div style="margin-bottom:24px">'
      + '<div style="font-weight:600;font-size:13px;color:var(--navy);padding:0 16px 8px">'+title+' <span style="font-weight:400;color:var(--warm-grey);font-size:12px">('+fmtNum(data.total)+' total)</span></div>'
      + '<table style="width:100%;border-collapse:collapse;font-size:13px">'
      + '<thead><tr style="border-bottom:1px solid var(--line)">'
      + '<th style="padding:8px 16px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey)">Field</th>'
      + '<th style="padding:8px 16px;text-align:right;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey)">Missing</th>'
      + '<th style="padding:8px 16px;text-align:right;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey)">%</th>'
      + '<th style="padding:8px 16px"></th></tr></thead>'
      + '<tbody>'+rows+'</tbody></table></div>';
  }

  el.innerHTML = qualityTable(d.contacts, 'Contacts') + qualityTable(d.companies, 'Companies');
}

async function loadActivityReport() {
  var el = document.getElementById('reports-activity-body');
  if (!el) return;
  var sel = document.getElementById('reports-period');
  var period = sel ? sel.value : '30d';
  el.innerHTML = '<div style="padding:20px;color:var(--warm-grey);text-align:center">Loading…</div>';
  var d = await apiFetch('/reports/activity?period='+period);
  if (!d) { el.innerHTML='<span style="color:#B33A47">Failed to load.</span>'; return; }
  var periodLabels = {'1d':'today','7d':'last 7 days','30d':'last 30 days','90d':'last 90 days','365d':'last 12 months'};
  var label = periodLabels[period]||period;
  var items = [
    ['New contacts',         d.new_contacts,         '👤'],
    ['New companies',        d.new_companies,         '🏢'],
    ['New pipeline entries', d.new_pipeline_entries,  '📋'],
    ['New orders',           d.new_orders,            '📦'],
    ['Emails received',      d.emails_inbound,        '📥'],
    ['Emails sent',          d.emails_outbound,       '📤'],
  ];
  el.innerHTML = '<div style="font-size:12px;color:var(--warm-grey);padding:0 0 16px">Since '+d.since+'</div>'
    + '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">'
    + items.map(function(it) {
        return '<div style="background:var(--bg);border-radius:10px;padding:16px 20px">'
          + '<div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);margin-bottom:6px">'+it[0]+'</div>'
          + '<div style="font-size:26px;font-weight:700;font-family:JetBrains Mono,monospace;color:var(--navy)">'+fmtNum(it[1])+'</div>'
          + '</div>';
      }).join('')
    + '</div>';
}

// ---- Brands ----'''

if old_marker in h:
    h = h.replace(old_marker, NEW_REPORT_JS)
    print('OK: Reports JS functions added')
else:
    print('NOT FOUND: Brands marker')

# 3f. Reorder admin cards alphabetically
# Current order: Users, Brands, Pipeline Statuses, Order Statuses, Sales Regions, Contact Tags, Countries
# Alpha order:   Brands, Contact Tags, Countries, Order Statuses, Pipeline Statuses, Sales Regions, Users

old_admin_body_start = '        <!-- Users — admin only -->'
old_admin_body_end   = '      </div>\n    </section>\n\n  </main>'

idx_s = h.find(old_admin_body_start)
idx_e = h.find(old_admin_body_end, idx_s) + len(old_admin_body_end)

NEW_ADMIN = '''        <!-- Brands -->
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

        <!-- Users — admin only -->
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

      </div>
    </section>

  </main>'''

h = h[:idx_s] + NEW_ADMIN + h[idx_e:]
print('OK: admin cards reordered alphabetically')

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved index.html.')
