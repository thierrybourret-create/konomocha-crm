with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

changes = []

# 1. Fix sidebar count badges to use fmtNum (currently set without formatting)
changes.append((
    "  const sc = document.getElementById('sb-count-contacts'); if(sc) sc.textContent = d.total;",
    "  const sc = document.getElementById('sb-count-contacts'); if(sc) sc.textContent = fmtNum(d.total);"
))
changes.append((
    "  const sc = document.getElementById('sb-count-companies'); if(sc) sc.textContent = d.total;",
    "  const sc = document.getElementById('sb-count-companies'); if(sc) sc.textContent = fmtNum(d.total);"
))
changes.append((
    "  const sc = document.getElementById('sb-count-pipeline'); if(sc) sc.textContent=d.total;",
    "  const sc = document.getElementById('sb-count-pipeline'); if(sc) sc.textContent=fmtNum(d.total);"
))
changes.append((
    "  const sc = document.getElementById('sb-count-orders'); if(sc) sc.textContent=d.total;",
    "  const sc = document.getElementById('sb-count-orders'); if(sc) sc.textContent=fmtNum(d.total);"
))

# 2. Remove group-by select from HTML
changes.append((
    '<select id="board-group-by" onchange="if(boardViewActive)renderBoard()" style="display:none;padding:7px 10px;font:inherit;font-size:13px;color:var(--navy);border:1px solid var(--line);border-radius:8px;background:var(--white);"><option value="status">Group by Status</option><option value="brand">Group by Brand</option><option value="contact">Group by Company</option></select>\n          ',
    ''
))

# 3. Remove group-by selector show/hide from toggleBoardView
changes.append((
    "  var gbSel = document.getElementById('board-group-by');\n"
    "  if (gbSel) gbSel.style.display = boardViewActive ? '' : 'none';\n",
    ''
))

# 4. Fix static status options that weren't replaced before (actual content in current file)
OLD_STATUS_STATIC = (
    '            <option value="">All statuses</option>\n'
    '            <option>Awaiting Feedback</option><option>Awaiting Info</option><option>Awaiting Samples</option>\n'
    '            <option>Cancelled</option><option>Catalogue Sent</option><option>Closed / No Action</option>\n'
    '            <option>Deposit Paid</option><option>Form Completed</option><option>In Progress</option>\n'
    '            <option>On Hold</option><option>Order Placed</option><option>Price List Sent</option><option>Quotation Sent</option><option>Samples Delivered</option>\n'
    '            <option>Samples Requested</option><option>Samples Sent</option><option>Stalled</option>'
)
changes.append((OLD_STATUS_STATIC, '            <option value="">All statuses</option>'))

# 5. Add onclick to Export CSV button in pipeline
changes.append((
    '          <button class="btn btn-secondary">\n'
    '            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>\n'
    '            Export CSV\n'
    '          </button>',
    '          <button class="btn btn-secondary" onclick="exportPipeline()">\n'
    '            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>\n'
    '            Export CSV\n'
    '          </button>'
))

# 6. Add board re-render at end of loadPipeline (before closing brace of the function)
# Find end of loadPipeline: the tbody.innerHTML line ends it
changes.append((
    "      <td><button class=\"more-btn\" onclick=\"event.stopPropagation();openPipelineDetail(${e.id})\">\n"
    "        <svg width=\"16\" height=\"16\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><circle cx=\"12\" cy=\"12\" r=\"1\"></circle><circle cx=\"19\" cy=\"12\" r=\"1\"></circle><circle cx=\"5\" cy=\"12\" r=\"1\"></circle></svg>\n"
    "      </button></td>\n"
    "    </tr>`).join('');\n"
    "}",
    "      <td><button class=\"more-btn\" onclick=\"event.stopPropagation();openPipelineDetail(${e.id})\">\n"
    "        <svg width=\"16\" height=\"16\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\"><circle cx=\"12\" cy=\"12\" r=\"1\"></circle><circle cx=\"19\" cy=\"12\" r=\"1\"></circle><circle cx=\"5\" cy=\"12\" r=\"1\"></circle></svg>\n"
    "      </button></td>\n"
    "    </tr>`).join('');\n"
    "  if (boardViewActive) renderBoard();\n"
    "}"
))

for old, new in changes:
    if old not in h:
        print('NOT FOUND: ' + repr(old[:70]))
    else:
        h = h.replace(old, new)
        print('OK: ' + old[:60].replace('\n','\\n'))

