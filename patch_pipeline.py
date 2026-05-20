with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

changes = []

changes.append((
    "function fmtShort(n) {",
    "function fmtNum(n) { return Number(n||0).toLocaleString(); }\nfunction fmtShort(n) {"
))

changes.append((
    'function fmtDate(d) {\n  if (!d) return \'<span style="color:var(--warm-grey-light)">—</span>\';\n  const dt = new Date(d), today = new Date(); today.setHours(0,0,0,0);\n  const diff = Math.floor((dt-today)/86400000);\n  const lbl = dt.toLocaleDateString(\'en-GB\',{day:\'numeric\',month:\'short\'});\n  if (diff<0) return `<span style="color:#B33A47;font-weight:600">${Math.abs(diff)}d overdue</span>`;\n  if (diff===0) return `<span style="color:#8A5A00;font-weight:600">Today</span>`;\n  return lbl;\n}',
    'function fmtDate(d) {\n  if (!d) return \'<span style="color:var(--warm-grey-light)">—</span>\';\n  const dt = new Date(d + \'T00:00:00\'), today = new Date(); today.setHours(0,0,0,0);\n  const diff = Math.floor((dt-today)/86400000);\n  const mn = [\'Jan\',\'Feb\',\'Mar\',\'Apr\',\'May\',\'Jun\',\'Jul\',\'Aug\',\'Sep\',\'Oct\',\'Nov\',\'Dec\'];\n  const lbl = String(dt.getDate()).padStart(2,\'0\') + \'/\' + mn[dt.getMonth()] + \'/\' + dt.getFullYear();\n  if (diff<0) return \'<span style="color:#B33A47;font-weight:600">\' + lbl + \'</span>\';\n  if (diff===0) return \'<span style="color:#8A5A00;font-weight:600">\' + lbl + \'</span>\';\n  return lbl;\n}'
))

changes.append((
    '<div class="page-sub">128 open deals &middot; USD 1.08M weighted value &middot; Updated 2 minutes ago</div>',
    '<div class="page-sub" id="pipeline-sub">Loading...</div>'
))

ADD_DEAL_BTN = (
    '          <button class="btn btn-primary" onclick="openNewDealModal()">\n'
    '            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>\n'
    '            Add deal\n'
    '          </button>'
)
changes.append((ADD_DEAL_BTN, ''))

BOARD_BTN_OLD = (
    '          <button class="btn btn-secondary">\n'
    '            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>\n'
    '            Board view\n'
    '          </button>'
)
BOARD_BTN_NEW = (
    '          <button id="pipeline-board-btn" class="btn btn-secondary" onclick="toggleBoardView()">\n'
    '            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>\n'
    '            Board view\n'
    '          </button>'
)
changes.append((BOARD_BTN_OLD, BOARD_BTN_NEW))

changes.append((
    '        <!-- Pipeline table -->\n        <div class="table-wrap">',
    '        <!-- Pipeline table -->\n        <div id="pipeline-table-wrap" class="table-wrap">'
))

changes.append((
    '        <!-- Status legend -->',
    '        <div id="pipeline-board" style="display:none;overflow-x:auto;padding:8px 0 16px;flex-wrap:nowrap;align-items:flex-start"></div>\n        <!-- Status legend -->'
))

TH_OLD = (
    '                <th class="cell-checkbox"><span class="check"></span></th>\n'
    '                <th>Contact / Company</th>\n'
    '                <th>Brand</th>\n'
    '                <th>Status</th>\n'
    '                <th style="text-align: right;">Potential value <svg class="sort-ico" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>\n'
    '                <th>Next action</th>\n'
    '                <th>Due date <svg class="sort-ico" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>\n'
    '                <th>Owner</th>\n'
    '                <th style="width: 36px;"></th>'
)
TH_NEW = (
    '                <th class="cell-checkbox"><span class="check"></span></th>\n'
    "                <th onclick=\"sortPipeline('contact')\" style=\"cursor:pointer\">Company / Contact <span id=\"sort-pipeline-contact\"></span></th>\n"
    "                <th onclick=\"sortPipeline('brand')\" style=\"cursor:pointer\">Brand <span id=\"sort-pipeline-brand\"></span></th>\n"
    "                <th onclick=\"sortPipeline('status')\" style=\"cursor:pointer\">Status <span id=\"sort-pipeline-status\"></span></th>\n"
    '                <th style="text-align:right;">Potential value</th>\n'
    '                <th>Next action</th>\n'
    "                <th onclick=\"sortPipeline('due_date')\" style=\"cursor:pointer\">FOB Date <span id=\"sort-pipeline-due_date\"></span></th>\n"
    '                <th>Owner</th>\n'
    '                <th style="width: 36px;"></th>'
)
changes.append((TH_OLD, TH_NEW))

changes.append((
    "      <td class=\"contact-cell\"><div class=\"nm\">${e.contact_name||'—'}</div><div class=\"co\">${e.contact_company||''}</div></td>",
    "      <td class=\"contact-cell\"><div class=\"nm\">${e.contact_company||e.contact_name||'—'}</div><div class=\"co\">${e.contact_company?e.contact_name||'':''}</div></td>"
))

changes.append((
    "      <tr><td style=\"padding:8px 0;color:var(--warm-grey)\">Due Date</td><td>${e.due_date||'—'}</td></tr>",
    "      <tr><td style=\"padding:8px 0;color:var(--warm-grey)\">FOB Date</td><td>${fmtDate(e.due_date)}</td></tr>"
))

changes.append((
    "  document.getElementById('modal-title').innerHTML = `${e.contact_name||''} — ${e.brand_name||''}`;",
    "  document.getElementById('modal-title').innerHTML = `${e.contact_company||e.contact_name||''} — ${e.brand_name||''}`;"
))

