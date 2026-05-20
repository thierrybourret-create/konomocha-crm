with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

changes = []

# 1. Owner first name only in ownerAv
changes.append((
    "  const ini=(name||'?').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);\n  const bg=OWN_COLORS[name]||'#E5E7EB';\n  return `<div class=\"owner-cell\"><div class=\"avatar\" style=\"width:24px;height:24px;font-size:10px;background:${bg};\">${ini}</div>${name||'—'}</div>`;",
    "  const ini=(name||'?').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);\n  const bg=OWN_COLORS[name]||'#E5E7EB';\n  const first=(name||'—').split(' ')[0];\n  return `<div class=\"owner-cell\"><div class=\"avatar\" style=\"width:24px;height:24px;font-size:10px;background:${bg};\">${ini}</div>${first}</div>`;"
))

# 2. Owner first name in pipeline detail modal
changes.append((
    "      <tr><td style=\"padding:8px 0;color:var(--warm-grey)\">Owner</td><td>${e.owner_name||'—'}</td></tr>",
    "      <tr><td style=\"padding:8px 0;color:var(--warm-grey)\">Owner</td><td>${(e.owner_name||'—').split(' ')[0]}</td></tr>"
))

# 3. OWN_COLORS - key on first name only
changes.append((
    "const OWN_COLORS = { Thierry:'linear-gradient(135deg,#76BCE0,#5A9FC4)', Zeal:'#F3E2C0', Erna:'#E0D8EE' };",
    "const OWN_COLORS = { Thierry:'linear-gradient(135deg,#76BCE0,#5A9FC4)', Zeal:'#F3E2C0', Erna:'#E0D8EE' };\nfunction firstOf(name){ return (name||'').split(' ')[0]; }"
))

# 4. Admin cards: collapse all by default — add display:none to all card bodies
changes.append((
    '          <div id="admin-users-body">\n          <div class="card-body" style="padding:0">',
    '          <div id="admin-users-body" style="display:none">\n          <div class="card-body" style="padding:0">'
))
changes.append((
    '          <div id="admin-brands-body">\n          <div class="card-body" style="padding:0">',
    '          <div id="admin-brands-body" style="display:none">\n          <div class="card-body" style="padding:0">'
))
changes.append((
    '            <div id="admin-regions-body"><div style="padding:0 20px" id="admin-regions-list"></div></div>',
    '            <div id="admin-regions-body" style="display:none"><div style="padding:0 20px" id="admin-regions-list"></div></div>'
))
changes.append((
    '            <div id="admin-tags-body"><div style="padding:0 20px" id="admin-tags-list"></div></div>',
    '            <div id="admin-tags-body" style="display:none"><div style="padding:0 20px" id="admin-tags-list"></div></div>'
))
changes.append((
    '            <div id="admin-countries-body"><div style="padding:8px 20px;max-height:260px;overflow-y:auto" id="admin-countries-list"></div></div>',
    '            <div id="admin-countries-body" style="display:none"><div style="padding:8px 20px;max-height:260px;overflow-y:auto" id="admin-countries-list"></div></div>'
))

# 5. Change chevrons from ▼ to ▶ (collapsed state)
changes.append(('<span id="admin-users-chevron" style="color:var(--warm-grey);margin-left:8px">▼</span>', '<span id="admin-users-chevron" style="color:var(--warm-grey);margin-left:8px">▶</span>'))
changes.append(('<span id="admin-brands-chevron" style="color:var(--warm-grey);margin-left:8px">▼</span>', '<span id="admin-brands-chevron" style="color:var(--warm-grey);margin-left:8px">▶</span>'))
changes.append(('<span id="admin-regions-chevron" style="color:var(--warm-grey)">▼</span>', '<span id="admin-regions-chevron" style="color:var(--warm-grey)">▶</span>'))
changes.append(('<span id="admin-tags-chevron" style="color:var(--warm-grey)">▼</span>', '<span id="admin-tags-chevron" style="color:var(--warm-grey)">▶</span>'))
changes.append(('<span id="admin-countries-chevron" style="color:var(--warm-grey)">▼</span>', '<span id="admin-countries-chevron" style="color:var(--warm-grey)">▶</span>'))