# 7. Add exportPipeline function (after sortPipeline)
old_sort_fn = "function sortPipeline(col) {\n  if (pipelineSort===col) pipelineSortDir = pipelineSortDir==='asc'?'desc':'asc';\n  else { pipelineSort=col; pipelineSortDir='asc'; }\n  pipelinePage=1; loadPipeline();\n}"
new_sort_fn = (
    old_sort_fn +
    "\n\nasync function exportPipeline() {\n"
    "  const p = new URLSearchParams({ per_page:9999, sort_by:pipelineSort, sort_dir:pipelineSortDir });\n"
    "  if (pipelineFilters.search)   p.set('search',   pipelineFilters.search);\n"
    "  if (pipelineFilters.brand_id) p.set('brand_id', pipelineFilters.brand_id);\n"
    "  if (pipelineFilters.owner_id) p.set('owner_id', pipelineFilters.owner_id);\n"
    "  if (pipelineFilters.status)   p.set('status',   pipelineFilters.status);\n"
    "  const d = await apiFetch('/pipeline?'+p);\n"
    "  if (!d || !d.results.length) { showToast('No data to export'); return; }\n"
    "  const cols = ['Company','Contact','Brand','Status','Potential Value','Next Action','FOB Date','Owner','Notes'];\n"
    "  const rows = d.results.map(e => [\n"
    "    e.contact_company||'', e.contact_name||'', e.brand_name||'', e.status||'',\n"
    "    e.potential_value||0, e.next_action||'', e.due_date||'', e.owner_name||'', (e.notes||'').replace(/,/g,' ')\n"
    "  ]);\n"
    "  const csv = [cols, ...rows].map(r => r.map(v => '\"'+String(v).replace(/\"/g,'\"\"')+'\"').join(',')).join('\\n');\n"
    "  const a = document.createElement('a');\n"
    "  a.href = URL.createObjectURL(new Blob([csv],{type:'text/csv'}));\n"
    "  a.download = 'pipeline_export.csv'; a.click();\n"
    "  showToast('Exported ' + d.results.length + ' deals');\n"
    "}"
)
if old_sort_fn not in h:
    print('NOT FOUND: sortPipeline function')
else:
    h = h.replace(old_sort_fn, new_sort_fn)
    print('OK: exportPipeline added')

# 8. Add DEF_ORDER_STATUSES and getOrderStatuses/saveOrderStatuses
old_def_pipeline = "const DEF_PIPELINE_STATUSES = "
idx = h.find(old_def_pipeline)
end = h.find('\n', idx) + 1
old_line = h[idx:end]
new_line = (old_line +
    "const DEF_ORDER_STATUSES = ['PO Received','PI Confirmed','Deposit Paid','Shipped','Payment Received','Cancelled'];\n")
if old_def_pipeline not in h:
    print('NOT FOUND: DEF_PIPELINE_STATUSES')
else:
    h = h.replace(old_line, new_line)
    print('OK: DEF_ORDER_STATUSES added')

old_save_pipeline = "function savePipelineStatuses(v) { localStorage.setItem('crm_pipeline_statuses', JSON.stringify(v)); }\n"
new_save_pipeline = (old_save_pipeline +
    "function getOrderStatuses() { return JSON.parse(localStorage.getItem('crm_order_statuses') || JSON.stringify(DEF_ORDER_STATUSES)); }\n"
    "function saveOrderStatuses(v) { localStorage.setItem('crm_order_statuses', JSON.stringify(v)); }\n")
if old_save_pipeline not in h:
    print('NOT FOUND: savePipelineStatuses')
else:
    h = h.replace(old_save_pipeline, new_save_pipeline)
    print('OK: getOrderStatuses/saveOrderStatuses added')

# 9. Add Order Statuses admin card (after Pipeline Statuses card)
old_ref_grid = '        <!-- Reference data — 3 columns -->'
new_order_card = '''        <!-- Order Statuses -->
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

        <!-- Reference data — 3 columns -->'''
if old_ref_grid not in h:
    print('NOT FOUND: reference data grid marker')
else:
    h = h.replace(old_ref_grid, new_order_card)
    print('OK: Order Statuses admin card added')

# 10. Wire order statuses into renderRefLists
old_render = "  renderList('admin-statuses-list', getPipelineStatuses(), 'status');"
new_render = (
    "  renderList('admin-statuses-list', getPipelineStatuses(), 'status');\n"
    "  renderList('admin-order-statuses-list', getOrderStatuses(), 'order_status');"
)
if old_render not in h:
    print('NOT FOUND: renderRefLists statuses line')
else:
    h = h.replace(old_render, new_render)
    print('OK: renderRefLists includes order statuses')

# 11. Wire order statuses into addRefItem
old_add = "  if (type==='status') { const s=getPipelineStatuses();if(!s.includes(val)){s.push(val);savePipelineStatuses(s);} }\n  el.value=''; renderRefLists(); populateFilterDropdowns();"
new_add = (
    "  if (type==='status') { const s=getPipelineStatuses();if(!s.includes(val)){s.push(val);savePipelineStatuses(s);} }\n"
    "  if (type==='order_status') { const el2=document.getElementById('new-order-status-input'); const s=getOrderStatuses();if(!s.includes(val)){s.push(val);saveOrderStatuses(s);} if(el2)el2.value=''; renderRefLists(); return; }\n"
    "  el.value=''; renderRefLists(); populateFilterDropdowns();"
)
if old_add not in h:
    print('NOT FOUND: addRefItem status block')
