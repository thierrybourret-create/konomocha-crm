with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

# Replace the entire Reports view section
old_reports_view_start = '    <!-- ===== REPORTS ===== -->'
old_reports_view_end   = '\n    <!-- ===== ADMIN ===== -->'
idx_s = h.find(old_reports_view_start)
idx_e = h.find(old_reports_view_end, idx_s)

NEW_REPORTS_VIEW = '''    <!-- ===== REPORTS ===== -->
    <section class="view" id="view-reports" data-screen-label="Reports">
      <div class="page-head">
        <div><h1 class="page-title">Reports</h1><div class="page-sub" id="reports-sub">Data quality and activity</div></div>
      </div>
      <div class="page-body">

        <!-- Contact Data Quality -->
        <div class="card" style="margin-bottom:16px;">
          <div class="card-head">
            <div><div class="card-title">Contact Data Quality</div><div class="card-sub">Completeness audit across all contact records</div></div>
            <button class="btn btn-secondary" onclick="downloadQualityCSV()" style="font-size:12px;padding:6px 12px">Download CSV</button>
          </div>
          <div class="card-body" style="padding:0">

            <!-- Filter bar -->
            <div style="display:flex;align-items:center;gap:8px;padding:14px 20px;border-bottom:1px solid var(--line);flex-wrap:wrap">
              <div style="display:flex;gap:4px;background:var(--bg);border-radius:8px;padding:3px">
                <button id="qf-all"          class="qf-btn qf-active" onclick="setQFilter('all')">All</button>
                <button id="qf-missing"      class="qf-btn"           onclick="setQFilter('missing')">Missing Fields</button>
                <button id="qf-complete"     class="qf-btn"           onclick="setQFilter('complete')">Complete</button>
                <button id="qf-wrong_region" class="qf-btn"           onclick="setQFilter('wrong_region')">Wrong Region</button>
              </div>
              <input id="q-search" placeholder="Search name, company, email…"
                style="border:1px solid var(--line);border-radius:8px;padding:7px 12px;font:inherit;font-size:13px;flex:1;min-width:180px"
                oninput="clearTimeout(window._qt);window._qt=setTimeout(loadQualityReport,400)"/>
            </div>

            <!-- Summary tiles -->
            <div style="display:flex;gap:0;border-bottom:1px solid var(--line)">
              <div class="q-tile" style="border-top:3px solid var(--logo-blue-dark)">
                <div class="q-tile-num" id="qt-total">—</div>
                <div class="q-tile-lbl">Total contacts</div>
              </div>
              <div class="q-tile" style="border-top:3px solid #B33A47">
                <div class="q-tile-num" id="qt-missing">—</div>
                <div class="q-tile-lbl">Missing fields</div>
              </div>
              <div class="q-tile" style="border-top:3px solid #22C55E">
                <div class="q-tile-num" id="qt-complete">—</div>
                <div class="q-tile-lbl">Fully complete</div>
              </div>
              <div class="q-tile" style="border-top:3px solid #D97706">
                <div class="q-tile-num" id="qt-region">—</div>
                <div class="q-tile-lbl">Wrong region</div>
              </div>
            </div>

            <!-- Row count -->
            <div style="padding:8px 20px;font-size:12px;color:var(--warm-grey);border-bottom:1px solid var(--line)" id="q-row-count"></div>

            <!-- Table -->
            <table class="data" id="q-table">
              <thead><tr>
                <th>Contact</th>
                <th style="width:160px">Score</th>
                <th>Missing Fields</th>
                <th>Country</th>
                <th>Sales Region</th>
                <th style="width:120px">Status</th>
              </tr></thead>
              <tbody id="q-tbody"><tr><td colspan="6" style="text-align:center;padding:40px;color:var(--warm-grey)">Loading…</td></tr></tbody>
            </table>

            <!-- Pagination -->
            <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 20px;border-top:1px solid var(--line)">
              <button class="btn btn-secondary" id="q-prev" onclick="qPage(-1)" style="font-size:12px;padding:5px 12px">← Previous</button>
              <span id="q-page-info" style="font-size:12px;color:var(--warm-grey)"></span>
              <button class="btn btn-secondary" id="q-next" onclick="qPage(1)"  style="font-size:12px;padding:5px 12px">Next →</button>
            </div>

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
    </section>'''