# 6. Remove "Pricing Sent" from all hardcoded status lists in HTML
changes.append((
    "<option>Price List Sent</option>\n            <option>Pricing Sent</option><option>Quotation Sent</option>",
    "<option>Price List Sent</option><option>Quotation Sent</option>"
))

# 7. Add board grouping control and fix board sort — add a group-by selector near board button
# Also add "Sort by Owner" column header and sort by potential_value link
# These are handled in the JS section below

# 8. Users table — split name display into first/last in admin
changes.append((
    "      <td class=\"contact-cell\"><div class=\"nm\">${u.name}</div></td>",
    "      <td class=\"contact-cell\"><div class=\"nm\">${u.name.split(' ').slice(1).join(' ')||'—'}</div><div class=\"co\">${u.name.split(' ')[0]}</div></td>"
))

# 9. Add Owner sort header to pipeline table
changes.append((
    '                <th>Owner</th>\n                <th style="width: 36px;"></th>',
    "                <th onclick=\"sortPipeline('owner')\" style=\"cursor:pointer\">Owner <span id=\"sort-pipeline-owner\"></span></th>\n                <th style=\"width: 36px;\"></th>"
))

# 10. Add potential_value to pipeline sort icons + owner
changes.append((
    "  ['contact','brand','status','due_date'].forEach(function(k){var el=document.getElementById('sort-pipeline-'+k);if(el)el.textContent=pipelineSort===k?sortIcon(pipelineSortDir):'';});",
    "  ['contact','brand','status','due_date','owner','potential_value'].forEach(function(k){var el=document.getElementById('sort-pipeline-'+k);if(el)el.textContent=pipelineSort===k?sortIcon(pipelineSortDir):'';});"
))

# 11. Add potential_value sort header
changes.append((
    '                <th style="text-align:right;">Potential value</th>',
    "                <th onclick=\"sortPipeline('potential_value')\" style=\"text-align:right;cursor:pointer\">Potential value <span id=\"sort-pipeline-potential_value\"></span></th>"
))

for old, new in changes:
    if old not in h:
        print('NOT FOUND: ' + old[:80])
    else:
        h = h.replace(old, new)
        print('OK: ' + old[:80])

# 12. Add pipeline statuses card in admin (after the brands card, before the 3-column grid)
# Also add board grouping selector in pipeline page-actions
# Also add "Convert to Order" button in pipeline detail modal
# Also fix toggleSection to update chevron correctly
# Also fix board sort to respect current pipelineSort/Dir
# Also add getPipelineStatuses() helper
# Also update status lists in JS to use getPipelineStatuses()

# Add getPipelineStatuses to reference data section
old_ref = "const DEF_REGIONS   = ['Africa','Asia','Eastern Europe','Europe','India','Middle East','North America','Oceania','South America'];\n"
new_ref = ("const DEF_REGIONS   = ['Africa','Asia','Eastern Europe','Europe','India','Middle East','North America','Oceania','South America'];\n"
           "const DEF_PIPELINE_STATUSES = ['Awaiting Feedback','Awaiting Info','Awaiting Samples','Catalogue Sent','Closed / No Action','Deposit Paid','Form Completed','In Progress','On Hold','Order Placed','Price List Sent','Quotation Sent','Samples Delivered','Samples Requested','Samples Sent','Stalled'];\n")
if old_ref not in h:
    print('NOT FOUND: DEF_REGIONS')
else:
    h = h.replace(old_ref, new_ref)
    print('OK: added DEF_PIPELINE_STATUSES')

# Add getPipelineStatuses/savePipelineStatuses helpers after saveCountries
old_save = "function saveCountries(v) { localStorage.setItem('crm_countries', JSON.stringify(v)); }\n"
new_save = (old_save +
            "function getPipelineStatuses() { return JSON.parse(localStorage.getItem('crm_pipeline_statuses') || JSON.stringify(DEF_PIPELINE_STATUSES)); }\n"
            "function savePipelineStatuses(v) { localStorage.setItem('crm_pipeline_statuses', JSON.stringify(v)); }\n")