changes.append((
    ">Due Date</label>\n          <input name=\"due_date\" type=\"date\"",
    ">FOB Date</label>\n          <input name=\"due_date\" type=\"date\""
))

changes.append((
    "document.getElementById('contacts-meta').textContent = d.total + ' contacts';",
    "document.getElementById('contacts-meta').textContent = fmtNum(d.total) + ' contacts';"
))

changes.append((
    "document.getElementById('companies-meta').textContent = d.total + ' companies';",
    "document.getElementById('companies-meta').textContent = fmtNum(d.total) + ' companies';"
))

changes.append((
    "let pipelinePage=1, pipelineData=[], pipelineFilters={search:'',brand_id:'',owner_id:'',status:''};",
    "let pipelinePage=1, pipelineData=[], pipelineFilters={search:'',brand_id:'',owner_id:'',status:''};\nlet pipelineSort='updated_at', pipelineSortDir='desc';"
))

changes.append((
    "  const p = new URLSearchParams({ page:pipelinePage, per_page:50 });",
    "  const p = new URLSearchParams({ page:pipelinePage, per_page:50, sort_by:pipelineSort, sort_dir:pipelineSortDir });"
))

changes.append((
    "  document.getElementById('pipeline-meta').innerHTML = `Showing <b>${d.results.length}</b> of <b>${d.total}</b> deals`;",
    "  document.getElementById('pipeline-meta').innerHTML = `Showing <b>${fmtNum(d.results.length)}</b> of <b>${fmtNum(d.total)}</b> deals`;\n"
    "  const psub = document.getElementById('pipeline-sub');\n"
    "  if (psub) psub.innerHTML = fmtNum(d.total) + ' open deals &middot; USD ' + fmtShort(d.total_value||0) + ' total value';\n"
    "  ['contact','brand','status','due_date'].forEach(function(k){var el=document.getElementById('sort-pipeline-'+k);if(el)el.textContent=pipelineSort===k?sortIcon(pipelineSortDir):'';});"
))

for old, new in changes:
    if old not in h:
        print('NOT FOUND: ' + old[:70])
    else:
        h = h.replace(old, new)
        print('OK: ' + old[:70])

NEW_FUNCS = """
function sortPipeline(col) {
  if (pipelineSort===col) pipelineSortDir = pipelineSortDir==='asc'?'desc':'asc';
  else { pipelineSort=col; pipelineSortDir='asc'; }
  pipelinePage=1; loadPipeline();
}

let boardViewActive = false;
function toggleBoardView() {
  boardViewActive = !boardViewActive;
  var btn = document.getElementById('pipeline-board-btn');
  if (btn) btn.textContent = boardViewActive ? 'Table view' : 'Board view';
  document.getElementById('pipeline-table-wrap').style.display = boardViewActive ? 'none' : '';
  var board = document.getElementById('pipeline-board');
  if (board) board.style.display = boardViewActive ? 'flex' : 'none';
  if (boardViewActive) renderBoard();
}

async function renderBoard() {
  var board = document.getElementById('pipeline-board');
  board.innerHTML = '<div style="padding:40px;color:var(--warm-grey)">Loading...</div>';
  var d = await apiFetch('/pipeline?per_page=500');
  if (!d) return;
  pipelineData = d.results;
  var statuses = ['In Progress','Awaiting Feedback','Awaiting Info','Awaiting Samples','Catalogue Sent','Price List Sent','Pricing Sent','Quotation Sent','Samples Requested','Samples Sent','Samples Delivered','Form Completed','Deposit Paid','Order Placed','On Hold','Stalled','Closed / No Action','Cancelled'];
  var byStatus = {};
  statuses.forEach(function(s){ byStatus[s] = []; });
  d.results.forEach(function(e){ if(byStatus[e.status]!==undefined) byStatus[e.status].push(e); });
  var cols = statuses.filter(function(s){ return byStatus[s].length > 0; });
  board.innerHTML = cols.map(function(s) {
    var cards = byStatus[s];
    var total = cards.reduce(function(sum,c){ return sum+(c.potential_value||0); },0);
    return '<div style="flex:0 0 220px;background:var(--bg);border-radius:10px;overflow:hidden;margin-right:12px">'
      + '<div style="padding:10px 12px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:8px">'
      + '<span class="pill ' + statusClass(s) + '">' + s + '</span>'
      + '<span style="font-size:11px;color:var(--warm-grey);white-space:nowrap">' + cards.length + ' &middot; ' + fmtShort(total) + '</span>'
      + '</div>'
      + '<div style="padding:8px;max-height:calc(100vh - 280px);overflow-y:auto">'
      + cards.map(function(e) {
          return '<div onclick="openPipelineDetail(' + e.id + ')" style="background:var(--white);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-bottom:6px;cursor:pointer">'
            + '<div style="font-weight:600;color:var(--navy);font-size:13px;margin-bottom:2px">' + (e.contact_company||e.contact_name||'—') + '</div>'
            + '<div style="font-size:11px;color:var(--warm-grey);margin-bottom:6px">' + (e.brand_name||'') + '</div>'
            + '<div style="display:flex;justify-content:space-between;align-items:center">'
            + '<span style="font-size:12px;font-weight:600;color:var(--logo-blue-dark)">USD ' + fmtNum(e.potential_value||0) + '</span>'
            + ownerAv(e.owner_name)
            + '</div></div>';
        }).join('')
      + '</div></div>';
  }).join('');
}

"""

needle = "// ---- New Deal modal ----"
if needle not in h:
    print('NOT FOUND: new deal modal marker')
else:
    h = h.replace(needle, NEW_FUNCS + needle, 1)
    print('OK: board/sort functions inserted')

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved.')