if idx_s != -1 and idx_e != -1:
    h = h[:idx_s] + NEW_REPORTS_VIEW + h[idx_e:]
    print('OK: Reports view replaced')
else:
    print('NOT FOUND: Reports view markers')

# Add CSS for quality report tiles and filter buttons (inside existing <style> tag)
old_style_end = '  /* ─── Responsive ─────────────────────────────────────────────────── */'
new_style_extra = '''  /* ─── Quality report ──────────────────────────────────────────────── */
  .q-tile { flex:1;padding:16px 20px;border-right:1px solid var(--line); }
  .q-tile:last-child { border-right:none; }
  .q-tile-num { font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:700;color:var(--navy);margin-bottom:2px; }
  .q-tile-lbl { font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey); }
  .qf-btn { padding:5px 12px;border:none;border-radius:6px;font:inherit;font-size:12px;cursor:pointer;background:transparent;color:var(--warm-grey); }
  .qf-btn.qf-active { background:#fff;color:var(--navy);font-weight:600;box-shadow:0 1px 3px rgba(0,0,0,.1); }
  .q-pill { display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500;border:1px solid #FCA5A5;background:#FEF2F2;color:#B33A47;margin:1px; }
  /* ─── Responsive ─────────────────────────────────────────────────── */'''
h = h.replace(old_style_end, new_style_extra)
print('OK: CSS added for quality report')

# Replace the loadReports JS function
old_reports_js_start = '// ---- Reports ----'
idx_rjs = h.find('// ---- Reports ----')
idx_rjs_end = h.find('\n// ---- Brands ----', idx_rjs)
old_reports_js = h[idx_rjs:idx_rjs_end]