if old_save not in h:
    print('NOT FOUND: saveCountries')
else:
    h = h.replace(old_save, new_save)
    print('OK: added getPipelineStatuses')

# Fix toggleSection to update chevrons properly
old_toggle = "function toggleSection(id) {"
# Get the full function
idx = h.find("function toggleSection(id) {")
end = h.find("\n}", idx) + 2
old_toggle_full = h[idx:end]
new_toggle = """function toggleSection(id) {
  var el = document.getElementById(id);
  if (!el) return;
  var hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  var chevId = id.replace('-body', '-chevron');
  var chev = document.getElementById(chevId);
  if (chev) chev.textContent = hidden ? '▼' : '▶';
}"""
if old_toggle_full:
    h = h.replace(old_toggle_full, new_toggle)
    print('OK: toggleSection fixed')
else:
    print('NOT FOUND: toggleSection')

# Update the status lists in openNewDealModal to use getPipelineStatuses()
old_statuses_js = "  const statuses = ['Awaiting Feedback','Awaiting Info','Awaiting Samples','Cancelled','Catalogue Sent','Closed / No Action','Deposit Paid','Form Completed','In Progress','On Hold','Order Placed','Price List Sent','Pricing Sent','Quotation Sent','Samples Delivered','Samples Requested','Samples Sent','Stalled'];"
new_statuses_js = "  const statuses = getPipelineStatuses();"
if old_statuses_js not in h:
    print('NOT FOUND: openNewDealModal statuses list')
else:
    h = h.replace(old_statuses_js, new_statuses_js)
    print('OK: openNewDealModal uses getPipelineStatuses()')

# Update filter dropdown statuses to use getPipelineStatuses() — the static <option> list in the filter bar
# These are rendered at page load so they need to be populated dynamically
# Replace the static status filter options with a placeholder populated on page load
OLD_STATUS_OPTS = (
    '            <option value="">All statuses</option>\n'
    '            <option>Awaiting Feedback</option><option>Awaiting Info</option><option>Awaiting Samples</option>\n'
    '            <option>Cancelled</option><option>Catalogue Sent</option><option>Closed / No Action</option>\n'
    '            <option>Deposit Paid</option><option>Form Completed</option><option>In Progress</option>\n'
    '            <option>On Hold</option><option>Order Placed</option><option>Price List Sent</option>\n'
    '            <option>Pricing Sent</option><option>Quotation Sent</option><option>Samples Delivered</option>\n'
    '            <option>Samples Requested</option><option>Samples Sent</option><option>Stalled</option>'
)
NEW_STATUS_OPTS = '            <option value="">All statuses</option>'
if OLD_STATUS_OPTS not in h:
    print('NOT FOUND: static status filter options')
else:
    h = h.replace(OLD_STATUS_OPTS, NEW_STATUS_OPTS)
    print('OK: static status filter options replaced')

# Add pipeline statuses card in admin (before the 3-column grid section)
OLD_ADMIN_GRID = '        <!-- Reference data — 3 columns -->'
NEW_ADMIN_PIPELINE_STATUSES = '''        <!-- Pipeline Statuses -->
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

        <!-- Reference data — 3 columns -->'''
if OLD_ADMIN_GRID not in h:
    print('NOT FOUND: admin grid marker')
else:
    h = h.replace(OLD_ADMIN_GRID, NEW_ADMIN_PIPELINE_STATUSES)
    print('OK: Pipeline Statuses admin card added')

# Add board grouping selector next to board view button
OLD_BOARD_BTN_AREA = '          <button id="pipeline-board-btn" class="btn btn-secondary" onclick="toggleBoardView()">'
NEW_BOARD_BTN_AREA = ('          <select id="board-group-by" style="display:none;padding:7px 10px;font:inherit;font-size:13px;color:var(--navy);border:1px solid var(--line);border-radius:8px;background:var(--white);">'
                      '<option value="status">Group by Status</option>'
                      '<option value="brand">Group by Brand</option>'
                      '<option value="contact">Group by Company</option>'
                      '</select>\n'
                      '          <button id="pipeline-board-btn" class="btn btn-secondary" onclick="toggleBoardView()">')