else:
    h = h.replace(old_add, new_add)
    print('OK: addRefItem handles order_status')

# 12. Wire order statuses into removeRefItem
old_remove = "  if (type==='status') { const s=getPipelineStatuses();s.splice(idx,1);savePipelineStatuses(s); }\n  renderRefLists(); populateFilterDropdowns();"
new_remove = (
    "  if (type==='status') { const s=getPipelineStatuses();s.splice(idx,1);savePipelineStatuses(s); }\n"
    "  if (type==='order_status') { const s=getOrderStatuses();s.splice(idx,1);saveOrderStatuses(s); }\n"
    "  renderRefLists(); populateFilterDropdowns();"
)
if old_remove not in h:
    print('NOT FOUND: removeRefItem status block')
else:
    h = h.replace(old_remove, new_remove)
    print('OK: removeRefItem handles order_status')

# 13. Overhaul openConvertToOrderModal with new fields
old_convert_fn_start = "async function openConvertToOrderModal(pipelineId) {"
idx2 = h.find("async function openConvertToOrderModal(pipelineId) {")
end2 = h.find("\nasync function saveConvertedOrder(", idx2)
old_convert_fn = h[idx2:end2]

new_convert_fn = """async function openConvertToOrderModal(pipelineId) {
  const e = pipelineData.find(x=>x.id===pipelineId); if(!e) return;
  const statuses = getOrderStatuses();
  document.getElementById('modal-title').innerHTML = 'Convert to Order';
  document.getElementById('modal-footer').innerHTML = '';
  document.getElementById('modal-body').innerHTML = `
    <form id="convert-order-form" onsubmit="saveConvertedOrder(event,${pipelineId})">
      <div style="background:var(--logo-blue-pale);border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px">
        <b>${e.contact_company||e.contact_name||'—'}</b> · ${e.brand_name||'—'}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Status *</label>
          <select name="status" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            ${statuses.map(s=>'<option>'+s+'</option>').join('')}
          </select></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Order Date *</label>
          <input name="order_date" type="date" required value="${new Date().toISOString().slice(0,10)}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">PO Received</label>
          <input name="po_date" type="date" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">PI Confirmed</label>
          <input name="pi_date" type="date" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Deposit Paid</label>
          <input name="deposit_date" type="date" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">FOB Date</label>
          <input name="fob_date" type="date" value="${e.due_date||''}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Payment Date</label>
          <input name="payment_date" type="date" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Order Value (USD) *</label>
          <input name="order_value" type="number" min="0" step="0.01" required placeholder="0" value="${e.potential_value||''}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Commission (USD)</label>
          <input name="commission_value" type="number" min="0" step="0.01" placeholder="0" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Testing Cost Deduction (USD)</label>
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

"""

if old_convert_fn_start not in h:
    print('NOT FOUND: openConvertToOrderModal function')
else:
    h = h.replace(old_convert_fn, new_convert_fn)
    print('OK: openConvertToOrderModal overhauled')

# 14. Update saveConvertedOrder to send new fields
old_save_convert_start = "async function saveConvertedOrder(ev, pipelineId) {"
idx3 = h.find("async function saveConvertedOrder(ev, pipelineId) {")
end3 = h.find("\n}\n", idx3) + 3
old_save_convert = h[idx3:end3]

new_save_convert = """async function saveConvertedOrder(ev, pipelineId) {
  ev.preventDefault();
  const e = pipelineData.find(x=>x.id===pipelineId); if(!e) return;
  const fd = new FormData(ev.target);
  const commValue = parseFloat(fd.get('commission_value'))||0;
  const testCost  = parseFloat(fd.get('testing_cost_deduction'))||0;
  const payload = {
    contact_id: e.contact_id,
    brand_id: e.brand_id,
    order_date: fd.get('order_date'),
    order_value: parseFloat(fd.get('order_value'))||0,
    currency: 'USD',
    gross_commission_rate: commValue,
    testing_cost_deduction: testCost,
    po_date:      fd.get('po_date')      || null,
    pi_date:      fd.get('pi_date')      || null,
    deposit_date: fd.get('deposit_date') || null,
    fob_date:     fd.get('fob_date')     || null,
    payment_date: fd.get('payment_date') || null,
    status: fd.get('status') || 'PO Received',
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
if old_save_convert_start not in h:
    print('NOT FOUND: saveConvertedOrder function')
else:
    h = h.replace(old_save_convert, new_save_convert)
    print('OK: saveConvertedOrder updated')

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved index.html.')