NEW_REPORTS_JS = '''// ---- Reports ----
let qFilter = 'all', qCurrentPage = 1, qPerPage = 50;

async function loadReports() {
  var u = JSON.parse(localStorage.getItem('crm_user')||'{}');
  var ac = document.getElementById('reports-activity-card');
  if (ac) ac.style.display = (u.role==='admin') ? '' : 'none';
  await Promise.all([loadQualityReport(), u.role==='admin' ? loadActivityReport() : Promise.resolve()]);
}

function setQFilter(f) {
  qFilter = f; qCurrentPage = 1;
  ['all','missing','complete','wrong_region'].forEach(function(k) {
    var btn = document.getElementById('qf-'+k);
    if (btn) btn.classList.toggle('qf-active', k===f);
  });
  loadQualityReport();
}

function qPage(dir) {
  qCurrentPage = Math.max(1, qCurrentPage + dir);
  loadQualityReport();
}

async function loadQualityReport() {
  var tbody = document.getElementById('q-tbody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--warm-grey)">Loading…</td></tr>';
  var search = (document.getElementById('q-search')||{}).value || '';
  var p = new URLSearchParams({filter:qFilter, search:search, page:qCurrentPage, per_page:qPerPage});
  var d = await apiFetch('/reports/contact-quality?'+p);
  if (!d) { tbody.innerHTML='<tr><td colspan="6" style="text-align:center;padding:40px;color:#B33A47">Failed to load.</td></tr>'; return; }

  document.getElementById('qt-total').textContent   = fmtNum(d.total);
  document.getElementById('qt-missing').textContent = fmtNum(d.n_missing);
  document.getElementById('qt-complete').textContent= fmtNum(d.n_complete);
  document.getElementById('qt-region').textContent  = fmtNum(d.n_wrong_region);

  var showing = d.filtered_total;
  document.getElementById('q-row-count').textContent =
    fmtNum(Math.min(qCurrentPage*qPerPage, showing)) + ' of ' + fmtNum(showing) + ' contacts shown';

  var totalPages = Math.ceil(showing / qPerPage);
  document.getElementById('q-page-info').textContent = 'Page ' + qCurrentPage + ' of ' + (totalPages||1);
  var prev = document.getElementById('q-prev'), next = document.getElementById('q-next');
  if (prev) prev.disabled = qCurrentPage <= 1;
  if (next) next.disabled = qCurrentPage >= totalPages;

  if (!d.results.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--warm-grey)">No contacts match this filter.</td></tr>';
    return;
  }

  tbody.innerHTML = d.results.map(function(r) {
    var pct = r.score;
    var barColour = pct===100 ? '#22C55E' : pct>=60 ? '#76BCE0' : pct>=40 ? '#D97706' : '#B33A47';
    var bar = '<div style="display:flex;align-items:center;gap:8px">'
      + '<div style="flex:1;height:6px;border-radius:3px;background:var(--line);overflow:hidden">'
      + '<div style="height:100%;width:'+pct+'%;background:'+barColour+'"></div></div>'
      + '<span style="font-size:11px;font-family:JetBrains Mono,monospace;color:var(--warm-grey);white-space:nowrap">'+pct+'%</span></div>';
    var pills = r.missing.map(function(m){ return '<span class="q-pill">'+m+'</span>'; }).join('');
    var status = r.complete
      ? '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500;background:#F0FDF4;border:1px solid #86EFAC;color:#166534">Complete</span>'
      : '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500;background:#FEF2F2;border:1px solid #FCA5A5;color:#B33A47">Missing fields</span>';
    return '<tr onclick="showView(\'contacts\')" style="cursor:pointer">'
      + '<td class="contact-cell"><div class="nm">'+escHtml(r.name||'—')+'</div>'
      + (r.company?'<div class="co">'+escHtml(r.company)+'</div>':'')
      + (r.email?'<div class="co">'+escHtml(r.email)+'</div>':'')
      + '</td>'
      + '<td>'+bar+'</td>'
      + '<td>'+(pills||'<span style="color:var(--warm-grey);font-size:12px">—</span>')+'</td>'
      + '<td style="font-size:13px">'+(r.country||'<span style="color:var(--warm-grey)">—</span>')+'</td>'
      + '<td style="font-size:13px">'+(r.region||'<span style="color:'+(r.wrong_region?'#B33A47':'var(--warm-grey)')+'">'+(r.wrong_region?'⚠ Missing':'—')+'</span>')+'</td>'
      + '<td>'+status+'</td>'
      + '</tr>';
  }).join('');
}

function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

async function downloadQualityCSV() {
  var search = (document.getElementById('q-search')||{}).value || '';
  var p = new URLSearchParams({filter:qFilter, search:search});
  var token = localStorage.getItem('crm_token');
  var resp = await fetch('/api/reports/contact-quality-csv?'+p, {headers:{'Authorization':'Bearer '+token}});
  if (!resp.ok) { showToast('Export failed'); return; }
  var blob = await resp.blob();
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'contact_quality.csv'; a.click();
  showToast('CSV downloaded');
}

async function loadActivityReport() {
  var el = document.getElementById('reports-activity-body');
  if (!el) return;
  var sel = document.getElementById('reports-period');
  var period = sel ? sel.value : '30d';
  el.innerHTML = '<div style="padding:20px;color:var(--warm-grey);text-align:center">Loading…</div>';
  var d = await apiFetch('/reports/activity?period='+period);
  if (!d) { el.innerHTML='<span style="color:#B33A47">Failed to load.</span>'; return; }
  var items = [
    ['New Contacts',         d.new_contacts],
    ['New Companies',        d.new_companies],
    ['New Pipeline Entries', d.new_pipeline_entries],
    ['New Orders',           d.new_orders],
    ['Emails Received',      d.emails_inbound],
    ['Emails Sent',          d.emails_outbound],
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
}'''

if old_reports_js in h:
    h = h.replace(old_reports_js, NEW_REPORTS_JS)
    print('OK: Reports JS replaced')
else:
    print('NOT FOUND: old reports JS block — trying marker only')
    h = h.replace('// ---- Reports ----', NEW_REPORTS_JS, 1)
    print('OK: Reports JS replaced via marker')

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved index.html.')