if OLD_BOARD_BTN_AREA not in h:
    print('NOT FOUND: board btn area')
else:
    h = h.replace(OLD_BOARD_BTN_AREA, NEW_BOARD_BTN_AREA)
    print('OK: board grouping selector added')

# Add "Convert to Order" button in pipeline detail modal
OLD_MODAL_CLOSE = "  document.getElementById('modal').style.display = 'flex';\n}\n\n// ---- New Deal modal ----"
NEW_MODAL_CLOSE = ("  document.getElementById('modal-footer').innerHTML = "
                   "`<button class=\"btn btn-secondary\" onclick=\"document.getElementById('modal').style.display='none'\">Close</button>"
                   "<button class=\"btn btn-primary\" onclick=\"openConvertToOrderModal(${e.id})\">Convert to Order</button>`;\n"
                   "  document.getElementById('modal').style.display = 'flex';\n"
                   "}\n\n"
                   "// ---- New Deal modal ----")
if OLD_MODAL_CLOSE not in h:
    print('NOT FOUND: modal close / new deal marker')
else:
    h = h.replace(OLD_MODAL_CLOSE, NEW_MODAL_CLOSE)
    print('OK: Convert to Order button added')

# Fix renderRefLists to include statuses
old_render = "  renderList('admin-regions-list',  getRegions(),   'region');\n  renderList('admin-tags-list',     getTags(),      'tag');\n  renderList('admin-countries-list',getCountries(), 'country');"
new_render = ("  renderList('admin-regions-list',  getRegions(),   'region');\n"
              "  renderList('admin-tags-list',     getTags(),      'tag');\n"
              "  renderList('admin-countries-list',getCountries(), 'country');\n"
              "  renderList('admin-statuses-list', getPipelineStatuses(), 'status');")
if old_render not in h:
    print('NOT FOUND: renderRefLists body')
else:
    h = h.replace(old_render, new_render)
    print('OK: renderRefLists includes statuses')

# Fix addRefItem to handle status type
old_add = "  if (type==='country'){ const c=getCountries();if(!c.includes(val)){c.push(val);c.sort();saveCountries(c);} }\n  el.value=''; renderRefLists(); populateFilterDropdowns();"
new_add = ("  if (type==='country'){ const c=getCountries();if(!c.includes(val)){c.push(val);c.sort();saveCountries(c);} }\n"
           "  if (type==='status') { const s=getPipelineStatuses();if(!s.includes(val)){s.push(val);savePipelineStatuses(s);} }\n"
           "  el.value=''; renderRefLists(); populateFilterDropdowns();")
if old_add not in h:
    print('NOT FOUND: addRefItem country block')
else:
    h = h.replace(old_add, new_add)
    print('OK: addRefItem handles status')

# Fix removeRefItem to handle status type
old_remove = "  if (type==='country'){ const c=getCountries();c.splice(idx,1);saveCountries(c); }\n  renderRefLists(); populateFilterDropdowns();"
new_remove = ("  if (type==='country'){ const c=getCountries();c.splice(idx,1);saveCountries(c); }\n"
              "  if (type==='status') { const s=getPipelineStatuses();s.splice(idx,1);savePipelineStatuses(s); }\n"
              "  renderRefLists(); populateFilterDropdowns();")
if old_remove not in h:
    print('NOT FOUND: removeRefItem country block')
else:
    h = h.replace(old_remove, new_remove)
    print('OK: removeRefItem handles status')

# Fix board view to respect pipelineSort and support groupBy
# Replace the renderBoard function
old_board_fn_start = "async function renderBoard() {"
idx = h.find("async function renderBoard() {")
end = h.find("\n}\n", idx) + 3
old_board_fn = h[idx:end]

new_board_fn = """async function renderBoard() {
  var board = document.getElementById('pipeline-board');
  board.innerHTML = '<div style="padding:40px;color:var(--warm-grey)">Loading...</div>';
  var p = new URLSearchParams({ per_page:500, sort_by:pipelineSort, sort_dir:pipelineSortDir });
  if (pipelineFilters.search)   p.set('search',   pipelineFilters.search);
  if (pipelineFilters.brand_id) p.set('brand_id', pipelineFilters.brand_id);
  if (pipelineFilters.owner_id) p.set('owner_id', pipelineFilters.owner_id);
  if (pipelineFilters.status)   p.set('status',   pipelineFilters.status);
  var d = await apiFetch('/pipeline?' + p);
  if (!d) return;
  pipelineData = d.results;
  var groupBy = (document.getElementById('board-group-by')||{}).value || 'status';
  var colKeys = [], getKey;
  if (groupBy === 'status') {
    colKeys = getPipelineStatuses();
    getKey = function(e){ return e.status; };
  } else if (groupBy === 'brand') {
    getKey = function(e){ return e.brand_name||'No Brand'; };
    colKeys = [...new Set(d.results.map(getKey))].sort();
  } else {
    getKey = function(e){ return e.contact_company||e.contact_name||'Unknown'; };
    colKeys = [...new Set(d.results.map(getKey))].sort();
  }
  var byKey = {};
  colKeys.forEach(function(k){ byKey[k] = []; });
  d.results.forEach(function(e){
    var k = getKey(e);
    if (!byKey[k]) byKey[k] = [];
    byKey[k].push(e);
  });
  var cols = colKeys.filter(function(k){ return byKey[k] && byKey[k].length > 0; });
  board.innerHTML = cols.map(function(s) {
    var cards = byKey[s];
    var total = cards.reduce(function(sum,c){ return sum+(c.potential_value||0); },0);
    return '<div style="flex:0 0 220px;background:var(--bg);border-radius:10px;overflow:hidden;margin-right:12px">'
      + '<div style="padding:10px 12px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:8px">'
      + (groupBy==='status' ? '<span class="pill ' + statusClass(s) + '">' + s + '</span>' : '<b style="font-size:13px;color:var(--navy)">' + s + '</b>')
      + '<span style="font-size:11px;color:var(--warm-grey);white-space:nowrap">' + cards.length + ' &middot; ' + fmtShort(total) + '</span>'
      + '</div>'
      + '<div style="padding:8px;max-height:calc(100vh - 280px);overflow-y:auto">'
      + cards.map(function(e) {
          return '<div onclick="openPipelineDetail(' + e.id + ')" style="background:var(--white);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-bottom:6px;cursor:pointer">'
            + '<div style="font-weight:600;color:var(--navy);font-size:13px;margin-bottom:2px">' + (e.contact_company||e.contact_name||'—') + '</div>'
            + '<div style="font-size:11px;color:var(--warm-grey);margin-bottom:4px">' + (e.brand_name||'') + (groupBy!=='status'?' · <span class="pill ' + statusClass(e.status) + '" style="font-size:10px">' + e.status + '</span>':'') + '</div>'
            + '<div style="display:flex;justify-content:space-between;align-items:center">'
            + '<span style="font-size:12px;font-weight:600;color:var(--logo-blue-dark)">USD ' + fmtNum(e.potential_value||0) + '</span>'
            + ownerAv(e.owner_name)
            + '</div></div>';
        }).join('')
      + '</div></div>';
  }).join('');
}
"""

if old_board_fn:
    h = h.replace(old_board_fn, new_board_fn)
    print('OK: renderBoard updated with groupBy + sort')
else:
    print('NOT FOUND: renderBoard function')

# Show/hide board-group-by selector with board toggle
old_toggle_board = "  if (btn) btn.textContent = boardViewActive ? 'Table view' : 'Board view';\n  document.getElementById('pipeline-table-wrap').style.display = boardViewActive ? 'none' : '';\n  var board = document.getElementById('pipeline-board');\n  if (board) board.style.display = boardViewActive ? 'flex' : 'none';\n  if (boardViewActive) renderBoard();"
new_toggle_board = ("  if (btn) btn.textContent = boardViewActive ? 'Table view' : 'Board view';\n"
                    "  var gbSel = document.getElementById('board-group-by');\n"
                    "  if (gbSel) gbSel.style.display = boardViewActive ? '' : 'none';\n"
                    "  document.getElementById('pipeline-table-wrap').style.display = boardViewActive ? 'none' : '';\n"
                    "  var board = document.getElementById('pipeline-board');\n"
                    "  if (board) board.style.display = boardViewActive ? 'flex' : 'none';\n"
                    "  if (boardViewActive) renderBoard();")
if old_toggle_board not in h:
    print('NOT FOUND: toggleBoardView body')
else:
    h = h.replace(old_toggle_board, new_toggle_board)
    print('OK: toggleBoardView shows groupBy selector')

# Add board-group-by onchange to re-render
old_group_sel = ('<select id="board-group-by" style="display:none;padding:7px 10px;font:inherit;font-size:13px;color:var(--navy);border:1px solid var(--line);border-radius:8px;background:var(--white);">'
                 '<option value="status">Group by Status</option>'
                 '<option value="brand">Group by Brand</option>'
                 '<option value="contact">Group by Company</option>'
                 '</select>')
new_group_sel = ('<select id="board-group-by" onchange="if(boardViewActive)renderBoard()" style="display:none;padding:7px 10px;font:inherit;font-size:13px;color:var(--navy);border:1px solid var(--line);border-radius:8px;background:var(--white);">'
                 '<option value="status">Group by Status</option>'
                 '<option value="brand">Group by Brand</option>'
                 '<option value="contact">Group by Company</option>'
                 '</select>')
if old_group_sel not in h:
    print('NOT FOUND: board-group-by select')
else:
    h = h.replace(old_group_sel, new_group_sel)
    print('OK: board-group-by has onchange')

# Populate status filter dropdown dynamically in populateFilterDropdowns
old_populate = "function populateFilterDropdowns() {"
idx2 = h.find("function populateFilterDropdowns() {")
end2 = h.find("\n}", idx2) + 2
old_populate_fn = h[idx2:end2]
if old_populate_fn and 'filter-status' in old_populate_fn:
    # Already populates filter-status
    print('OK: populateFilterDropdowns already handles status')
else:
    # Need to add status population
    # Find where filter-brand is populated and add status after
    idx3 = h.find("function populateFilterDropdowns() {")
    end3 = h.find("\n}", idx3) + 2
    old_pop = h[idx3:end3]
    new_pop = old_pop.rstrip('}\n') + """
  var fs = document.getElementById('filter-status');
  if (fs) {
    var curStatus = fs.value;
    fs.innerHTML = '<option value="">All statuses</option>' + getPipelineStatuses().map(function(s){ return '<option' + (s===curStatus?' selected':'') + '>' + s + '</option>'; }).join('');
  }
}"""
    h = h.replace(old_pop, new_pop)
    print('OK: populateFilterDropdowns populates status dropdown')

# Add openConvertToOrderModal function before saveNewDeal
OLD_CONVERT = "async function saveNewDeal(e) {"
CONVERT_FN = """async function openConvertToOrderModal(pipelineId) {
  const e = pipelineData.find(x=>x.id===pipelineId); if(!e) return;
  document.getElementById('modal-title').innerHTML = 'Convert to Order';
  document.getElementById('modal-footer').innerHTML = '';
  document.getElementById('modal-body').innerHTML = `
    <form id="convert-order-form" onsubmit="saveConvertedOrder(event,${pipelineId})">
      <div style="background:var(--logo-blue-pale);border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px">
        <b>${e.contact_company||e.contact_name||'—'}</b> · ${e.brand_name||'—'}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Order Date *</label>
          <input name="order_date" type="date" required value="${new Date().toISOString().slice(0,10)}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Order Value (USD) *</label>
          <input name="order_value" type="number" min="0" step="0.01" required placeholder="0" value="${e.potential_value||''}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Gross Commission % *</label>
          <input name="gross_commission_rate" type="number" min="0" max="100" step="0.1" required placeholder="0" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Testing Cost Deduction</label>
          <input name="testing_cost_deduction" type="number" min="0" step="0.01" placeholder="0" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div id="co-error" style="display:none;color:#B33A47;font-size:13px;margin-bottom:12px;padding:10px;background:#FAE3E5;border-radius:8px"></div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" onclick="document.getElementById('modal').style.display='none'" class="btn btn-secondary">Cancel</button>
        <button type="submit" class="btn btn-primary">Create Order</button>
      </div>
    </form>`;
  document.getElementById('modal').style.display = 'flex';
}

async function saveConvertedOrder(ev, pipelineId) {
  ev.preventDefault();
  const e = pipelineData.find(x=>x.id===pipelineId); if(!e) return;
  const fd = new FormData(ev.target);
  const orderValue = parseFloat(fd.get('order_value'))||0;
  const commRate = parseFloat(fd.get('gross_commission_rate'))||0;
  const testCost = parseFloat(fd.get('testing_cost_deduction'))||0;
  const netComm = (orderValue * commRate / 100) - testCost;
  const payload = {
    contact_id: e.contact_id,
    brand_id: e.brand_id,
    order_date: fd.get('order_date'),
    order_value: orderValue,
    currency: 'USD',
    gross_commission_rate: commRate,
    testing_cost_deduction: testCost,
    net_commission: netComm,
    status: 'Confirmed',
    notes: 'Converted from pipeline deal #' + pipelineId,
  };
  const btn = ev.target.querySelector('[type=submit]'); btn.textContent='Saving…'; btn.disabled=true;
  const result = await apiFetch('/orders', {method:'POST', body:JSON.stringify(payload)});
  if (result) {
    document.getElementById('modal').style.display='none';
    showToast('Order created successfully');
    loadPipeline();
  } else {
    document.getElementById('co-error').textContent='Failed to create order.';
    document.getElementById('co-error').style.display='block';
    btn.textContent='Create Order'; btn.disabled=false;
  }
}

"""
if OLD_CONVERT not in h:
    print('NOT FOUND: saveNewDeal marker for convert fn')
else:
    h = h.replace(OLD_CONVERT, CONVERT_FN + OLD_CONVERT)
    print('OK: openConvertToOrderModal added')

# Add showToast if not present
if 'function showToast' not in h:
    old_sort_icon = "function sortIcon(dir) { return dir==='asc' ? ' ▲' : ' ▼'; }"
    new_sort_icon = ("function sortIcon(dir) { return dir==='asc' ? ' ▲' : ' ▼'; }\n"
                     "function showToast(msg) {\n"
                     "  var t=document.createElement('div');\n"
                     "  t.style.cssText='position:fixed;bottom:24px;right:24px;background:var(--navy);color:#fff;padding:12px 20px;border-radius:8px;font-size:13px;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,.2)';\n"
                     "  t.textContent=msg; document.body.appendChild(t);\n"
                     "  setTimeout(function(){t.remove();},3000);\n"
                     "}")
    if old_sort_icon not in h:
        print('NOT FOUND: sortIcon for toast')
    else:
        h = h.replace(old_sort_icon, new_sort_icon)
        print('OK: showToast added')

# Add modal-footer div to the modal (needed for Convert to Order button)
old_modal_inner = '<div id="modal-body"></div>'
if old_modal_inner in h:
    h = h.replace(old_modal_inner, '<div id="modal-body"></div>\n      <div id="modal-footer" style="display:flex;gap:8px;justify-content:flex-end;padding:16px 24px 0;margin-top:8px;border-top:1px solid var(--line)"></div>')
    print('OK: modal-footer added')
else:
    print('NOT FOUND: modal-body div')

# Add owner sort to pipeline backend — update sort_col map in pipeline.py (already handled)
# Add owner to sort_col
with open('/home/thierry/konomocha-crm/app/routers/pipeline.py', encoding='utf-8') as f:
    py = f.read()
if '"owner": User.name' not in py:
    py = py.replace(
        '"potential_value": PipelineEntry.potential_value,\n    }.get(sort_by, PipelineEntry.updated_at)',
        '"potential_value": PipelineEntry.potential_value,\n        "owner": User.name,\n    }.get(sort_by, PipelineEntry.updated_at)'
    )
    with open('/home/thierry/konomocha-crm/app/routers/pipeline.py', 'w', encoding='utf-8') as f:
        f.write(py)
    print('OK: owner sort added to pipeline.py')
else:
    print('OK: owner sort already in pipeline.py')

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved index.html.')
