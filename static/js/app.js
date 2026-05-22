
// ============================================================
// Kizuna (Konomocha CRM) v2.13
// ============================================================

const API = '/crm-staging/api';
let TOKEN = localStorage.getItem('crm_token');
let CURRENT_USER = JSON.parse(localStorage.getItem('crm_user') || 'null');

// ---- Reference data (localStorage) ----
const DEF_REGIONS   = ['Africa','Asia','Balkans','Eastern Europe','Europe','India','Middle East','North America','Oceania','South America'];
const DEF_PIPELINE_STATUSES = ['Awaiting Feedback','Awaiting Info','Awaiting Samples','Catalogue Sent','Closed / No Action','Deposit Paid','Form Completed','In Progress','On Hold','Order Placed','Price List Sent','Quotation Sent','Samples Delivered','Samples Requested','Samples Sent','Stalled'];
const DEF_LOST_STATUSES = ['Stalled', 'Closed / No Action', 'Cancelled'];
function isLostStatus(st) {
  var sp = _stageProbs && _stageProbs[st];
  if (sp !== undefined && sp !== null) return (sp.probability || 0) === 0;
  return DEF_LOST_STATUSES.indexOf(st) !== -1;
}
const DEF_ORDER_STATUSES = ['PO Received','PI Confirmed','Deposit Paid','Shipped','Payment Received','Cancelled'];
const DEF_TAGS      = ['Agent','CloseOut','DND','Distributor','Manufacturer','Network','Principal','Retailer','Stationery'];
const DEF_COUNTRIES = ['Afghanistan','Albania','Algeria','Angola','Argentina','Armenia','Australia','Austria','Azerbaijan','Bahrain','Bangladesh','Belarus','Belgium','Bosnia','Botswana','Brazil','Bulgaria','Cambodia','Canada','Chile','China','Colombia','Costa Rica','Croatia','Cyprus','Czech Republic','Denmark','Dominican Republic','Ecuador','Egypt','El Salvador','Estonia','Fiji','Finland','France','Georgia','Germany','Ghana','Gibraltar','Greece','Hong Kong','Hungary','Iceland','India','Indonesia','Iran','Iraq','Ireland','Israel','Italy','Jamaica','Japan','Jordan','Kazakhstan','Kenya','Korea','Kuwait','Latvia','Lebanon','Liechtenstein','Lithuania','Luxembourg','Macedonia','Madagascar','Malaysia','Malta','Mauritius','Mexico','Moldova','Mongolia','Morocco','Myanmar','Namibia','Netherlands','New Zealand','Nigeria','Norway','Oman','Pakistan','Palestine','Panama','Paraguay','Peru','Philippines','Poland','Portugal','Puerto Rico','Qatar','Romania','Russia','Saudi Arabia','Senegal','Serbia','Singapore','Slovakia','Slovenia','South Africa','South Korea','Spain','Sri Lanka','Sweden','Switzerland','Taiwan','Thailand','Trinidad and Tobago','Tunisia','Turkey','Ukraine','United Arab Emirates','United Kingdom','United States of America','Uruguay','Venezuela','Vietnam','Zimbabwe'];
// Reset countries if the list version changed
(function(){
  var stored = localStorage.getItem('crm_countries');
  if (stored && stored.indexOf('Serbia') === -1) {
    localStorage.removeItem('crm_countries');
  }
})();


function getRegions()   { return JSON.parse(localStorage.getItem('crm_regions')   || JSON.stringify(DEF_REGIONS)); }
function getTags()      { return JSON.parse(localStorage.getItem('crm_tags')      || JSON.stringify(DEF_TAGS)); }
function getCountries() { return JSON.parse(localStorage.getItem('crm_countries') || JSON.stringify(DEF_COUNTRIES)); }
function saveRegions(v)   { localStorage.setItem('crm_regions',   JSON.stringify(v)); }
function saveTags(v)      { localStorage.setItem('crm_tags',      JSON.stringify(v)); }
function saveCountries(v) { localStorage.setItem('crm_countries', JSON.stringify(v)); }
function getPipelineStatuses() { return JSON.parse(localStorage.getItem('crm_pipeline_statuses') || JSON.stringify(DEF_PIPELINE_STATUSES)); }
function savePipelineStatuses(v) { localStorage.setItem('crm_pipeline_statuses', JSON.stringify(v)); }
function getOrderStatuses() { return JSON.parse(localStorage.getItem('crm_order_statuses') || JSON.stringify(DEF_ORDER_STATUSES)); }
function saveOrderStatuses(v) { localStorage.setItem('crm_order_statuses', JSON.stringify(v)); }

// ---- Auth ----
async function login(email, password) {
  const fd = new FormData();
  fd.append('username', email); fd.append('password', password);
  const r = await fetch(API + '/auth/token', { method: 'POST', body: fd });
  if (!r.ok) throw new Error('Bad credentials');
  const d = await r.json();
  TOKEN = d.access_token;
  CURRENT_USER = { name: d.name, role: d.role };
  localStorage.setItem('crm_token', TOKEN);
  localStorage.setItem('crm_user', JSON.stringify(CURRENT_USER));
}

function logout() {
  localStorage.removeItem('crm_token'); localStorage.removeItem('crm_user');
  TOKEN = null; CURRENT_USER = null; showLogin();
}

async function apiFetch(path, opts = {}) {
  const r = await fetch(API + path, {
    ...opts,
    headers: { 'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json', ...(opts.headers||{}) }
  });
  if (r.status === 401) { logout(); return null; }
  if (!r.ok) { console.error(path, r.status, await r.text()); return null; }
  return r.json();
}

// ---- UI state ----
function showLogin() {
  document.getElementById('app-root').style.display = 'none';
  document.getElementById('login-screen').style.display = 'flex';
}

function showApp() {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app-root').style.display = 'grid';
  if (!CURRENT_USER) return;
  const ini = CURRENT_USER.name.split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
  document.getElementById('user-avatar').textContent = ini;
  document.getElementById('user-name').textContent   = CURRENT_USER.name;
  document.getElementById('user-role').textContent   = CURRENT_USER.role === 'admin' ? 'Administrator' : 'Agent';
  // Admin nav
  if (CURRENT_USER.role === 'admin') {
    document.getElementById('sb-hdr-admin').style.display = '';
    document.getElementById('nav-trash').style.display = '';
    document.getElementById('sb-body-admin').style.display = '';
  }
  // Orders — admin only
  if (CURRENT_USER.role !== 'admin') {
    document.querySelectorAll('[data-view="orders"]').forEach(el => el.style.display='none');
    var rrc = document.getElementById('rr-commission'); if(rrc) rrc.style.display='none';
    var rrb = document.getElementById('rr-bonus'); if(rrb) rrb.style.display='none';
  }
}

// ---- Navigation ----
const TITLES = { dashboard:'Dashboard', contacts:'Contacts', companies:'Companies', pipeline:'Pipeline', brands:'Brands', orders:'Orders', tasks:'Tasks', email:'Email Log', reports:'Reports', admin:'Admin', trash:'Trash' };
function activate(view) {
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === 'view-'+view));
  document.querySelectorAll('.sb-item[data-view]').forEach(n => n.classList.toggle('active', n.dataset.view === view));
  const crumb = document.getElementById('crumb-here');
  if (crumb) crumb.textContent = TITLES[view] || view;
  window.scrollTo({top:0});
  loadView(view);
}
document.querySelectorAll('.sb-item[data-view]').forEach(n => n.addEventListener('click', () => activate(n.dataset.view)));

// ---- Helpers ----
const STATUS_CLASS = { 'Deposit Paid':'green','Order Placed':'green','On Hold':'amber','Stalled':'amber','Closed / No Action':'grey','Cancelled':'grey' };
function statusClass(s) { return STATUS_CLASS[s] || 'blue'; }

function fmtNum(n) { return Number(n||0).toLocaleString('en-GB'); }
function fmtShort(n) {
  n = Number(n)||0;
  if (n>=1000000) return (n/1000000).toFixed(1)+'M';
  if (n>=1000) return (n/1000).toFixed(0)+'K';
  return n.toString();
}
function fmtVal(v, cur='USD') {
  return `<span class="ccy">${cur}</span>${v ? Number(v).toLocaleString() : '0'}`;
}
function fmtDate(d) {
  if (!d) return '<span style="color:var(--warm-grey-light)">—</span>';
  const dt = new Date(d + 'T00:00:00'), today = new Date(); today.setHours(0,0,0,0);
  const diff = Math.floor((dt-today)/86400000);
  const mn = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const lbl = String(dt.getDate()).padStart(2,'0') + '/' + mn[dt.getMonth()] + '/' + dt.getFullYear();
  if (diff<0) return '<span style="color:#B33A47;font-weight:600">' + lbl + '</span>';
  if (diff===0) return '<span style="color:#8A5A00;font-weight:600">' + lbl + '</span>';
  return lbl;
}

const OWN_COLORS = { Thierry:'linear-gradient(135deg,#76BCE0,#5A9FC4)', Zeal:'#F3E2C0', Erna:'#E0D8EE' };
function firstOf(name){ return (name||'').split(' ')[0]; }
function ownerAv(name) {
  const ini=(name||'?').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
  const bg=OWN_COLORS[name]||'#E5E7EB';
  const first=(name||'—').split(' ')[0];
  return `<div class="owner-cell"><div class="avatar" style="width:24px;height:24px;font-size:10px;background:${bg};">${escHtml(ini)}</div>${escHtml(first)}</div>`;
}

const BM=['bm-1','bm-2','bm-3','bm-4','bm-5','bm-6','bm-7','bm-8']; const BM_MAP={}; let bmI=0;
function brandMark(name) {
  if (!BM_MAP[name]) BM_MAP[name]=BM[bmI++%8];
  const ini=(name||'?').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
  return `<div class="brand-cell"><div class="brand-mark ${BM_MAP[name]}">${escHtml(ini)}</div>${escHtml(name)}</div>`;
}

function getRegionFromTags(tags) {
  if (!tags) return '';
  for (const r of getRegions()) { if (tags.includes(r)) return r; }
  return '';
}
function getTagGroup(tags) {
  if (!tags) return '';
  for (const t of getTags()) { if (tags.includes(t)) return t; }
  return '';
}
function cleanTags(tags) {
  if (!tags) return '';
  return tags.split(',').map(t=>t.trim()).filter(t=>t && t!=='Contact' && t!=='Company' && !getRegions().includes(t)).join(', ');
}

// ---- Sort helpers ----
function sortIcon(dir) { return dir==='asc' ? ' ▲' : ' ▼'; }
function showToast(msg) {
  var t=document.createElement('div');
  t.style.cssText='position:fixed;bottom:24px;right:24px;background:var(--navy);color:#fff;padding:12px 20px;border-radius:8px;font-size:13px;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,.2)';
  t.textContent=msg; document.body.appendChild(t);
  setTimeout(function(){t.remove();},3000);
}

// ---- Pager ----
function renderPager(containerId, page, total, perPage, cb) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const pages = Math.ceil(total/perPage);
  if (pages <= 1) { el.innerHTML=''; return; }
  let btns = '';
  for (let p=1; p<=pages; p++) {
    if (p===1||p===pages||Math.abs(p-page)<=2) btns+=`<button class="pg-btn${p===page?' current':''}" onclick="(${cb})(${p})">${p}</button>`;
    else if (Math.abs(p-page)===3) btns+=`<button class="pg-btn" disabled>…</button>`;
  }
  el.innerHTML = `<button class="pg-btn" onclick="(${cb})(${Math.max(1,page-1)})">‹</button>${btns}<button class="pg-btn" onclick="(${cb})(${Math.min(pages,page+1)})">›</button>`;
}

// ---- Export ----
async function downloadFileBlob(path, filename) {
  const r = await fetch(API + path, { headers: { 'Authorization': 'Bearer ' + TOKEN } });
  if (!r.ok) { showToast('Download failed (' + r.status + ')'); return; }
  const blob = await r.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename; a.click();
}

function downloadBrandReport(brandId) {
  downloadFileBlob('/brands/' + brandId + '/report.xlsx', 'brand_report.xlsx');
}

function exportTable(tbodyId, headers, filename) {
  const rows = document.querySelectorAll('#'+tbodyId+' tr');
  const lines = [headers.join(',')];
  rows.forEach(r => {
    const cells = r.querySelectorAll('td');
    if (!cells.length) return;
    lines.push(Array.from(cells).slice(0, headers.length).map(c=>`"${c.textContent.trim().replace(/"/g,'""')}"`).join(','));
  });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([lines.join('\n')],{type:'text/csv'}));
  a.download = filename+'_export.csv'; a.click();
}

// ---- Dashboard ----
async function loadDashboard() {
  const d = await apiFetch('/dashboard');
  if (!d) return;
  const ds=document.getElementById('dash-sub');
  if(ds) ds.textContent = new Date().toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long',year:'numeric'});
  const kp=document.getElementById('kpi-pipeline'); if(kp) kp.innerHTML=d.total_active_pipeline;
  const ko=document.getElementById('kpi-overdue'); if(ko) ko.innerHTML=d.overdue_actions;
  const kv=document.getElementById('kpi-value'); if(kv) kv.innerHTML=fmtShort(d.total_pipeline_value);
  const kc=document.getElementById('kpi-commission'); if(kc) kc.innerHTML=fmtShort(d.commission_due);
  // Update KPI scope labels
  var scope = d.is_admin ? 'company-wide' : 'your deals';
  var kpf = document.getElementById('kpi-pipe-scope'); if(kpf) kpf.textContent = scope;
  var kvf = document.getElementById('kpi-val-scope');  if(kvf) kvf.textContent = scope;
  var kcf = document.getElementById('kpi-com-scope');  if(kcf) kcf.textContent = d.is_admin ? 'unpaid orders' : 'your contacts';
  var kof = document.getElementById('kpi-ovd-scope');  if(kof) kof.textContent = scope;
  // Agent bonus widget
  if (!d.is_admin) {
    var bw = document.getElementById('agent-bonus-widget'); if(bw) bw.style.display='block';
    loadMyBonus();
  }

  // Recent emails
  const ef = document.getElementById('email-feed');
  if (ef) {
    if (d.recent_emails && d.recent_emails.length) {
      const avatarCls = ['av-a','av-b','av-c','av-d','av-e','av-f'];
      ef.innerHTML = d.recent_emails.map(function(e,i) {
        var name = e.contact_name || e.subject || '?';
        var initials = name.split(' ').map(function(w){return w[0]||'';}).slice(0,2).join('').toUpperCase() || '?';
        var co = e.contact_company ? '<span class="em-co">' + escHtml(e.contact_company) + '</span>' : '';
        var dir = e.direction === 'inbound' ? '<span class="em-dir in">In</span>' : '<span class="em-dir out">Out</span>';
        var when = e.sent_at ? new Date(e.sent_at).toLocaleDateString('en-GB',{day:'numeric',month:'short'}) : '';
        return '<div class="email-row">'
          + '<div class="email-avatar ' + avatarCls[i % avatarCls.length] + '">' + initials + '</div>'
          + '<div><div class="em-line1"><span class="em-from">' + escHtml(name) + '</span>' + co + dir + '</div>'
          + '<div class="em-subj">' + escHtml(e.subject || '(no subject)') + '</div></div>'
          + '<div class="em-meta">' + when + '</div>'
          + '</div>';
      }).join('');
    } else {
      ef.innerHTML = '<div style="padding:20px;color:var(--warm-grey);text-align:center">No emails logged yet.</div>';
    }
  }

  // Today's actions
  var al = document.getElementById('actions-list');
  if (al) {
    var today = new Date().toISOString().slice(0,10);
    if (d.today_actions && d.today_actions.length) {
      al.innerHTML = d.today_actions.map(function(t) {
        var overdue = t.due_date && t.due_date < today;
        var co = t.contact_company ? escHtml(t.contact_company) : escHtml(t.contact_name || '');
        return '<div style="display:flex;align-items:flex-start;gap:12px;padding:10px 16px;border-bottom:1px solid var(--line);cursor:pointer" onclick="openContactDetail(' + t.contact_id + ')">'
          + '<div style="margin-top:2px;width:8px;height:8px;border-radius:50%;background:' + (overdue ? 'var(--accent-coral)' : '#4CAF50') + ';flex-shrink:0"></div>'
          + '<div style="flex:1;min-width:0">'
          + '<div style="font-size:13px;font-weight:500;color:var(--navy);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + escHtml(t.title) + '</div>'
          + '<div style="font-size:11px;color:var(--warm-grey)">' + co + '</div>'
          + '</div>'
          + '<div style="font-size:11px;color:' + (overdue ? 'var(--accent-coral)' : 'var(--warm-grey)') + ';white-space:nowrap;font-weight:' + (overdue ? '600' : '400') + '">' + (t.due_date || '') + '</div>'
          + '</div>';
      }).join('');
    } else {
      al.innerHTML = '<div style="padding:20px;color:var(--warm-grey);text-align:center">No tasks due today.</div>';
    }
  }

  // Pipeline by stage
  var sb = document.getElementById('stage-bars');
  if (sb) {
    if (d.pipeline_by_stage && d.pipeline_by_stage.length) {
      var maxCnt = Math.max.apply(null, d.pipeline_by_stage.map(function(s){return s.count;}));
      sb.innerHTML = '<div style="padding:12px 16px">'
        + d.pipeline_by_stage.map(function(s) {
            var pct = maxCnt ? Math.round(s.count / maxCnt * 100) : 0;
            var valStr = s.value > 0 ? ' &middot; <span style="color:var(--logo-blue-dark)">USD ' + fmtShort(s.value) + '</span>' : '';
            return '<div style="margin-bottom:10px">'
              + '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px">'
              + '<span style="color:var(--navy)">' + escHtml(s.status) + '</span>'
              + '<span style="color:var(--warm-grey)">' + s.count + ' deal' + (s.count!==1?'s':'') + valStr + '</span>'
              + '</div>'
              + '<div style="height:6px;background:var(--off-white);border-radius:3px">'
              + '<div style="height:6px;width:' + pct + '%;background:var(--logo-blue);border-radius:3px;transition:width .3s"></div>'
              + '</div>'
              + '</div>';
          }).join('')
        + '</div>';
    } else {
      sb.innerHTML = '<div style="padding:20px;color:var(--warm-grey);text-align:center">No active pipeline.</div>';
    }
  }

  // Team workload — tasks due today + overdue
  var tw = document.getElementById('team-workload');
  if (tw && d.team_workload) {
    var active = d.team_workload.filter(function(u){return u.tasks_today > 0 || u.tasks_overdue > 0;});
    if (active.length) {
      tw.innerHTML = active.map(function(u) {
        var ovd = u.tasks_overdue > 0
          ? '<div style="font-size:11px;color:#B33A47;font-weight:600;margin-top:2px">' + u.tasks_overdue + ' overdue</div>'
          : '';
        return '<div style="background:var(--white);border:1px solid var(--line);border-radius:10px;padding:14px 18px;display:flex;flex-direction:column;gap:4px">'
          + '<div style="font-weight:600;color:var(--navy);font-size:14px">' + escHtml(u.name.split(' ')[0]) + '</div>'
          + '<div style="font-size:22px;font-weight:700;color:var(--logo-blue-dark);font-family:var(--font-mono)">' + u.tasks_today + '</div>'
          + '<div style="font-size:11px;color:var(--warm-grey)">due today</div>'
          + ovd
          + '</div>';
      }).join('');
    } else {
      tw.innerHTML = '<div style="padding:20px;color:var(--warm-grey);text-align:center;grid-column:span 3">No tasks due today.</div>';
    }
  }
}

// ---- Contacts ----
let contactPage=1, contactSearch='', contactSort='name', contactSortDir='asc';
let contactFilters = { country:'', region:'', tag:'' };

async function loadContacts() {
  const backendContactSort = contactSort === 'region' ? 'tags' : contactSort;
  const p = new URLSearchParams({ source:'contacts', page:contactPage, per_page:50, sort_by:backendContactSort, sort_dir:contactSortDir });
  if (contactSearch) p.set('search', contactSearch);
  if (contactFilters.country) p.set('country', contactFilters.country);
  const d = await apiFetch('/contacts?'+p);
  if (!d) return;

  // Client-side region/tag filter (not yet in backend)
  let rows = d.results;
  if (contactFilters.region) rows = rows.filter(c => getRegionFromTags(c.tags) === contactFilters.region);
  if (contactFilters.tag)    rows = rows.filter(c => getTagGroup(c.tags) === contactFilters.tag);

  document.getElementById('contacts-meta').textContent = fmtNum(d.total) + ' contacts';
  const sc = document.getElementById('sb-count-contacts'); if(sc) sc.textContent = fmtNum(d.total);
  document.getElementById('contacts-foot').innerHTML = `Showing ${rows.length} of ${d.total}`;

  // Sort icons
  ['name','last_name','country','company','region','tags'].forEach(k => {
    const el = document.getElementById('sort-contact-'+k);
    if (el) el.textContent = contactSort===k ? sortIcon(contactSortDir) : '';
  });

  const tbody = document.getElementById('contacts-tbody');
  if (!rows.length) { tbody.innerHTML='<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--warm-grey);">No contacts found.</td></tr>'; return; }
  tbody.innerHTML = rows.map(c => `
    <tr style="cursor:pointer" onclick="openContactDetail(${c.id})">
      <td class="contact-cell">${escHtml(c.first_name||'')}</td>
      <td><div class="nm">${escHtml(c.last_name)||'—'}</div></td>
      <td>${c.company ? `<span style="color:var(--logo-blue-dark);font-weight:500" onclick="event.stopPropagation();openCompanyContacts('${c.company.replace(/'/g,"\\'")}','${encodeURIComponent(c.company)}')">${escHtml(c.company)}</span>` : '—'}</td><td>${escHtml(c.job_title)||'—'}</td>
      <td>${escHtml(c.country)||'—'}</td>
      <td>${getRegionFromTags(c.tags)||'—'}</td>
      <td>${escHtml(c.phone)||'—'}</td>
      <td style="font-size:12px;color:var(--warm-grey)">${escHtml(c.email)||'—'}</td>
      <td>${getTagGroup(c.tags)?`<span style="font-size:11px;background:var(--logo-blue-pale);color:var(--logo-blue-dark);padding:2px 8px;border-radius:10px">${getTagGroup(c.tags)}</span>`:'—'}</td>
    </tr>`).join('');

  renderPager('contacts-pager', contactPage, d.total, 50, 'function(p){contactPage=p;loadContacts()}');
}

function sortContacts(col) {
  if (contactSort===col) contactSortDir = contactSortDir==='asc'?'desc':'asc';
  else { contactSort=col; contactSortDir='asc'; }
  contactPage=1; loadContacts();
}

// ---- Companies ----
let companyPage=1, companySearch='', companySort='company', companySortDir='asc';
let companyFilters = { country:'', region:'', tag:'' };

async function loadCompanies() {
  const backendCompanySort = companySort === 'region' ? 'tags' : companySort;
  const p = new URLSearchParams({ source:'companies', page:companyPage, per_page:50, sort_by:backendCompanySort, sort_dir:companySortDir });
  if (companySearch) p.set('search', companySearch);
  if (companyFilters.country) p.set('country', companyFilters.country);
  const d = await apiFetch('/contacts?'+p);
  if (!d) return;

  let rows = d.results;
  if (companyFilters.region) rows = rows.filter(c => getRegionFromTags(c.tags) === companyFilters.region);
  if (companyFilters.tag)    rows = rows.filter(c => getTagGroup(c.tags) === companyFilters.tag);

  document.getElementById('companies-meta').textContent = fmtNum(d.total) + ' companies';
  const sc = document.getElementById('sb-count-companies'); if(sc) sc.textContent = fmtNum(d.total);
  document.getElementById('companies-foot').innerHTML = `Showing ${rows.length} of ${d.total}`;

  ['company','country','region','tags'].forEach(k => {
    const el = document.getElementById('sort-company-'+k);
    if (el) el.textContent = companySort===k ? sortIcon(companySortDir) : '';
  });

  const tbody = document.getElementById('companies-tbody');
  if (!rows.length) { tbody.innerHTML='<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--warm-grey);">No companies found.</td></tr>'; return; }
  tbody.innerHTML = rows.map(c => `
    <tr style="cursor:pointer" onclick="openCompanyContacts('${(c.company||c.name).replace(/'/g,"\\'")}','${encodeURIComponent(c.company||c.name)}')">
      <td class="contact-cell"><div class="nm">${escHtml(c.company||c.name)}</div></td>
      <td>${escHtml(c.country)||'—'}</td>
      <td>${getRegionFromTags(c.tags)||'—'}</td>
      <td>${getTagGroup(c.tags)?`<span style="font-size:11px;background:var(--logo-blue-pale);color:var(--logo-blue-dark);padding:2px 8px;border-radius:10px">${getTagGroup(c.tags)}</span>`:'—'}</td>
      <td><span style="color:var(--logo-blue-dark);font-weight:600">View →</span></td>
    </tr>`).join('');

  renderPager('companies-pager', companyPage, d.total, 50, 'function(p){companyPage=p;loadCompanies()}');
}

function sortCompanies(col) {
  if (companySort===col) companySortDir = companySortDir==='asc'?'desc':'asc';
  else { companySort=col; companySortDir='asc'; }
  companyPage=1; loadCompanies();
}

// ---- Contact detail ----
async function openContactDetail(id) {
  const c = await apiFetch('/contacts/'+id);
  if (!c) return;
  const countries  = getCountries();
  const regions    = getRegions();
  const tagGroups  = getTags();
  const curRegion  = regions.find(r => (c.tags||'').includes(r)) || '';
  const curTag     = tagGroups.find(t => (c.tags||'').includes(t)) || '';
  document.getElementById('modal-title').innerHTML =
    `<div>${escHtml(c.first_name||'')} ${escHtml(c.last_name||c.name||'')}</div>`+
    `<div style="font-size:13px;font-weight:400;color:var(--warm-grey)">`+
      `${escHtml(c.company||'')}${c.country?' · '+escHtml(c.country):''}</div>`;
  document.getElementById('modal-body').innerHTML =
    `<form id="edit-contact-form" onsubmit="saveContactEdit(event,${id})">`+
    `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">`+
      `<div><label class="fl">First Name</label>`+
        `<input name="first_name" value="${escHtml(c.first_name||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
      `<div><label class="fl">Last Name</label>`+
        `<input name="last_name" value="${escHtml(c.last_name||c.name||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
    `</div>`+
    `<div style="margin-bottom:12px"><label class="fl">Company</label>`+
      `<input name="company" value="${escHtml(c.company||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
    `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">`+
      `<div><label class="fl">Email</label>`+
        `<input name="email" type="email" value="${escHtml(c.email||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
      `<div><label class="fl">Phone</label>`+
        `<input name="phone" value="${escHtml(c.phone||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
    `</div>`+
    `<div style="margin-bottom:12px"><label class="fl">Job Title</label>`+
      `<input name="job_title" value="${escHtml(c.job_title||'')}" placeholder="e.g. Buying Manager" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
    `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">`+
      `<div><label class="fl">Country</label>`+
        `<select name="country" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">`+
          `<option value="">— Select —</option>`+
          `${countries.map(co=>`<option${co===c.country?' selected':''}>${escHtml(co)}</option>`).join('')}`+
        `</select></div>`+
      `<div><label class="fl">Sales Region</label>`+
        `<select name="region" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">`+
          `<option value="">— Select —</option>`+
          `${regions.map(r=>`<option${r===curRegion?' selected':''}>${escHtml(r)}</option>`).join('')}`+
        `</select></div>`+
    `</div>`+
    `<div style="margin-bottom:20px"><label class="fl">Group / Tag</label>`+
      `<select name="tag_group" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">`+
        `<option value="">— Select —</option>`+
        `${tagGroups.map(t=>`<option${t===curTag?' selected':''}>${escHtml(t)}</option>`).join('')}`+
      `</select></div>`+
    `<div id="ec-error" style="display:none;color:#B33A47;font-size:13px;margin-bottom:12px;padding:10px;background:#FAE3E5;border-radius:8px"></div>`+
    `<div style="display:flex;gap:8px;justify-content:flex-end;margin-bottom:24px">`+
      `<button type="button" onclick="document.getElementById('modal').style.display='none';window._editFromReport=false;" class="btn btn-secondary">Cancel</button>`+
      `${CURRENT_USER&&CURRENT_USER.role==='admin'?'<button type="button" onclick="deleteContactFromModal('+id+')" class="btn btn-secondary" style="color:#B33A47">Delete</button>':''}`+
      `<button type="submit" class="btn btn-primary">Save</button>`+
    `</div></form>`+
    `<div style="text-align:right;margin:-4px 0 16px"><button type="button" onclick="openMergeModal(${id})" style="background:none;border:none;color:var(--warm-grey);font-size:12px;cursor:pointer;padding:0;text-decoration:underline">Merge duplicate…</button></div>`+
    `<div style="border-top:1px solid var(--line);padding-top:16px">`+
      `<div style="font-size:13px;font-weight:600;color:var(--navy);margin-bottom:12px">Notes</div>`+
      `<div id="contact-notes-list"><div style="font-size:13px;color:var(--warm-grey)">Loading…</div></div>`+
      (c.notes ? `<div style="margin-bottom:12px;padding:10px 12px;background:var(--off-white);border-radius:8px;font-size:12px"><span style="font-weight:600;color:var(--warm-grey)">Imported note:</span> <span style="white-space:pre-wrap">${escHtml(c.notes)}</span></div>` : '')+
      `<div style="margin-top:12px">`+
        `<label class="fl">Add Note</label>`+
        `<textarea id="new-note-body" rows="3" placeholder="Type a note…" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;resize:vertical;margin-bottom:8px;box-sizing:border-box"></textarea>`+
        `<button onclick="addContactNote(${id})" class="btn btn-primary" style="font-size:13px">Add Note</button>`+
      `</div>`+
    `</div>`+
    `<div style="border-top:1px solid var(--line);padding-top:16px;margin-top:16px">`+
      `<div style="font-size:13px;font-weight:600;color:var(--navy);margin-bottom:12px">Attachments</div>`+
      `<div id="contact-attachments-list"><div style="font-size:13px;color:var(--warm-grey)">Loading…</div></div>`+
      `<div style="margin-top:10px;display:flex;align-items:center;gap:10px">`+
        `<label class="btn btn-secondary" style="cursor:pointer;font-size:12px">+ Attach File`+
          `<input type="file" multiple style="display:none" onchange="uploadContactAttachment(${id},this)"/>`+
        `</label>`+
      `</div>`+
    `</div>`+
    `<div style="border-top:1px solid var(--line);padding-top:16px;margin-top:16px">`+
      `<div style="font-size:13px;font-weight:600;color:var(--navy);margin-bottom:12px">Tasks</div>`+
      `<div id="contact-tasks-list"><div style="font-size:13px;color:var(--warm-grey)">Loading…</div></div>`+
      `<div style="display:grid;grid-template-columns:1fr auto;gap:8px;align-items:end;margin-top:10px">`+
        `<div><label class="fl">New Task</label>`+
          `<input id="new-task-title" placeholder="Task description…" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
        `<div><label class="fl">Due Date</label>`+
          `<input type="date" id="new-task-due" style="border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
      `</div>`+
      `<div style="display:flex;gap:8px;align-items:center;margin-top:8px">`+
        `<select id="new-task-assignee" style="flex:1;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">`+
          `<option value="">Assign to…</option>`+
          `${(window._crmUsers||[]).map(u=>`<option value="${u.id}">${escHtml(u.name)}</option>`).join('')}`+
        `</select>`+
        `<button onclick="addContactTask(${id})" class="btn btn-primary" style="font-size:13px">Add Task</button>`+
      `</div>`+
    `</div>`;
  document.getElementById('modal').style.display = 'flex';
  loadContactNotes(id);
  loadContactAttachments(id);
  loadContactTasks(id);
}

async function saveContactEdit(e, id) {
  e.preventDefault();
  const fd       = new FormData(e.target);
  const first    = fd.get('first_name')||'';
  const last     = fd.get('last_name')||'';
  const name     = (first+' '+last).trim() || fd.get('company')||'';
  const newRegion= fd.get('region')||'';
  const newTag   = fd.get('tag_group')||'';
  const c = await apiFetch('/contacts/'+id);
  const regions   = getRegions();
  const tagGroups = getTags();
  let tags = (c ? (c.tags||'') : '').split(',').map(t=>t.trim())
    .filter(t=>t && !regions.includes(t) && !tagGroups.includes(t) && t!=='Contact' && t!=='Company');
  if (newRegion) tags.push(newRegion);
  if (newTag)    tags.push(newTag);
  const payload = {
    first_name: first||null, last_name: last||null, name,
    company: fd.get('company')||null,
    email:   fd.get('email')||null,
    phone:   fd.get('phone')||null,
    job_title: fd.get('job_title')||null,
    country: fd.get('country')||null,
    tags:    tags.join(', ')||null,
  };
  const btn = e.target.querySelector('[type=submit]');
  btn.textContent='Saving…'; btn.disabled=true;
  const result = await apiFetch('/contacts/'+id, {method:'PUT', body:JSON.stringify(payload)});
  if (result) {
    document.getElementById('modal').style.display='none';
    showToast('Contact saved');
    if (window._editFromReport) {
      window._editFromReport = false;
      loadQualityReport();
    } else {
      contactSearch = '';
      const _si = document.getElementById('contact-search'); if (_si) _si.value = '';
      loadContacts();
    }
  } else {
    document.getElementById('ec-error').textContent='Failed to save. Please try again.';
    document.getElementById('ec-error').style.display='block';
    btn.textContent='Save'; btn.disabled=false;
  }
}

async function loadContactNotes(contactId) {
  const data = await apiFetch('/contacts/'+contactId+'/notes');
  const el = document.getElementById('contact-notes-list');
  if (!el) return;
  if (!data || !data.length) {
    el.innerHTML = '<div style="font-size:13px;color:var(--warm-grey);margin-bottom:12px">No notes yet.</div>';
    return;
  }
  el.innerHTML = data.map(n=>`
    <div style="margin-bottom:8px;padding:10px 12px;background:var(--off-white);border-radius:8px">
      <div style="font-size:11px;color:var(--warm-grey);margin-bottom:4px">
        <strong style="color:var(--navy)">${escHtml(n.author_name)}</strong>
        &nbsp;·&nbsp;${new Date(n.created_at).toLocaleString('en-GB',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})}
      </div>
      <div style="font-size:13px;white-space:pre-wrap">${escHtml(n.body)}</div>
    </div>`).join('');
}

async function addContactNote(contactId) {
  const bodyEl = document.getElementById('new-note-body');
  const body   = (bodyEl ? bodyEl.value : '').trim();
  if (!body) return;
  const btn = document.querySelector('[onclick="addContactNote('+contactId+')"]');
  if (btn) { btn.textContent='Saving…'; btn.disabled=true; }
  const result = await apiFetch('/contacts/'+contactId+'/notes', {method:'POST', body:JSON.stringify({body})});
  if (result) {
    if (bodyEl) bodyEl.value = '';
    loadContactNotes(contactId);
    showToast('Note added');
  }
  if (btn) { btn.textContent='Add Note'; btn.disabled=false; }
}

async function openCompanyContacts(name, encoded) {
  const d = await apiFetch('/contacts?search='+encodeURIComponent(name)+'&per_page=100');
  if (!d) return;
  const contacts = d.results
    .filter(c => (c.company||'').toLowerCase()===name.toLowerCase() && c.source !== 'lacrm_company_import')
    .sort((a,b) => (a.last_name||a.name||'').localeCompare(b.last_name||b.name||''));
  document.getElementById('modal-title').innerHTML = escHtml(name);
  document.getElementById('modal-body').innerHTML = contacts.length ? `
    <div style="font-size:13px;color:var(--warm-grey);margin-bottom:12px">${contacts.length} contact${contacts.length>1?'s':''}</div>
    ${contacts.map(c=>`<div onclick="document.getElementById('modal').style.display='none';setTimeout(()=>openContactDetail(${c.id}),100)"
      style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border:1px solid var(--line);border-radius:8px;margin-bottom:6px;cursor:pointer"
      onmouseover="this.style.background='var(--logo-blue-pale)'" onmouseout="this.style.background=''">
      <div><div style="font-weight:600;color:var(--navy)">${escHtml(c.first_name||'')} ${escHtml(c.last_name||c.name)}</div>
      <div style="font-size:12px;color:var(--warm-grey)">${escHtml(c.email||'')} ${c.phone?'· '+escHtml(c.phone):''}</div></div>
      <span style="color:var(--logo-blue-dark)">View →</span>
    </div>`).join('')}
  ` : '<div style="padding:20px;text-align:center;color:var(--warm-grey);">No contacts found for this company.</div>';
  document.getElementById('modal').style.display = 'flex';
}

// ---- New Contact / Company modal ----
async function openNewContactModal(type) {
  const isCompany = type === 'company';
  document.getElementById('modal-title').innerHTML = isCompany ? 'New Company' : 'New Contact';
  const countries = getCountries();
  const tags = getTags();
  document.getElementById('modal-body').innerHTML = `
    <form id="new-contact-form" onsubmit="saveNewContact(event,'${type}')">
      ${!isCompany ? `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">First Name</label>
          <input name="first_name" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Last Name</label>
          <input name="last_name" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>` : ''}
      <div style="margin-bottom:12px;position:relative">
        <label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">
          Company Name ${!isCompany ? '<span style="color:var(--accent-coral);font-size:11px;text-transform:none;letter-spacing:0">(company must exist first)</span>' : ''}
        </label>
        <input id="company-name-input" name="company" autocomplete="off"
          style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"
          ${!isCompany ? 'oninput="companyLookup(this.value)"' : ''}/>
        ${!isCompany ? '<div id="company-suggestions" style="display:none;position:absolute;top:100%;left:0;right:0;background:var(--white);border:1px solid var(--line);border-radius:8px;z-index:20;max-height:200px;overflow-y:auto;box-shadow:var(--shadow-md)"></div>' : ''}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Email</label>
          <input name="email" type="email" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Phone</label>
          <input name="phone" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Job Title</label>
        <input name="job_title" placeholder="e.g. Buying Manager" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Country</label>
          <select name="country" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            <option value="">— Select —</option>
            ${countries.map(c=>`<option>${c}</option>`).join('')}
          </select></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Group / Tag</label>
          <select name="tags" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            <option value="">— Select —</option>
            ${tags.map(t=>`<option>${t}</option>`).join('')}
          </select></div>
      </div>
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Assigned To</label>
        <select name="owner_id" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
          <option value="">— Select —</option>
          ${(window._crmUsers||[]).map(u=>`<option value="${u.id}">${escHtml(u.name)}</option>`).join('')}
        </select></div>
      <div style="margin-bottom:20px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Notes</label>
        <textarea name="notes" rows="3" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;resize:vertical"></textarea></div>
      <div id="nc-error" style="display:none;color:#B33A47;font-size:13px;margin-bottom:12px;padding:10px;background:#FAE3E5;border-radius:8px"></div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" onclick="document.getElementById('modal').style.display='none'" class="btn btn-secondary">Cancel</button>
        <button type="submit" class="btn btn-primary">Save</button>
      </div>
    </form>`;
  document.getElementById('modal').style.display = 'flex';
}

async function companyLookup(val) {
  const list = document.getElementById('company-suggestions');
  if (!list || val.length < 3) { if(list) list.style.display='none'; return; }
  const d = await apiFetch('/contacts?source=companies&search='+encodeURIComponent(val)+'&per_page=8');
  if (!d) return;
  if (!d.results.length) {
    list.innerHTML = `<div style="padding:10px 14px;font-size:12px;color:var(--accent-coral)">No company found — please create the company first.</div>`;
  } else {
    list.innerHTML = d.results.map(c=>`
      <div onclick="document.getElementById('company-name-input').value='${(c.company||c.name).replace(/'/g,"\\'")}';document.getElementById('company-suggestions').style.display='none'"
        style="padding:9px 14px;font-size:13px;cursor:pointer;border-bottom:1px solid var(--line)"
        onmouseover="this.style.background='var(--logo-blue-pale)'" onmouseout="this.style.background=''">
        ${escHtml(c.company||c.name)} ${c.country?`<span style="color:var(--warm-grey);font-size:11px">· ${escHtml(c.country)}</span>`:''}
      </div>`).join('');
  }
  list.style.display = 'block';
}

async function saveNewContact(e, type) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const isCompany = type === 'company';
  const first = fd.get('first_name')||''; const last = fd.get('last_name')||'';
  const name = isCompany ? (fd.get('company')||'') : ((first+' '+last).trim() || fd.get('company')||'');

  // Duplicate check
  if (name) {
    const check = await apiFetch('/contacts?search='+encodeURIComponent(name)+'&per_page=5');
    if (check && check.results.some(c => c.name.toLowerCase()===name.toLowerCase())) {
      document.getElementById('nc-error').textContent = `A contact named "${name}" already exists. Please check before saving.`;
      document.getElementById('nc-error').style.display = 'block';
      return;
    }
  }

  const payload = {
    first_name: first||null, last_name: last||null, name,
    company: fd.get('company')||null, email: fd.get('email')||null,
    phone: fd.get('phone')||null, job_title: fd.get('job_title')||null, country: fd.get('country')||null,
    tags: fd.get('tags') || (isCompany?'Company':'Contact'),
    notes: fd.get('notes')||null,
    owner_id: fd.get('owner_id') ? parseInt(fd.get('owner_id')) : null,
  };
  const btn = e.target.querySelector('[type=submit]');
  btn.textContent='Saving…'; btn.disabled=true;
  const result = await apiFetch('/contacts', { method:'POST', body:JSON.stringify(payload) });
  if (result) {
    document.getElementById('modal').style.display='none';
    isCompany ? loadCompanies() : loadContacts();
  } else {
    document.getElementById('nc-error').textContent='Failed to save. Please try again.';
    document.getElementById('nc-error').style.display='block';
    btn.textContent='Save'; btn.disabled=false;
  }
}

// CSV upload
function downloadContactTemplate() {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['First Name,Last Name,Company,Email,Phone,Country,Tags,Notes\nJohn,Smith,Acme Ltd,john@acme.com,+1234567890,United Kingdom,Retailer,Key account'],{type:'text/csv'}));
  a.download='contacts_template.csv'; a.click();
}
async function uploadContactCSV(input) {
  const file = input.files[0]; if(!file) return;
  const text = await file.text();
  const lines = text.split('\n').filter(l=>l.trim());
  const headers = lines[0].split(',').map(h=>h.replace(/"/g,'').trim());
  let added=0, errors=0;
  for (let i=1;i<lines.length;i++) {
    const vals = lines[i].match(/(".*?"|[^,]+)(?=,|$)/g)||lines[i].split(',');
    const row={}; headers.forEach((h,idx)=>row[h]=(vals[idx]||'').replace(/"/g,'').trim());
    const payload={ first_name:row['First Name']||null, last_name:row['Last Name']||null,
      name:(row['First Name']||'')+' '+(row['Last Name']||''), company:row['Company']||null,
      email:row['Email']||null, phone:row['Phone']||null, country:row['Country']||null,
      tags:row['Tags']||null, notes:row['Notes']||null };
    if (!payload.name.trim()) continue;
    const r = await apiFetch('/contacts',{method:'POST',body:JSON.stringify(payload)});
    if(r) added++; else errors++;
  }
  alert(`Import complete. Added: ${added}, Errors: ${errors}`);
  loadContacts(); input.value='';
}

// ---- Pipeline ----
let pipelinePage=1, pipelineData=[], pipelineFilters={search:'',brand_id:'',owner_id:'',statuses:[]};
let pipelineSort='updated_at', pipelineSortDir='desc';

async function loadPipeline() {
  const p = new URLSearchParams({ page:pipelinePage, per_page:50, sort_by:pipelineSort, sort_dir:pipelineSortDir });
  if (pipelineFilters.search)   p.set('search',   pipelineFilters.search);
  if (pipelineFilters.brand_id) p.set('brand_id', pipelineFilters.brand_id);
  if (pipelineFilters.owner_id) p.set('owner_id', pipelineFilters.owner_id);
  if (pipelineFilters.statuses && pipelineFilters.statuses.length) p.set('statuses', pipelineFilters.statuses.join(','));
  const d = await apiFetch('/pipeline?'+p);
  if (!d) return;
  pipelineData = d.results;
  const sc = document.getElementById('sb-count-pipeline'); if(sc) sc.textContent=fmtNum(d.total);
  document.getElementById('pipeline-meta').innerHTML = `Showing <b>${fmtNum(d.results.length)}</b> of <b>${fmtNum(d.total)}</b> deals`;
  const psub = document.getElementById('pipeline-sub');
  if (psub) psub.innerHTML = fmtNum(d.total) + ' open deals &middot; USD ' + fmtShort(d.total_value||0) + ' total value';
  ['contact','brand','status','fob_date','owner','potential_value'].forEach(function(k){var el=document.getElementById('sort-pipeline-'+k);if(el)el.textContent=pipelineSort===k?sortIcon(pipelineSortDir):'';});
  const tbody = document.getElementById('pipeline-tbody');
  if (!d.results.length) { tbody.innerHTML='<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--warm-grey);">No pipeline entries found.</td></tr>'; return; }
  tbody.innerHTML = d.results.map(e=>`
    <tr data-id="${e.id}" style="cursor:pointer" onclick="openPipelineDetail(${e.id})">
      <td class="cell-checkbox"><span class="check"></span></td>
      <td class="contact-cell"><div class="nm">${escHtml(e.contact_company||e.contact_name||'—')}</div><div class="co">${e.contact_company?escHtml(e.contact_name||''):''}</div></td>
      <td>${brandMark(e.brand_name||'—')}</td>
      <td><span class="pill ${statusClass(e.status)}">${e.status}</span></td>
      <td class="value-cell">${fmtVal(e.potential_value)}</td>
      <td class="action-cell">${escHtml(e.next_action)||'—'}<div class="note">${e.notes?escHtml(e.notes.slice(0,60))+(e.notes.length>60?'…':''):''}</div></td>
      <td>${fmtDate(e.fob_date)}</td>
      <td>${ownerAv(e.owner_name)}</td>
      <td><button class="more-btn" onclick="event.stopPropagation();openPipelineDetail(${e.id})">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="12" r="1"></circle><circle cx="5" cy="12" r="1"></circle></svg>
      </button></td>
    </tr>`).join('');
  // Pipeline pagination
  var _totalPages = Math.ceil(d.total / 50);
  var _foot = document.getElementById('pipeline-foot');
  if (_foot) {
    var _s = (pipelinePage - 1) * 50 + 1, _e = Math.min(pipelinePage * 50, d.total);
    var _pg = '';
    if (_totalPages > 1) {
      _pg = '<div class="pager">';
      if (pipelinePage > 1) _pg += '<button class="pg-btn" onclick="pipelinePage='+(pipelinePage-1)+';loadPipeline()">&#8249;</button>';
      var _last = 0;
      for (var _pp = 1; _pp <= _totalPages; _pp++) {
        if (_pp === 1 || _pp === _totalPages || Math.abs(_pp - pipelinePage) <= 1) {
          if (_last && _pp - _last > 1) _pg += '<button class="pg-btn" disabled style="cursor:default">&#8230;</button>';
          _pg += '<button class="pg-btn'+(_pp===pipelinePage?' current':'')+'" onclick="pipelinePage='+_pp+';loadPipeline()">'+_pp+'</button>';
          _last = _pp;
        }
      }
      if (pipelinePage < _totalPages) _pg += '<button class="pg-btn" onclick="pipelinePage='+(pipelinePage+1)+';loadPipeline()">&#8250;</button>';
      _pg += '</div>';
    }
    _foot.innerHTML = '<span>Showing <b style="color:var(--navy)">'+fmtNum(_s)+'\u2013'+fmtNum(_e)+'</b> of <b style="color:var(--navy)">'+fmtNum(d.total)+'</b> deals</span>' + _pg;
  }
  if (boardViewActive) renderBoard();
}

function openPipelineDetail(id) {
  const e = pipelineData.find(x=>x.id===id); if(!e) return;
  const statuses = getPipelineStatuses();
  const users = window._crmUsers || [];
  document.getElementById('modal-title').innerHTML = escHtml((e.contact_company||e.contact_name||'') + ' — ' + (e.brand_name||''));
  document.getElementById('modal-body').innerHTML = `
    <form id="pe-edit-form" onsubmit="savePipelineEdit(event,${e.id})">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label class="fl">Status</label>
          <select name="status" id="pe-status-select" onchange="onPipelineStatusChange(this.value)" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            ${statuses.map(s=>`<option${s===e.status?' selected':''}>${s}</option>`).join('')}
          </select></div>
        <div><label class="fl">Owner</label>
          <select name="owner_id" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            ${users.map(u=>`<option value="${u.id}"${u.id===e.owner_id?' selected':''}>${u.name}</option>`).join('')}
          </select></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label class="fl">Potential Value</label>
          <input name="potential_value" type="number" step="0.01" value="${e.potential_value||0}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label class="fl">FOB Date</label>
          <input name="fob_date" type="date" value="${e.fob_date||''}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="margin-bottom:12px"><label class="fl">Next Action</label>
        <input name="next_action" value="${(e.next_action||'').replace(/"/g,'&quot;')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div id="pe-close-reason-wrap" style="${isLostStatus(e.status)?'':'display:none'}"><label class="fl">Close Reason </label>
        ${buildCloseReasonSelect(e.close_reason||'')}</div>
      <div id="pe-edit-error" style="display:none;color:#B33A47;font-size:13px;margin-bottom:12px;padding:10px;background:#FAE3E5;border-radius:8px"></div>
    </form>
    <div style="border-top:1px solid var(--line);padding-top:16px;margin-top:4px">
      <div style="font-size:13px;font-weight:600;color:var(--navy);margin-bottom:12px">Notes</div>
      <div id="pipeline-notes-list"><div style="font-size:13px;color:var(--warm-grey)">Loading…</div></div>
      ${e.notes?`<div style="margin-bottom:12px;padding:10px 12px;background:var(--off-white);border-radius:8px;font-size:12px"><span style="font-weight:600;color:var(--warm-grey)">Legacy note:</span> <span style="white-space:pre-wrap">${escHtml(e.notes)}</span></div>`:''}
      <div style="margin-top:8px">
        <label class="fl">Add Note</label>
        <textarea id="new-pipeline-note-body" rows="3" placeholder="Type a note…" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;resize:vertical;margin-bottom:8px;box-sizing:border-box"></textarea>
        <button onclick="addPipelineNote(${e.id})" class="btn btn-primary" style="font-size:13px">Add Note</button>
      </div>
    </div>`;
  const isAdminPE = CURRENT_USER && CURRENT_USER.role === 'admin';
  document.getElementById('modal-footer').innerHTML = `
    <button class="btn btn-secondary" onclick="document.getElementById('modal').style.display='none'">Cancel</button>
    ${isAdminPE ? `<button class="btn btn-secondary" style="color:#B33A47" onclick="deletePipelineEntry(${e.id})">Delete</button>` : ''}
    <button class="btn btn-secondary" onclick="openConvertToOrderModal(${e.id})">Convert to Order</button>
    <button class="btn btn-primary" onclick="document.getElementById('pe-edit-form').requestSubmit()">Save</button>`;
  document.getElementById('modal').style.display = 'flex';
  loadPipelineNotes(e.id);
}

async function savePipelineEdit(evt, id) {
  evt.preventDefault();
  const e = pipelineData.find(x=>x.id===id); if(!e) return;
  const fd = new FormData(evt.target);
  const newStatus = fd.get('status');
  const closeReasonRaw = fd.get('close_reason');
  const payload = {
    contact_id:      e.contact_id,
    brand_id:        e.brand_id,
    status:          newStatus,
    potential_value: parseFloat(fd.get('potential_value'))||0,
    next_action:     fd.get('next_action')||null,
    fob_date:        fd.get('fob_date')||null,
    owner_id:        parseInt(fd.get('owner_id')),
  };
  if (isLostStatus(newStatus)) {
    const reason = (closeReasonRaw || '').trim();
    if (!reason) {
      document.getElementById('pe-edit-error').textContent = 'A close reason is required for this status.';
      document.getElementById('pe-edit-error').style.display = 'block';
      return;
    }
    payload.close_reason = reason;
  }
  const btn = document.querySelector('#modal-footer .btn-primary');
  if (btn) { btn.textContent='Saving…'; btn.disabled=true; }
  const result = await apiFetch('/pipeline/'+id, {method:'PUT', body:JSON.stringify(payload)});
  if (result) {
    document.getElementById('modal').style.display='none';
    showToast('Pipeline entry saved');
    loadPipeline();
  } else {
    document.getElementById('pe-edit-error').textContent='Failed to save. Please try again.';
    document.getElementById('pe-edit-error').style.display='block';
    if (btn) { btn.textContent='Save'; btn.disabled=false; }
  }
}


function sortPipeline(col) {
  if (pipelineSort===col) pipelineSortDir = pipelineSortDir==='asc'?'desc':'asc';
  else { pipelineSort=col; pipelineSortDir='asc'; }
  pipelinePage=1; loadPipeline();
}

async function exportOrders() {
  const d = await apiFetch('/orders?per_page=5000');
  if (!d || !d.orders || !d.orders.length) { showToast('No orders to export'); return; }
  const cols = ['Contact','Company','Brand','Owner','Order Date','Value','Currency','Commission %','Testing Ded.','Net Commission','Status'];
  const rows = d.orders.map(function(o) { return [
    o.contact_name||'', o.contact_company||'', o.brand_name||'', o.owner_name||'',
    o.order_date||'', o.order_value||0, o.currency||'USD',
    o.gross_commission_rate||0, o.testing_deduction||0, o.net_commission||0, o.status||''
  ]; });
  const csv = [cols, ...rows].map(function(r) {
    return r.map(function(v) { return '"'+String(v).replace(/"/g,'""')+'"'; }).join(',');
  }).join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], {type:'text/csv'}));
  a.download = 'orders_export.csv'; a.click();
  showToast('Exported ' + d.orders.length + ' orders');
}

async function exportPipeline() {
  const p = new URLSearchParams({ per_page:5000, sort_by:pipelineSort, sort_dir:pipelineSortDir });
  if (pipelineFilters.search)   p.set('search',   pipelineFilters.search);
  if (pipelineFilters.brand_id) p.set('brand_id', pipelineFilters.brand_id);
  if (pipelineFilters.owner_id) p.set('owner_id', pipelineFilters.owner_id);
  if (pipelineFilters.statuses && pipelineFilters.statuses.length) p.set('statuses', pipelineFilters.statuses.join(','));
  const d = await apiFetch('/pipeline?'+p);
  if (!d || !d.results.length) { showToast('No data to export'); return; }
  const cols = ['Company','Contact','Brand','Status','Potential Value','Next Action','FOB Date','Owner','Notes'];
  const rows = d.results.map(e => [
    e.contact_company||'', e.contact_name||'', e.brand_name||'', e.status||'',
    e.potential_value||0, e.next_action||'', e.fob_date||'', e.owner_name||'', (e.notes||'').replace(/,/g,' ')
  ]);
  const csv = [cols, ...rows].map(r => r.map(v => '"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  a.download = 'pipeline_export.csv'; a.click();
  showToast('Exported ' + d.results.length + ' deals');
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
  var p = new URLSearchParams({ per_page:500, sort_by:pipelineSort, sort_dir:pipelineSortDir });
  if (pipelineFilters.search)   p.set('search',   pipelineFilters.search);
  if (pipelineFilters.brand_id) p.set('brand_id', pipelineFilters.brand_id);
  if (pipelineFilters.owner_id) p.set('owner_id', pipelineFilters.owner_id);
  if (pipelineFilters.statuses && pipelineFilters.statuses.length) p.set('statuses', pipelineFilters.statuses.join(','));
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
            + '<div style="font-weight:600;color:var(--navy);font-size:13px;margin-bottom:2px">' + escHtml(e.contact_company||e.contact_name||'—') + '</div>'
            + '<div style="font-size:11px;color:var(--warm-grey);margin-bottom:4px">' + escHtml(e.brand_name||'') + (groupBy!=='status'?' · <span class="pill ' + statusClass(e.status) + '" style="font-size:10px">' + escHtml(e.status) + '</span>':'') + '</div>'
            + '<div style="display:flex;justify-content:space-between;align-items:center">'
            + '<span style="font-size:12px;font-weight:600;color:var(--logo-blue-dark)">USD ' + fmtNum(e.potential_value||0) + '</span>'
            + ownerAv(e.owner_name)
            + '</div></div>';
        }).join('')
      + '</div></div>';
  }).join('');
}

// ---- New Deal modal ----
async function openNewDealModal(preContactId) {
  const [cData, bData, uData] = await Promise.all([apiFetch('/contacts?source=contacts&per_page=200'), apiFetch('/brands'), apiFetch('/users')]);
  const contacts = cData?cData.results:[], brands=bData||[], users=uData||[];
  const statuses = getPipelineStatuses();
  document.getElementById('modal-title').innerHTML = 'New Pipeline Entry';
  document.getElementById('modal-body').innerHTML = `
    <form id="new-deal-form" onsubmit="saveNewDeal(event)">
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Contact / Company *</label>
        <select name="contact_id" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
          <option value="">— Select —</option>
          ${contacts.map(c=>`<option value="${c.id}" ${preContactId===c.id?'selected':''}>${c.name}${c.company&&c.company!==c.name?' ('+c.company+')':''}</option>`).join('')}
        </select></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Brand *</label>
          <select name="brand_id" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            <option value="">— Select —</option>
            ${brands.map(b=>`<option value="${b.id}">${b.name}</option>`).join('')}
          </select></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Status *</label>
          <select name="status" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            ${statuses.map(s=>`<option>${s}</option>`).join('')}
          </select></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Potential Value (USD) *</label>
          <input name="potential_value" type="number" min="0" required placeholder="0" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Owner *</label>
          <select name="owner_id" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            ${users.map(u=>`<option value="${u.id}" ${u.name===CURRENT_USER?.name?'selected':''}>${u.name}</option>`).join('')}
          </select></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">FOB Date</label>
          <input name="fob_date" type="date" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Next Action</label>
          <input name="next_action" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="margin-bottom:20px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Notes</label>
        <textarea name="notes" rows="3" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;resize:vertical"></textarea></div>
      <div id="nd-error" style="display:none;color:#B33A47;font-size:13px;margin-bottom:12px;padding:10px;background:#FAE3E5;border-radius:8px"></div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" onclick="document.getElementById('modal').style.display='none'" class="btn btn-secondary">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Deal</button>
      </div>
    </form>`;
  document.getElementById('modal').style.display = 'flex';
}

async function openConvertToOrderModal(pipelineId) {
  const e = pipelineData.find(x=>x.id===pipelineId); if(!e) return;
  const statuses = getOrderStatuses();
  document.getElementById('modal-title').innerHTML = 'Convert to Order';
  document.getElementById('modal-footer').innerHTML = '';
  document.getElementById('modal-body').innerHTML = `
    <form id="convert-order-form" onsubmit="saveConvertedOrder(event,${pipelineId})">
      <div style="background:var(--logo-blue-pale);border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px">
        <b>${escHtml(e.contact_company||e.contact_name||'—')}</b> · ${escHtml(e.brand_name||'—')}
        <span class="pill blue" style="margin-left:8px">PO Received</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label class="fl">Order Date *</label>
          <input name="order_date" type="date" required value="${new Date().toISOString().slice(0,10)}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label class="fl">PO Date</label>
          <input name="po_date" type="date" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label class="fl">Order Value (USD) *</label>
          <input name="order_value" type="number" min="0" step="0.01" required placeholder="0" value="${e.potential_value||''}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label class="fl">Commission Rate %</label>
          <input name="gross_commission_rate" type="number" min="0" step="0.01" placeholder="0" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label class="fl">Testing Cost Deduction (USD)</label>
          <input name="testing_cost_deduction" type="number" min="0" step="0.01" placeholder="0" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label class="fl">Ship Date (optional)</label>
          <input name="ship_date" type="date" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
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
  const commRate = parseFloat(fd.get('gross_commission_rate'))||0;
  const testCost  = parseFloat(fd.get('testing_cost_deduction'))||0;
  const payload = {
    contact_id: e.contact_id,
    brand_id: e.brand_id,
    order_date: fd.get('order_date'),
    order_value: parseFloat(fd.get('order_value'))||0,
    currency: 'USD',
    gross_commission_rate: commRate,
    testing_cost_deduction: testCost,
    owner_id: e.owner_id || null,
    po_date:      fd.get('po_date')      || null,
    ship_date:    fd.get('ship_date')    || null,
    status: 'po_received',
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


async function saveNewDeal(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = { contact_id:parseInt(fd.get('contact_id')), brand_id:parseInt(fd.get('brand_id')),
    status:fd.get('status'), potential_value:parseFloat(fd.get('potential_value'))||0,
    owner_id:parseInt(fd.get('owner_id')), fob_date:fd.get('fob_date')||null,
    next_action:fd.get('next_action')||null, notes:fd.get('notes')||null };
  const btn = e.target.querySelector('[type=submit]'); btn.textContent='Saving…'; btn.disabled=true;
  const result = await apiFetch('/pipeline',{method:'POST',body:JSON.stringify(payload)});
  if (result) { document.getElementById('modal').style.display='none'; loadPipeline(); }
  else { document.getElementById('nd-error').textContent='Failed. Check all required fields.'; document.getElementById('nd-error').style.display='block'; btn.textContent='Save Deal'; btn.disabled=false; }
}

// ---- Agent Bonus Widget ----
async function loadMyBonus() {
  const d = await apiFetch('/reports/my-bonus');
  const widget = document.getElementById('agent-bonus-widget');
  if (!d || !widget) return;
  var titleEl = document.getElementById('bonus-widget-title');
  var subEl = document.getElementById('bonus-widget-sub');
  var bodyEl = document.getElementById('bonus-widget-body');
  if (titleEl) titleEl.textContent = 'My Bonus — ' + (d.current_quarter||'');
  if (subEl) subEl.textContent = 'Commission Paid: $' + fmtShort(d.summary.total_paid||0) + '  ·  Pending: $' + fmtShort(d.summary.total_pending||0);
  if (!bodyEl) return;
  if (!d.orders||!d.orders.length) {
    bodyEl.innerHTML = '<div style="padding:12px 0;color:var(--warm-grey);font-size:13px">No orders in progress this quarter.</div>';
  } else {
    var STATUS_COLOR = {shipped:'amber',fully_paid:'amber',commission_invoiced:'amber',commission_paid:'green',bonus_paid:'grey'};
    var STATUS_LABEL = {shipped:'Shipped',fully_paid:'Fully Paid',commission_invoiced:'Comm. Invoiced',commission_paid:'Comm. Paid',bonus_paid:'Bonus Paid'};
    bodyEl.innerHTML = '<table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:12px">'
      + '<thead><tr style="color:var(--warm-grey);font-size:11px">'
      + '<th style="text-align:left;padding:4px 0">Contact</th><th style="text-align:left;padding:4px 0">Brand</th>'
      + '<th style="text-align:right;padding:4px 0">Net Commission</th><th style="text-align:right;padding:4px 0">My Bonus</th><th style="text-align:center;padding:4px 0">Status</th>'
      + '</tr></thead><tbody>'
      + d.orders.map(function(o){
          var pc = STATUS_COLOR[o.status]||'blue';
          var rowStyle = o.status==='bonus_paid'?'color:var(--warm-grey)':'';
          return '<tr style="border-bottom:1px solid var(--line);'+rowStyle+'">'
            +'<td style="padding:6px 0">'+escHtml(o.contact_name||'—')+'</td>'
            +'<td style="padding:6px 0">'+escHtml(o.brand_name||'—')+'</td>'
            +'<td style="text-align:right;padding:6px 0">'+fmtVal(o.net_commission)+'</td>'
            +'<td style="text-align:right;padding:6px 0;font-weight:700;color:#8E44AD">'+fmtVal(o.bonus_amount)+'</td>'
            +'<td style="text-align:center;padding:6px 0"><span class="pill '+pc+'" style="font-size:10px">'+escHtml(STATUS_LABEL[o.status]||o.status)+'</span></td>'
            +'</tr>';
        }).join('')
      + '</tbody></table>'
      + '<div style="font-size:13px;border-top:1px solid var(--line);padding-top:10px">'
      + '<b>This quarter:</b> $'+fmtShort(d.summary.total_earned||0)+' earned, <span style="color:var(--st-green-fg)">$'+fmtShort(d.summary.total_paid||0)+' paid</span>, <span style="color:#C97B2B">$'+fmtShort(d.summary.total_pending||0)+' pending</span>'
      + (d.next_quarter_pipeline?'<br><b>Next quarter estimate:</b> <span style="color:#8E44AD">$'+fmtShort(d.next_quarter_pipeline)+' projected</span>':'')
      + '</div>';
  }
}

// ---- Admin Bonus Widget ----
async function loadAdminBonusWidget() {
  const d = await apiFetch('/reports/bonus-summary');
  const widget = document.getElementById('admin-bonus-widget');
  const body = document.getElementById('admin-bonus-body');
  if (!d || !widget || !body) return;
  document.getElementById('admin-bonus-title').textContent = 'Staff Bonus — ' + (d.quarter||'');
  document.getElementById('admin-bonus-sub').textContent = 'Outstanding: $' + fmtShort(d.grand_total_outstanding||0) + '  ·  Paid: $' + fmtShort(d.grand_total_paid||0);
  if (!d.staff || !d.staff.length) { body.innerHTML = '<div style="padding:12px 0;color:var(--warm-grey);font-size:13px">No bonus data this quarter.</div>'; return; }
  var STATUS_COLOR = {shipped:'amber',fully_paid:'amber',commission_invoiced:'amber',commission_paid:'green',bonus_paid:'grey'};
  var STATUS_LABEL = {shipped:'Shipped',fully_paid:'Fully Paid',commission_invoiced:'Comm. Invoiced',commission_paid:'Comm. Paid',bonus_paid:'Bonus Paid'};
  var html = '';
  d.staff.forEach(function(member) {
    if (!member.orders.length) return;
    html += '<div style="margin-bottom:16px">'
      + '<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey);padding:6px 0 4px;border-bottom:1px solid var(--line);margin-bottom:6px">' + escHtml(member.owner_name) + '</div>'
      + '<table style="width:100%;border-collapse:collapse;font-size:12px">'
      + '<thead><tr style="color:var(--warm-grey);font-size:11px">'
      + '<th style="text-align:left;padding:3px 0">Contact</th>'
      + '<th style="text-align:left;padding:3px 0">Brand</th>'
      + '<th style="text-align:right;padding:3px 0">Net Comm.</th>'
      + '<th style="text-align:right;padding:3px 0">Bonus</th>'
      + '<th style="text-align:center;padding:3px 0">Status</th>'
      + '<th style="text-align:center;padding:3px 0">Paid</th>'
      + '</tr></thead><tbody>'
      + member.orders.map(function(o) {
          var pc = STATUS_COLOR[o.status] || 'blue';
          var rowStyle = o.status === 'bonus_paid' ? 'color:var(--warm-grey)' : '';
          return '<tr style="border-bottom:1px solid var(--line);' + rowStyle + '">'
            + '<td style="padding:5px 0">' + escHtml(o.contact_name||'—') + '</td>'
            + '<td style="padding:5px 0">' + escHtml(o.brand_name||'—') + '</td>'
            + '<td style="text-align:right;padding:5px 0">' + fmtVal(o.net_commission) + '</td>'
            + '<td style="text-align:right;padding:5px 0;font-weight:700;color:#8E44AD">' + fmtVal(o.bonus_amount) + '</td>'
            + '<td style="text-align:center;padding:5px 0"><span class="pill ' + pc + '" style="font-size:10px">' + escHtml(STATUS_LABEL[o.status]||o.status) + '</span></td>'
            + '<td style="text-align:center;padding:5px 0">' + (o.bonus_paid ? '<span class="pill green" style="font-size:10px">Paid</span>' : '<span class="pill grey" style="font-size:10px">No</span>') + '</td>'
            + '</tr>';
        }).join('')
      + '</tbody></table>'
      + '<div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;font-size:12px">'
      + '<span>Earned: <b style="color:#8E44AD">$' + fmtShort(member.total_bonus_earned||0) + '</b>  ·  Paid: <b style="color:var(--st-green-fg)">$' + fmtShort(member.total_bonus_paid||0) + '</b>  ·  Outstanding: <b>$' + fmtShort(member.total_bonus_outstanding||0) + '</b></span>'
      + '<button class="btn btn-secondary" style="font-size:11px;padding:3px 10px" onclick="markBonusPaid(' + member.owner_id + ')">Mark Bonus Paid</button>'
      + '</div></div>';
  });
  html += '<div style="padding-top:10px;border-top:2px solid var(--line);font-size:13px;font-weight:700">'
    + 'Total outstanding: <span style="color:#8E44AD">$' + fmtShort(d.grand_total_outstanding||0) + '</span>'
    + '  ·  Total paid: <span style="color:var(--st-green-fg)">$' + fmtShort(d.grand_total_paid||0) + '</span>'
    + '</div>';
  body.innerHTML = html;
}

async function markBonusPaid(ownerId) {
  const d = await apiFetch('/reports/bonus-summary');
  if (!d) return;
  var member = d.staff.find(function(s){ return s.owner_id === ownerId; });
  if (!member) return;
  var ids = member.orders.filter(function(o){ return o.status === 'commission_paid' && !o.bonus_paid; }).map(function(o){ return o.order_id; });
  if (!ids.length) { alert('No commission_paid orders to mark.'); return; }
  if (!confirm('Mark ' + ids.length + ' order(s) as Bonus Paid for ' + member.owner_name + '?')) return;
  var r = await apiFetch('/orders/mark-bonus-paid', {method:'PUT', body:JSON.stringify({order_ids:ids})});
  if (r) { showToast(r.updated + ' order(s) marked as Bonus Paid'); loadAdminBonusWidget(); }
}

// ---- Commission Forecast Report ----
async function loadCommissionForecast() {
  const overlay = document.getElementById('report-overlay');
  const body = document.getElementById('report-overlay-body');
  document.getElementById('report-overlay-title').textContent = 'Commission Forecast';
  overlay.style.display = 'flex';
  body.innerHTML = '<div style="padding:40px;text-align:center;color:var(--warm-grey)">Loading…</div>';
  const d = await apiFetch('/reports/commission-forecast'); if(!d){body.innerHTML='<div style="padding:40px;text-align:center;color:#B33A47">Failed to load report.</div>';return;}
  var COLS = ['actual_received','confirmed','weighted_pipeline','total_forecast'];
  var LABELS = {actual_received:'Actual Received',confirmed:'Confirmed',weighted_pipeline:'Weighted Pipeline',total_forecast:'Total Forecast'};
  var COLORS = {actual_received:'var(--st-green-fg)',confirmed:'var(--logo-blue)',weighted_pipeline:'#C97B2B',total_forecast:'var(--navy)'};
  var months = d.months||[];
  var html = '<div style="padding:16px;overflow-x:auto">';
  html += '<div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap">';
  [d.fy_current, d.fy_next].forEach(function(fy){
    if(!fy) return;
    html += '<div style="flex:1;min-width:220px;background:var(--off-white);border-radius:10px;padding:14px 16px">'
      + '<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey);margin-bottom:8px">'+escHtml(fy.label)+'</div>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">'
      + COLS.map(function(k){return '<div><div style="font-size:10px;color:var(--warm-grey)">'+LABELS[k]+'</div><div style="font-size:14px;font-weight:700;color:'+COLORS[k]+'">$'+fmtShort(fy[k]||0)+'</div></div>';}).join('')
      + '</div></div>';
  });
  html += '</div>';
  html += '<table style="width:100%;border-collapse:collapse;font-size:12px;white-space:nowrap">'
    + '<thead><tr><th style="text-align:left;padding:6px 10px;border-bottom:2px solid var(--line);color:var(--warm-grey);font-size:11px"></th>'
    + months.map(function(m){
        var hl = m.is_current ? 'background:var(--logo-blue-pale);' : '';
        return '<th style="text-align:right;padding:6px 8px;border-bottom:2px solid var(--line);'+hl+'font-size:11px;color:'+(m.is_current?'var(--logo-blue)':'var(--warm-grey)')+'">'+escHtml(m.label)+'</th>';
      }).join('')
    + '</tr></thead><tbody>'
    + COLS.map(function(k){
        var bold = k==='total_forecast' ? 'font-weight:700;' : '';
        return '<tr>'
          + '<td style="padding:6px 10px;font-weight:600;color:'+COLORS[k]+';white-space:nowrap">'+LABELS[k]+'</td>'
          + months.map(function(m){
              var hl = m.is_current ? 'background:var(--logo-blue-pale);' : '';
              var v = m[k]||0;
              return '<td style="text-align:right;padding:6px 8px;border-bottom:1px solid var(--line);'+hl+bold+'color:'+COLORS[k]+'">'+(v?'$'+fmtShort(v):'—')+'</td>';
            }).join('')
          + '</tr>';
      }).join('')
    + '</tbody></table>'
    + '<div style="margin-top:12px"><button class="btn btn-secondary" onclick="exportCommissionCSV()">&#8595; Export CSV</button></div>'
    + '</div>';
  body.innerHTML = html;
}

function exportCommissionCSV() {
  apiFetch('/reports/commission-forecast').then(function(d){
    if(!d) return;
    var cols = ['Month','Actual Received','Confirmed','Weighted Pipeline','Total Forecast'];
    var rows = d.months.map(function(m){return[m.label,m.actual_received,m.confirmed,m.weighted_pipeline,m.total_forecast];});
    var csv = [cols.join(',')].concat(rows.map(function(r){return r.join(',');})).join(String.fromCharCode(10));
    var a=document.createElement('a');a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);a.download='commission_forecast.csv';a.click();
  });
}

// ---- Bonus Report ----
var bonusReportFY = 2026, bonusReportQ = 1;

async function loadBonusReport() {
  const overlay = document.getElementById('report-overlay');
  const body = document.getElementById('report-overlay-body');
  document.getElementById('report-overlay-title').textContent = 'Bonus Report';
  overlay.style.display = 'flex';
  body.innerHTML = '<div style="padding:16px">'
    + '<div style="display:flex;gap:8px;align-items:center;margin-bottom:16px;flex-wrap:wrap">'
    + '<label style="font-size:13px;font-weight:600;color:var(--navy)">Quarter:</label>'
    + '<select id="bonus-fy-sel" onchange="bonusReportFY=parseInt(this.value);loadBonusReportData()" style="border:1px solid var(--line);border-radius:8px;padding:6px 10px;font:inherit;font-size:13px">'
    + [2026,2027].map(function(y){return '<option value="'+y+'"'+(y===bonusReportFY?' selected':'')+'>FY'+y+'-'+(y+1).toString().slice(2)+'</option>';}).join('')
    + '</select>'
    + '<select id="bonus-q-sel" onchange="bonusReportQ=parseInt(this.value);loadBonusReportData()" style="border:1px solid var(--line);border-radius:8px;padding:6px 10px;font:inherit;font-size:13px">'
    + [1,2,3,4].map(function(q){return '<option value="'+q+'"'+(q===bonusReportQ?' selected':'')+'>'+'Q'+q+'</option>';}).join('')
    + '</select>'
    + '</div>'
    + '<div id="bonus-report-content"><div style="padding:20px;text-align:center;color:var(--warm-grey)">Loading…</div></div></div>';
  await loadBonusReportData();
}

async function loadBonusReportData() {
  const d = await apiFetch('/reports/bonus?fy='+bonusReportFY+'&quarter=Q'+bonusReportQ);
  const cont = document.getElementById('bonus-report-content');
  if (!cont) return;
  if (!d) { cont.innerHTML='<div style="padding:20px;text-align:center;color:#B33A47">Failed to load.</div>'; return; }
  var html = '<div style="font-size:13px;font-weight:700;color:var(--navy);margin-bottom:16px">'+escHtml(d.quarter)+'</div>';
  d.agents.forEach(function(agent){
    html += '<div style="margin-bottom:20px">'
      + '<div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey);padding:8px 0;border-bottom:2px solid var(--line);margin-bottom:8px">'+escHtml(agent.owner_name)+'</div>';
    if (!agent.orders.length) {
      html += '<div style="color:var(--warm-grey);font-size:13px;padding:8px 0">No qualifying orders this quarter.</div>';
    } else {
      html += '<table style="width:100%;border-collapse:collapse;font-size:13px">'
        + '<thead><tr style="color:var(--warm-grey);font-size:11px">'
        + '<th style="text-align:left;padding:4px 8px">Contact</th><th style="text-align:left;padding:4px 8px">Brand</th>'
        + '<th style="text-align:right;padding:4px 8px">Net Commission</th><th style="text-align:right;padding:4px 8px">Bonus</th>'
        + '<th style="text-align:center;padding:4px 8px">Commission Paid</th><th style="text-align:center;padding:4px 8px">Bonus Paid</th>'
        + '</tr></thead><tbody>'
        + agent.orders.map(function(o){
            return '<tr style="border-bottom:1px solid var(--line)">'
              +'<td style="padding:6px 8px">'+escHtml(o.contact_name||'—')+'</td>'
              +'<td style="padding:6px 8px">'+escHtml(o.brand_name||'—')+'</td>'
              +'<td style="text-align:right;padding:6px 8px">'+fmtVal(o.net_commission)+'</td>'
              +'<td style="text-align:right;padding:6px 8px;font-weight:700;color:#8E44AD">'+fmtVal(o.bonus_amount)+'</td>'
              +'<td style="text-align:center;padding:6px 8px;color:var(--warm-grey);font-size:11px">'+escHtml(o.commission_paid_date||'—')+'</td>'
              +'<td style="text-align:center;padding:6px 8px">'+(o.bonus_paid?'<span class="pill green" style="font-size:10px">Paid</span>':'<span class="pill amber" style="font-size:10px">Pending</span>')+'</td>'
              +'</tr>';
          }).join('')
        + '</tbody></table>'
        + '<div style="margin-top:8px;text-align:right;font-size:13px">'
        + 'Total commission: <b>'+fmtVal(agent.total_net_commission)+'</b> &nbsp;·&nbsp; Total bonus: <b style="color:#8E44AD">'+fmtVal(agent.total_bonus)+'</b>'
        + '</div>'
        + '<div style="margin-top:8px">'
        + '<button class="btn btn-secondary" style="font-size:12px" onclick="markAllBonusPaid('+JSON.stringify(agent.orders.map(function(o){return o.order_id;}))+')">Mark all as Bonus Paid</button>'
        + '</div>';
    }
    html += '</div>';
  });
  html += '<div style="margin-top:16px;padding-top:16px;border-top:2px solid var(--line);font-size:14px;font-weight:700;color:#8E44AD">Grand Total Bonus: '+fmtVal(d.grand_total_bonus)+'</div>';
  cont.innerHTML = html;
}

async function markAllBonusPaid(orderIds) {
  if (!orderIds.length) return;
  if (!confirm('Mark '+orderIds.length+' order(s) as Bonus Paid?')) return;
  var done = 0;
  for (var i=0;i<orderIds.length;i++) {
    var r = await apiFetch('/orders/'+orderIds[i]+'/advance-status',{method:'POST',body:JSON.stringify({status:'bonus_paid'})});
    if (r) done++;
  }
  showToast(done+' order(s) marked as Bonus Paid');
  loadBonusReportData();
}

// ---- Reports ----
let qFilter = 'all', qCurrentPage = 1, qPerPage = 50;


function openReport(type) {
  if (type === 'lost-deals') {
    var lo = document.getElementById('report-overlay');
    if (lo) lo.style.display = 'flex';
    loadLostDealsReport();
    return;
  }
  const overlay = document.getElementById('report-overlay');
  const title   = document.getElementById('report-overlay-title');
  const body    = document.getElementById('report-overlay-body');
  overlay.style.display = 'flex';

  if (type === 'quality') {
    title.textContent = 'Data Quality Audit';
    body.innerHTML =
      '<div style="display:flex;align-items:center;gap:6px;padding:14px 24px;flex-wrap:wrap;border-bottom:1px solid var(--line)">' +
        '<button id="qf-all" class="qf-pill qf-pill-active" onclick="setQFilter(\'all\')">All</button>' +
        '<button id="qf-missing" class="qf-pill" onclick="setQFilter(\'missing\')">Missing Fields</button>' +
        '<button id="qf-complete" class="qf-pill" onclick="setQFilter(\'complete\')">Complete</button>' +
        '<button id="qf-invalid_country" class="qf-pill" onclick="setQFilter(\'invalid_country\')">Invalid Country</button>' +
        '<button id="qf-wrong_region" class="qf-pill" onclick="setQFilter(\'wrong_region\')">Wrong Region</button>' +
        '<select id="q-owner" onchange="qCurrentPage=1;loadQualityReport()" style="padding:6px 10px;font:inherit;font-size:12px;color:var(--navy);border:1px solid var(--line);border-radius:6px;background:var(--white);cursor:pointer;margin-left:4px"><option value="">All owners</option></select>' +
        '<input id="q-search" placeholder="Search…" style="border:1px solid var(--line);border-radius:6px;padding:6px 12px;font:inherit;font-size:13px;width:180px" oninput="clearTimeout(window._qt);window._qt=setTimeout(loadQualityReport,400)"/>' +
        '<button onclick="downloadQualityCSV()" style="padding:7px 18px;background:#76BCE0;color:#fff;border:none;border-radius:6px;font:inherit;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;cursor:pointer;margin-left:auto;white-space:nowrap">Download CSV</button>' +
      '</div>' +
      '<div style="display:flex;border-bottom:1px solid var(--line)">' +
        '<div class="q-tile" style="border-top:3px solid #76BCE0"><div class="q-tile-num" id="qt-total">&mdash;</div><div class="q-tile-lbl">Total contacts</div></div>' +
        '<div class="q-tile" style="border-top:3px solid #E57373"><div class="q-tile-num" id="qt-missing">&mdash;</div><div class="q-tile-lbl">Missing fields</div></div>' +
        '<div class="q-tile" style="border-top:3px solid #4CAF50"><div class="q-tile-num" id="qt-complete">&mdash;</div><div class="q-tile-lbl">Fully complete</div></div>' +
        '<div class="q-tile" style="border-top:3px solid #E57373"><div class="q-tile-num" id="qt-invalid-country">&mdash;</div><div class="q-tile-lbl">Invalid country</div></div>' +
        '<div class="q-tile" style="border-top:3px solid #F59E0B"><div class="q-tile-num" id="qt-region">&mdash;</div><div class="q-tile-lbl">Wrong region</div></div>' +
      '</div>' +
      '<div style="padding:8px 24px;font-size:12px;color:var(--warm-grey)" id="q-row-count"></div>' +
      '<table class="data" id="q-table">' +
        '<thead style="background:#EBF5FB"><tr>' +
          '<th style="padding-left:24px">Contact</th>' +
          '<th style="width:160px">Score</th>' +
          '<th>Missing Fields</th>' +
          '<th>Country</th>' +
          '<th>Owner</th>' +
          '<th style="width:130px">Status</th>' +
        '</tr></thead>' +
        '<tbody id="q-tbody"><tr><td colspan="6" style="text-align:center;padding:40px;color:var(--warm-grey)">Loading…</td></tr></tbody>' +
      '</table>' +
      '<div style="display:flex;align-items:center;justify-content:space-between;padding:12px 24px;border-top:1px solid var(--line)">' +
        '<button class="btn btn-secondary" id="q-prev" onclick="qPage(-1)" style="font-size:12px;padding:5px 12px">&larr; Previous</button>' +
        '<span id="q-page-info" style="font-size:12px;color:var(--warm-grey)"></span>' +
        '<button class="btn btn-secondary" id="q-next" onclick="qPage(1)" style="font-size:12px;padding:5px 12px">Next &rarr;</button>' +
      '</div>';
    qFilter = 'all'; qCurrentPage = 1;
    apiFetch('/users').then(function(users) {
      var od = document.getElementById('q-owner');
      if (od && users) od.innerHTML = '<option value="">All owners</option>' + users.map(function(u){ return '<option value="'+u.id+'">'+escHtml(u.name)+'</option>'; }).join('');
      loadQualityReport();
    });

  } else if (type === 'activity') {
    title.textContent = 'Activity Report';
    body.innerHTML =
      '<div style="padding:16px 24px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px;flex-wrap:wrap">' +
        '<span style="font-size:13px;color:var(--warm-grey)">Period:</span>' +
        '<select id="reports-period" onchange="loadActivityReport()" style="padding:7px 12px;font:inherit;font-size:13px;color:var(--navy);border:1px solid var(--line);border-radius:8px;background:var(--white)">' +
          '<option value="1d">Today</option>' +
          '<option value="7d">Last 7 days</option>' +
          '<option value="30d" selected>Last 30 days</option>' +
          '<option value="90d">Last 90 days</option>' +
          '<option value="365d">Last 12 months</option>' +
        '</select>' +
        '<span style="font-size:13px;color:var(--warm-grey);margin-left:8px">User:</span>' +
        '<select id="reports-owner" onchange="loadActivityReport()" style="padding:7px 12px;font:inherit;font-size:13px;color:var(--navy);border:1px solid var(--line);border-radius:8px;background:var(--white)">' +
          '<option value="">All users</option>' +
        '</select>' +
      '</div>' +
      '<div id="reports-activity-body" style="padding:24px;color:var(--warm-grey);text-align:center">Loading…</div>';
    apiFetch('/users').then(function(users) {
      var sel = document.getElementById('reports-owner');
      if (sel && users) sel.innerHTML = '<option value="">All users</option>' + users.map(function(u){ return '<option value="'+u.id+'">'+escHtml(u.name)+'</option>'; }).join('');
      loadActivityReport();
    });

  } else if (type === 'tasks') {
    title.textContent = 'Task Report';
    const taskWrap = document.createElement('div');
    taskWrap.innerHTML =
      '<div style="padding:16px 24px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px">' +
        '<span style="font-size:13px;color:var(--warm-grey)">Filter:</span>' +
        '<select id="task-report-filter" style="padding:7px 12px;font:inherit;font-size:13px;color:var(--navy);border:1px solid var(--line);border-radius:8px;background:var(--white)">' +
          '<option value="open">Open</option>' +
          '<option value="overdue">Overdue</option>' +
          '<option value="all">All</option>' +
          '<option value="completed">Completed</option>' +
        '</select>' +
      '</div>' +
      '<table class="data" style="margin:0">' +
        '<thead style="background:#EBF5FB"><tr><th>Contact</th><th>Task</th><th>Assigned To</th><th>Due Date</th><th>Status</th></tr></thead>' +
        '<tbody id="task-report-body"><tr><td colspan="5" style="text-align:center;padding:40px;color:var(--warm-grey)">Loading…</td></tr></tbody>' +
      '</table>';
    body.innerHTML = '';
    body.appendChild(taskWrap);
    var trSel = taskWrap.querySelector('#task-report-filter');
    var trTbody = taskWrap.querySelector('#task-report-body');
    var _renderTasks = async function(filter) {
      trTbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--warm-grey)">Loading…</td></tr>';
      var data = await apiFetch('/reports/tasks?filter=' + filter);
      if (!data) { trTbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:#B33A47">Failed to load.</td></tr>'; return; }
      if (!data.length) { trTbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--warm-grey)">No tasks found.</td></tr>'; return; }
      var today = new Date().toISOString().slice(0,10);
      trTbody.innerHTML = data.map(function(t) {
        var overdue = !t.completed && t.due_date && t.due_date < today;
        return '<tr onclick="openContactDetail(' + t.contact_id + ')" style="cursor:pointer">' +
          '<td class="contact-cell"><div class="nm">' + escHtml(t.contact_company||t.contact_name||'—') + '</div>' +
            '<div class="co">' + escHtml(t.contact_company ? t.contact_name||'' : '') + '</div></td>' +
          '<td>' + escHtml(t.title) + '</td>' +
          '<td>' + escHtml(t.assigned_to||'—') + '</td>' +
          '<td style="color:' + (overdue ? '#B33A47' : 'inherit') + '">' + (t.due_date||'—') + '</td>' +
          '<td>' + (t.completed ? '<span style="color:#4CAF50;font-weight:600">Done</span>' : overdue ? '<span style="color:#B33A47;font-weight:600">Overdue</span>' : '<span style="color:var(--warm-grey)">Open</span>') + '</td>' +
        '</tr>';
      }).join('');
    };
    if (trSel) trSel.addEventListener('change', function() { _renderTasks(this.value); });
    _renderTasks('open');
  }
}

function closeReport() {
  document.getElementById('report-overlay').style.display = 'none';
}

function togglePrincipalPicker() {
  const picker = document.getElementById('principal-picker');
  if (!picker) return;
  const isOpen = picker.style.display !== 'none';
  picker.style.display = isOpen ? 'none' : '';
  if (!isOpen) populatePrincipalBrands();
}

function onPipelineStatusChange(val) {
  var wrap = document.getElementById('pe-close-reason-wrap');
  if (wrap) wrap.style.display = isLostStatus(val) ? '' : 'none';
}

function buildCloseReasonSelect(currentVal) {
  var reasons = (_stageList.close_reason || []).slice().sort(function(a,b){return a.position-b.position;});
  var style = 'width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)';
  var html = '<select name="close_reason" id="pe-close-reason" required style="' + style + '">';
  html += '<option value="">Select a reason…</option>';
  var labels = reasons.map(function(r){ return r.label||r.name; });
  if (currentVal && !labels.includes(currentVal)) {
    html += '<option value="' + escHtml(currentVal) + '" selected>' + escHtml(currentVal) + '</option>';
  }
  reasons.forEach(function(r) {
    var lbl = r.label||r.name;
    html += '<option value="' + lbl + '"' + (currentVal === lbl ? ' selected' : '') + '>' + lbl + '</option>';
  });
  html += '</select>';
  return html;
}

function fmtDate(iso) {
  if (!iso) return "—";
  var d = iso.substring(0, 10);
  return d.slice(8,10) + '/' + d.slice(5,7) + '/' + d.slice(0,4);
}

async function loadReports() {
  var u = JSON.parse(localStorage.getItem('crm_user')||'{}');
  var ra = document.getElementById('rr-activity');
  if (ra) ra.style.display = (u.role==='admin') ? '' : 'none';
}

async function loadLostDealsReport() {
  var body = document.getElementById('report-overlay-body');
  var title = document.getElementById('report-overlay-title');
  if (title) title.textContent = 'Lost Deals';
  if (!body) return;
  var ownerEl   = document.getElementById('ld-owner-filter');
  var brandEl   = document.getElementById('ld-brand-filter');
  var fromEl    = document.getElementById('ld-date-from');
  var toEl      = document.getElementById('ld-date-to');
  var companyEl = document.getElementById('ld-company-search');
  var companySearch = ((companyEl && companyEl.value) || '').toLowerCase().trim();
  body.innerHTML = '<div style="padding:40px;text-align:center;color:var(--warm-grey)">Loading…</div>';
  var params = new URLSearchParams();
  if (ownerEl && ownerEl.value) params.set('owner_id', ownerEl.value);
  if (brandEl && brandEl.value) params.set('brand_id', brandEl.value);
  if (fromEl  && fromEl.value)  params.set('date_from', fromEl.value);
  if (toEl    && toEl.value)    params.set('date_to',   toEl.value);
  var d = await apiFetch('/reports/lost-deals?' + params);
  if (!d) { body.innerHTML='<div style="padding:40px;text-align:center;color:#B33A47">Failed to load.</div>'; return; }
  var isAdmin = CURRENT_USER && CURRENT_USER.role === 'admin';
  var users  = (window._crmUsers || []);
  var brands = allBrands || [];
  var filters = '<div style="display:flex;flex-wrap:wrap;gap:10px;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--off-white)">';
  if (isAdmin) {
    filters += '<div><label style="font-size:12px;color:var(--warm-grey);display:block;margin-bottom:4px">Owner</label>'
      + '<select id="ld-owner-filter" onchange="loadLostDealsReport()" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;background:var(--white)">'
      + '<option value="">All owners</option>'
      + users.map(function(u){ return '<option value="' + u.id + '"' + ((ownerEl&&ownerEl.value==u.id)?' selected':'') + '>' + escHtml(u.name) + '</option>'; }).join('')
      + '</select></div>';
  }
  filters += '<div><label style="font-size:12px;color:var(--warm-grey);display:block;margin-bottom:4px">Brand</label>'
    + '<select id="ld-brand-filter" onchange="loadLostDealsReport()" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;background:var(--white)">'
    + '<option value="">All brands</option>'
    + brands.map(function(b){ return '<option value="' + b.id + '"' + ((brandEl&&brandEl.value==b.id)?' selected':'') + '>' + escHtml(b.name) + '</option>'; }).join('')
    + '</select></div>';
  filters += '<div><label style="font-size:12px;color:var(--warm-grey);display:block;margin-bottom:4px">Company</label>'
    + '<input id="ld-company-search" type="text" placeholder="Filter by company…" value="' + escHtml(companySearch) + '" onchange="loadLostDealsReport()" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px;min-width:180px"/></div>';
  filters += '<div><label style="font-size:12px;color:var(--warm-grey);display:block;margin-bottom:4px">Closed from</label>'
    + '<input id="ld-date-from" type="date" value="' + ((fromEl&&fromEl.value)||'') + '" onchange="loadLostDealsReport()" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px"/></div>';
  filters += '<div><label style="font-size:12px;color:var(--warm-grey);display:block;margin-bottom:4px">Closed to</label>'
    + '<input id="ld-date-to" type="date" value="' + ((toEl&&toEl.value)||'') + '" onchange="loadLostDealsReport()" style="border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;font-size:13px"/></div>';
  filters += '</div>';
  var winRateColor  = (d.win_rate_pct  >= 50) ? '#1A7F4B' : '#B33A47';
  var lossRateColor = (d.loss_rate_pct >= 50) ? '#B33A47' : '#1A7F4B';
  var summaryHtml = '<div style="display:flex;flex-wrap:wrap;gap:0;border-bottom:1px solid var(--line)">'
    + '<div style="padding:16px 24px;border-right:1px solid var(--line);min-width:120px">'
    + '<div style="font-size:11px;color:var(--warm-grey);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">Won deals</div>'
    + '<div style="font-size:26px;font-weight:700;color:#1A7F4B">' + (d.total_won||0) + '</div>'
    + '<div style="font-size:11px;color:var(--warm-grey);margin-top:2px">' + fmtVal(d.total_won_value||0) + '</div>'
    + '</div>'
    + '<div style="padding:16px 24px;border-right:1px solid var(--line);min-width:120px">'
    + '<div style="font-size:11px;color:var(--warm-grey);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">Lost deals</div>'
    + '<div style="font-size:26px;font-weight:700;color:#B33A47">' + (d.total_lost||d.total||0) + '</div>'
    + '<div style="font-size:11px;color:var(--warm-grey);margin-top:2px">' + fmtVal(d.total_lost_value||d.total_value||0) + '</div>'
    + '</div>'
    + '<div style="padding:16px 24px;border-right:1px solid var(--line);min-width:110px">'
    + '<div style="font-size:11px;color:var(--warm-grey);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">Win rate</div>'
    + '<div style="font-size:26px;font-weight:700;color:' + winRateColor + '">' + (d.win_rate_pct||0) + '%</div>'
    + '</div>'
    + '<div style="padding:16px 24px;min-width:110px">'
    + '<div style="font-size:11px;color:var(--warm-grey);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">Loss rate</div>'
    + '<div style="font-size:26px;font-weight:700;color:' + lossRateColor + '">' + (d.loss_rate_pct||0) + '%</div>'
    + '</div>'
    + '</div>';
  var reasonsHtml = '';
  var reasonKeys = Object.keys(d.by_reason || {});
  if (reasonKeys.length) {
    reasonsHtml = '<div style="padding:16px 24px;border-bottom:1px solid var(--line)">'
      + '<div style="font-size:13px;font-weight:600;color:var(--navy);margin-bottom:10px">By Close Reason</div>'
      + '<div style="display:flex;flex-wrap:wrap;gap:8px">'
      + reasonKeys.map(function(r){
          return '<span style="padding:4px 12px;border-radius:12px;font-size:12px;font-weight:500;background:#F0F4FF;border:1px solid #C7D2FF;color:#3B4FCF">'
            + escHtml(r) + ' <b>' + d.by_reason[r] + '</b></span>';
        }).join('')
      + '</div></div>';
  }
  var byOwnerHtml = '';
  if (d.by_owner && d.by_owner.length > 1) {
    byOwnerHtml = '<div style="padding:16px 24px;border-bottom:1px solid var(--line)">'
      + '<div style="font-size:13px;font-weight:600;color:var(--navy);margin-bottom:10px">Win / Loss by Owner</div>'
      + '<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:12px">'
      + '<thead><tr style="background:var(--off-white)">'
      + '<th style="text-align:left;padding:8px 12px;font-weight:600;color:var(--navy)">Owner</th>'
      + '<th style="text-align:right;padding:8px 12px;font-weight:600;color:#1A7F4B">Won</th>'
      + '<th style="text-align:right;padding:8px 12px;font-weight:600;color:#B33A47">Lost</th>'
      + '<th style="text-align:right;padding:8px 12px;font-weight:600;color:var(--navy)">Win %</th>'
      + '<th style="text-align:left;padding:8px 12px;font-weight:600;color:var(--navy)"> </th>'
      + '</tr></thead><tbody>'
      + d.by_owner.map(function(o) {
          var bar = '<div style="display:flex;height:6px;border-radius:3px;overflow:hidden;width:100px;background:var(--line)">'
            + '<div style="background:#1A7F4B;width:' + o.win_rate_pct + '%"></div>'
            + '</div>';
          return '<tr style="border-top:1px solid var(--line)">'
            + '<td style="padding:8px 12px;font-weight:500">' + escHtml(o.owner_name||'—') + '</td>'
            + '<td style="padding:8px 12px;text-align:right;color:#1A7F4B;font-weight:600">' + o.won + '</td>'
            + '<td style="padding:8px 12px;text-align:right;color:#B33A47;font-weight:600">' + o.lost + '</td>'
            + '<td style="padding:8px 12px;text-align:right;font-weight:600">' + o.win_rate_pct + '%</td>'
            + '<td style="padding:8px 12px">' + bar + '</td>'
            + '</tr>';
        }).join('')
      + '</tbody></table></div>'
      + '</div>';
  }

  var filteredEntries = companySearch
    ? (d.entries || []).filter(function(e){ return (e.contact_company||'').toLowerCase().includes(companySearch); })
    : (d.entries || []);
  var tableHtml = '';
  if (filteredEntries.length) {
    var isAdminCol = isAdmin ? '<th style="text-align:left;padding:10px 12px;font-weight:600;color:var(--navy)">Owner</th>' : '';
    tableHtml = '<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px">'
      + '<thead><tr style="background:var(--off-white)">'
      + '<th style="text-align:left;padding:10px 12px;font-weight:600;color:var(--navy)">Contact / Company</th>'
      + '<th style="text-align:left;padding:10px 12px;font-weight:600;color:var(--navy)">Brand</th>'
      + '<th style="text-align:left;padding:10px 12px;font-weight:600;color:var(--navy)">Status</th>'
      + '<th style="text-align:right;padding:10px 12px;font-weight:600;color:var(--navy)">Value</th>'
      + '<th style="text-align:left;padding:10px 12px;font-weight:600;color:var(--navy)">Close Reason</th>'
      + '<th style="text-align:left;padding:10px 12px;font-weight:600;color:var(--navy)">Closed</th>'
      + isAdminCol + '</tr></thead><tbody>'
      + filteredEntries.map(function(e, i) {
          var adminCol = isAdmin ? '<td style="padding:10px 12px">' + escHtml(e.owner_name||'—') + '</td>' : '';
          return '<tr style="border-top:1px solid var(--line)">'
            + '<td style="padding:10px 12px"><div style="font-weight:500">' + escHtml(e.contact_name||'—') + '</div>'
            + (e.contact_company ? '<div style="font-size:12px;color:var(--warm-grey)">' + escHtml(e.contact_company) + '</div>' : '')
            + '</td>'
            + '<td style="padding:10px 12px">' + escHtml(e.brand_name||'—') + '</td>'
            + '<td style="padding:10px 12px"><span style="padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500;background:#FEF2F2;border:1px solid #FCA5A5;color:#B33A47">' + escHtml(e.status||'') + '</span></td>'
            + '<td style="padding:10px 12px;text-align:right;font-family:monospace">' + fmtVal(e.potential_value) + '</td>'
            + '<td style="padding:10px 12px">' + escHtml(e.close_reason||'—') + '</td>'
            + '<td style="padding:10px 12px;color:var(--warm-grey);white-space:nowrap">' + fmtDate(e.closed_at) + '</td>'
            + adminCol + '</tr>';
        }).join('')
      + '</tbody></table></div>';
  } else {
    tableHtml = '<div style="padding:40px;text-align:center;color:var(--warm-grey)">No lost deals found.</div>';
  }
  body.innerHTML = filters + summaryHtml + reasonsHtml + byOwnerHtml + tableHtml;
}

function setQFilter(f) {
  qFilter = f; qCurrentPage = 1;
  ['all','missing','complete','invalid_country','wrong_region'].forEach(function(k) {
    var btn = document.getElementById('qf-'+k);
    if (btn) btn.classList.toggle('qf-pill-active', k===f);
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
  var search       = (document.getElementById('q-search')||{}).value || '';
  var owner_id     = (document.getElementById('q-owner')||{}).value || '';
  var contact_type = (document.getElementById('q-contact-type')||{}).value || 'contacts';
  var p = new URLSearchParams({filter:qFilter, search:search, page:qCurrentPage, per_page:qPerPage, contact_type:contact_type});
  if (owner_id) p.set('owner_id', owner_id);
  var d = await apiFetch('/reports/contact-quality?'+p);
  if (!d) { tbody.innerHTML='<tr><td colspan="6" style="text-align:center;padding:40px;color:#B33A47">Failed to load.</td></tr>'; return; }

  // Timestamp
  var sub = document.getElementById('q-report-subtitle');
  if (sub) {
    var now  = new Date();
    var opts = {timeZone:'Asia/Bangkok',day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false};
    var ts   = now.toLocaleString('en-GB', opts).replace(',','');
    sub.textContent = 'LACRM REPORTS • GENERATED: '+ts+' (BANGKOK TIME)';
  }

  document.getElementById('qt-total').textContent           = fmtNum(d.total);
  document.getElementById('qt-missing').textContent         = fmtNum(d.n_missing);
  document.getElementById('qt-complete').textContent        = fmtNum(d.n_complete);
  document.getElementById('qt-invalid-country').textContent = fmtNum(d.n_invalid_country);
  document.getElementById('qt-region').textContent          = fmtNum(d.n_wrong_region);

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
    var barColour = pct===100 ? '#4CAF50' : pct>=60 ? '#76BCE0' : pct>=40 ? '#F59E0B' : '#E57373';
    var bar = '<div style="display:flex;align-items:center;gap:8px">'
      + '<div style="flex:1;height:5px;border-radius:3px;background:var(--line);overflow:hidden">'
      + '<div style="height:100%;width:'+pct+'%;background:'+barColour+'"></div></div>'
      + '<span style="font-size:12px;font-family:JetBrains Mono,monospace;color:var(--navy);white-space:nowrap">'+pct+'%</span></div>';
    var pills = r.missing.map(function(m){ return '<span class="q-pill">'+m+'</span>'; }).join('');
    var countryCell = '';
    if (r.country) {
      countryCell = escHtml(r.country);
      if (r.invalid_country) countryCell += ' <span style="color:#E57373;font-size:11px">⚠ Invalid</span>';
      else if (r.wrong_region) countryCell += ' <span style="color:#F59E0B;font-size:11px">⚠ No region</span>';
    } else {
      countryCell = '<span style="color:var(--warm-grey)">—</span>';
    }
    var status = r.complete
      ? '<span style="display:inline-block;padding:2px 10px;border-radius:4px;font-size:11px;font-weight:500;background:#F0FDF4;border:1px solid #86EFAC;color:#166534">Complete</span>'
      : '<span style="display:inline-block;padding:2px 10px;border-radius:4px;font-size:11px;font-weight:500;background:#FEF2F2;border:1px solid #FCA5A5;color:#B33A47">Missing fields</span>';
    return '<tr style="cursor:pointer" onclick="openContactEditFromReport('+r.id+')">' 
      + '<td class="contact-cell" style="padding-left:32px"><div class="nm">'+escHtml(r.name||'—')+'</div>'+(r.job_title?'<div class="co">'+escHtml(r.job_title)+'</div>':'')
      + (r.company?'<div class="co">'+escHtml(r.company)+'</div>':'')
      + '</td>'
      + '<td>'+bar+'</td>'
      + '<td>'+(pills||'<span style="color:var(--warm-grey);font-size:12px">—</span>')+'</td>'
      + '<td style="font-size:13px">'+countryCell+'</td>'
      + '<td style="font-size:13px">'+(r.owner||'<span style="color:var(--warm-grey)">—</span>')+'</td>'
      + '<td>'+status+'</td>'
      + '</tr>';
  }).join('');
}

function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

async function downloadQualityCSV() {
  var search       = (document.getElementById('q-search')||{}).value || '';
  var owner_id     = (document.getElementById('q-owner')||{}).value || '';
  var contact_type = (document.getElementById('q-contact-type')||{}).value || 'contacts';
  var p = new URLSearchParams({filter:qFilter, search:search, contact_type:contact_type});
  if (owner_id) p.set('owner_id', owner_id);
  var resp = await fetch(API+'/reports/contact-quality-csv?'+p, {headers:{'Authorization':'Bearer '+TOKEN}});
  if (!resp.ok) { showToast('Export failed'); return; }
  var blob = await resp.blob();
  var a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'contact_quality.csv'; a.click();
  showToast('CSV downloaded');
}


async function populatePrincipalBrands() {
  const el = document.getElementById('principal-brand-list');
  if (!el) return;
  let brands = (typeof allBrands !== 'undefined' && allBrands && allBrands.length) ? allBrands : null;
  if (!brands) {
    const fetched = await apiFetch('/brands');
    brands = fetched || [];
    if (fetched && fetched.length && typeof allBrands !== 'undefined') allBrands = fetched;
  }
  if (!brands.length) {
    el.innerHTML = '<div style="color:var(--warm-grey);font-size:13px">No brands available.</div>';
    return;
  }
  el.innerHTML = brands.map(b =>
    `<label style="display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer;padding:6px 12px;border:1px solid var(--line);border-radius:8px;user-select:none" ` +
    `onmouseover="this.style.background='var(--off-white)'" onmouseout="this.style.background=''">`+
      `<input type="checkbox" value="${b.id}" style="cursor:pointer"> ${escHtml(b.name)}`+
    `</label>`
  ).join('');
}

async function downloadPrincipalReport() {
  const checks = document.querySelectorAll('#principal-brand-list input[type=checkbox]:checked');
  if (!checks.length) { showToast('Select at least one brand'); return; }
  const ids = Array.from(checks).map(c=>c.value).join(',');
  await downloadFileBlob('/reports/principal-report.xlsx?brands='+ids, 'principal_report.xlsx');
}
async function loadActivityReport() {
  var el = document.getElementById('reports-activity-body');
  if (!el) return;
  var sel = document.getElementById('reports-period');
  var period = sel ? sel.value : '30d';
  el.innerHTML = '<div style="padding:20px;color:var(--warm-grey);text-align:center">Loading…</div>';
  var ownerEl = document.getElementById('reports-owner');
  var ownerId = ownerEl ? ownerEl.value : '';
  var d = await apiFetch('/reports/activity?period='+period+(ownerId?'&owner_id='+ownerId:''));
  if (!d) { el.innerHTML='<span style="color:#B33A47">Failed to load.</span>'; return; }
  var items = [
    ['New Contacts',         d.new_contacts],
    ['New Companies',        d.new_companies],
    ['New Pipeline Entries', d.new_pipeline_entries],
    ['New Orders',           d.new_orders],
    ['Emails Received',      d.emails_inbound],
    ['Emails Sent',          d.emails_outbound],
    ['New Tasks',            d.new_tasks||0],
    ['New Notes',            d.new_notes||0],
    ['Tasks Completed',      d.completed_tasks||0],
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
async function openContactEditFromReport(id) {
  window._editFromReport = true;
  openContactDetail(id);
}

// ── Contact merge ─────────────────────────────────────────────────────────────
async function openMergeModal(masterId) {
  document.getElementById('merge-overlay')?.remove();
  const master = await apiFetch('/contacts/' + masterId);
  if (!master) return;

  const overlay = document.createElement('div');
  overlay.id = 'merge-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:10000';
  overlay.innerHTML =
    `<div style="background:#fff;border-radius:12px;padding:28px 32px;width:480px;max-width:95vw;max-height:85vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,.2)">`+
      `<div style="font-family:'Playfair Display',serif;font-size:17px;color:var(--navy);font-weight:700;margin-bottom:4px">Merge Contact</div>`+
      `<div style="font-size:13px;color:var(--warm-grey);margin-bottom:20px">Master (kept): <strong>${escHtml(master.name)}</strong></div>`+
      `<label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:6px">Search for duplicate to absorb</label>`+
      `<input id="merge-search" type="text" placeholder="Name, email, or company…" `+
        `style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;box-sizing:border-box;margin-bottom:12px" `+
        `oninput="searchMergeCandidates(${masterId})">`+
      `<div id="merge-results" style="min-height:40px"></div>`+
      `<div style="margin-top:20px;text-align:right">`+
        `<button onclick="document.getElementById('merge-overlay').remove()" class="btn btn-secondary">Cancel</button>`+
      `</div>`+
    `</div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  setTimeout(() => document.getElementById('merge-search')?.focus(), 50);
}

let _mergeSearchTimer = null;
async function searchMergeCandidates(masterId) {
  clearTimeout(_mergeSearchTimer);
  _mergeSearchTimer = setTimeout(async () => {
    const q = (document.getElementById('merge-search')?.value || '').trim();
    const results = document.getElementById('merge-results');
    if (!results) return;
    if (q.length < 2) { results.innerHTML = ''; return; }
    results.innerHTML = '<div style="font-size:13px;color:var(--warm-grey)">Searching…</div>';
    const data = await apiFetch('/contacts?search=' + encodeURIComponent(q) + '&per_page=10');
    if (!data) { results.innerHTML = ''; return; }
    const hits = (data.results || []).filter(c => c.id !== masterId);
    if (!hits.length) {
      results.innerHTML = '<div style="font-size:13px;color:var(--warm-grey)">No results</div>';
      return;
    }
    results.innerHTML = hits.map(c =>
      `<div onclick="showMergeConfirm(${masterId},${c.id})" `+
           `style="padding:10px 12px;border:1px solid var(--line);border-radius:8px;margin-bottom:6px;cursor:pointer" `+
           `onmouseover="this.style.background='var(--off-white)'" onmouseout="this.style.background=''">`+
        `<div style="font-size:13px;font-weight:600;color:var(--navy)">${escHtml(c.name)}</div>`+
        `<div style="font-size:12px;color:var(--warm-grey)">${escHtml(c.company||'')}${c.email?' · '+escHtml(c.email):''}</div>`+
      `</div>`
    ).join('');
  }, 300);
}

async function showMergeConfirm(masterId, dupId) {
  const overlay = document.getElementById('merge-overlay');
  const panel = overlay?.querySelector('div');
  if (!panel) return;
  panel.innerHTML = '<div style="font-size:13px;color:var(--warm-grey);padding:20px 0">Loading preview…</div>';
  const preview = await apiFetch('/contacts/' + masterId + '/merge-preview/' + dupId);
  if (!preview) {
    panel.innerHTML = '<div style="color:#B33A47;padding:20px 0">Failed to load preview. <button onclick="document.getElementById(\'merge-overlay\').remove()" class="btn btn-secondary" style="margin-top:12px">Close</button></div>';
    return;
  }
  const rows = [
    {label: 'Pipeline entries', n: preview.pipeline},
    {label: 'Emails',           n: preview.emails},
    {label: 'Orders',           n: preview.orders},
    {label: 'Notes',            n: preview.notes},
    {label: 'Tasks',            n: preview.tasks},
    {label: 'Attachments',      n: preview.attachments},
  ].filter(x => x.n > 0);

  panel.innerHTML =
    `<div style="font-family:'Playfair Display',serif;font-size:17px;color:var(--navy);font-weight:700;margin-bottom:20px">Confirm Merge</div>`+
    `<div style="display:grid;grid-template-columns:140px 1fr;gap:6px 12px;font-size:13px;margin-bottom:20px;align-items:baseline">`+
      `<span style="color:var(--warm-grey);font-weight:600">Master (kept)</span>`+
      `<span style="color:var(--navy);font-weight:600">${escHtml(preview.master_name)}</span>`+
      `<span style="color:var(--warm-grey);font-weight:600">Duplicate (deleted)</span>`+
      `<span style="color:var(--navy)">${escHtml(preview.dup_name)}</span>`+
    `</div>`+
    (rows.length
      ? `<div style="font-size:11px;font-weight:600;color:var(--warm-grey);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">Records to move to master</div>`+
        rows.map(x =>
          `<div style="font-size:13px;padding:6px 0;border-bottom:1px solid var(--off-white)">`+
            `• ${x.n} ${x.label}`+
          `</div>`
        ).join('')
      : `<div style="font-size:13px;color:var(--warm-grey);margin-bottom:12px">No related records to move.</div>`
    )+
    `<div style="background:#FFF8E1;border:1px solid #FFD54F;border-radius:8px;padding:10px 14px;font-size:13px;margin-top:16px;margin-bottom:20px">`+
      `⚠️ <strong>${escHtml(preview.dup_name)}</strong> will be permanently deleted. This cannot be undone.`+
    `</div>`+
    `<div style="display:flex;gap:8px;justify-content:flex-end">`+
      `<button onclick="openMergeModal(${masterId})" class="btn btn-secondary">← Back</button>`+
      `<button id="merge-confirm-btn" onclick="executeMerge(${masterId},${dupId})" `+
        `class="btn btn-primary" style="background:#B33A47;border-color:#B33A47">Merge &amp; Delete Duplicate</button>`+
    `</div>`;
}

async function executeMerge(masterId, dupId) {
  const btn = document.getElementById('merge-confirm-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Merging…'; }
  const result = await apiFetch('/contacts/' + masterId + '/merge', {
    method: 'POST',
    body: JSON.stringify({ duplicate_id: dupId })
  });
  document.getElementById('merge-overlay')?.remove();
  if (result?.ok) {
    showToast('Contacts merged successfully');
    openContactDetail(masterId);
  } else {
    alert('Merge failed. Please try again.');
  }
}


async function _openContactEditFromReport_UNUSED(id) {
  const c = await apiFetch('/contacts/'+id);
  if (!c) return;
  const countries = getCountries();
  const regions   = getRegions();
  const currentRegion = regions.find(r => (c.tags||'').includes(r)) || '';
  document.getElementById('modal-title').innerHTML = 'Edit Contact';
  document.getElementById('modal-body').innerHTML = `
    <form id="edit-contact-form" onsubmit="saveContactEditFromReport(event,${id})">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label class="fl">First Name</label>
          <input name="first_name" value="${escHtml(c.first_name||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label class="fl">Last Name</label>
          <input name="last_name" value="${escHtml(c.last_name||c.name||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="margin-bottom:12px"><label class="fl">Company</label>
        <input name="company" value="${escHtml(c.company||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><label class="fl">Email</label>
          <input name="email" type="email" value="${escHtml(c.email||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
        <div><label class="fl">Phone</label>
          <input name="phone" value="${escHtml(c.phone||'')}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
        <div><label class="fl">Country</label>
          <select name="country" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            <option value="">— Select —</option>
            ${countries.map(co=>`<option${co===c.country?' selected':''}>${co}</option>`).join('')}
          </select></div>
        <div><label class="fl">Sales Region</label>
          <select name="region" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
            <option value="">— Select —</option>
            ${regions.map(r=>`<option${r===currentRegion?' selected':''}>${r}</option>`).join('')}
          </select></div>
      </div>
      <div id="ecfr-error" style="display:none;color:#B33A47;font-size:13px;margin-bottom:12px;padding:10px;background:#FAE3E5;border-radius:8px"></div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" onclick="document.getElementById('modal').style.display='none'" class="btn btn-secondary">Cancel</button>
        <button type="submit" class="btn btn-primary">Save</button>
      </div>
    </form>`;
  document.getElementById('modal').style.display = 'flex';
}

async function saveContactEditFromReport(e, id) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const first = fd.get('first_name')||'';
  const last  = fd.get('last_name')||'';
  const name  = (first+' '+last).trim() || fd.get('company')||'';
  const newRegion = fd.get('region')||'';
  const c = await apiFetch('/contacts/'+id);
  // Keep existing tags, replace the region tag
  const regions = getRegions();
  let tags = (c ? (c.tags||'') : '').split(',').map(t=>t.trim()).filter(t=>t && !regions.includes(t));
  if (newRegion) tags.push(newRegion);
  const payload = {
    first_name: first||null, last_name: last||null, name,
    company: fd.get('company')||null,
    email:   fd.get('email')||null,
    phone:   fd.get('phone')||null,
    job_title: fd.get('job_title')||null,
    country: fd.get('country')||null,
    tags:    tags.join(', ')||null,
  };
  const btn = e.target.querySelector('[type=submit]');
  btn.textContent='Saving…'; btn.disabled=true;
  const result = await apiFetch('/contacts/'+id, {method:'PUT', body:JSON.stringify(payload)});
  if (result) {
    document.getElementById('modal').style.display='none';
    showToast('Contact saved');
    loadQualityReport();
  } else {
    document.getElementById('ecfr-error').textContent='Failed to save. Please try again.';
    document.getElementById('ecfr-error').style.display='block';
    btn.textContent='Save'; btn.disabled=false;
  }
}


// ---- Brands ----
let allBrands = [];
async function loadBrands() {
  const d = await apiFetch('/brands'); if(!d) return;
  allBrands = d;
  const sc = document.getElementById('sb-count-brands'); if(sc) sc.textContent=d.length;
  const grid = document.getElementById('brands-grid');
  if (grid) grid.innerHTML = d.map(b=>`
    <div class="wl">
      <div class="wl-head">
        <div class="wl-av" style="background:var(--logo-blue-pale);color:var(--navy)">${escHtml(b.name.slice(0,2).toUpperCase())}</div>
        <div><div class="wl-name">${escHtml(b.name)}</div><div class="wl-sub">${b.is_active?'Active':'Inactive'}</div></div>
      </div>
      ${b.notes?`<div style="font-size:12px;color:var(--warm-grey);margin-top:4px">${escHtml(b.notes)}</div>`:''}
      <div style="margin-top:10px;text-align:right"><button onclick="downloadBrandReport(${b.id})" style="font-size:12px;color:var(--logo-blue);background:transparent;border:1px solid var(--logo-blue);border-radius:6px;padding:3px 10px;cursor:pointer;white-space:nowrap">↓ Report</button></div>
    </div>`).join('');
  const bf = document.getElementById('filter-brand');
  if (bf) bf.innerHTML='<option value="">All brands</option>'+d.map(b=>`<option value="${b.id}">${b.name}</option>`).join('');
  const ab = document.getElementById('admin-brands-tbody');
  if (ab) ab.innerHTML = d.map(b=>`
    <tr><td class="contact-cell"><div class="nm">${escHtml(b.name)}</div></td>
      <td><span class="pill ${b.is_active?'green':'grey'}">${b.is_active?'Active':'Inactive'}</span></td>
      <td style="color:var(--warm-grey);font-size:12px">${escHtml(b.notes)||'—'}</td>
      <td style="display:flex;gap:6px"><button class="btn btn-secondary" style="padding:4px 10px;font-size:12px" onclick="toggleBrand(${b.id},${b.is_active})">${b.is_active?'Deactivate':'Activate'}</button><button onclick="downloadBrandReport(${b.id})" class="btn btn-secondary" style="padding:4px 10px;font-size:12px;cursor:pointer">↓ Report</button></td>
    </tr>`).join('');
}

function openNewBrandModal() {
  document.getElementById('modal-title').innerHTML='New Brand';
  document.getElementById('modal-body').innerHTML=`
    <form onsubmit="saveNewBrand(event)">
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Brand Name *</label>
        <input name="name" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div style="margin-bottom:20px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Notes</label>
        <textarea name="notes" rows="2" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;resize:vertical"></textarea></div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" onclick="document.getElementById('modal').style.display='none'" class="btn btn-secondary">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Brand</button>
      </div>
    </form>`;
  document.getElementById('modal').style.display='flex';
}
async function saveNewBrand(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const r = await apiFetch('/brands',{method:'POST',body:JSON.stringify({name:fd.get('name'),notes:fd.get('notes')||null})});
  if(r){document.getElementById('modal').style.display='none';loadBrands();}
}
async function toggleBrand(id, active) {
  await apiFetch('/brands/'+id,{method:'PUT',body:JSON.stringify({is_active:!active})});
  loadBrands();
}

// ---- Orders ----
var ordersPage = 1;
var ordersData = [];

function orderStatusPillClass(s) {
  if (s==='commission_paid'||s==='bonus_paid') return 'green';
  if (s==='shipped'||s==='fully_paid'||s==='commission_invoiced') return 'amber';
  return 'blue';
}

async function loadOrders() {
  const p = new URLSearchParams({ page: ordersPage, per_page: 50 });
  const sf = document.getElementById('orders-filter-status'); if(sf&&sf.value) p.set('status',sf.value);
  const of2 = document.getElementById('orders-filter-owner'); if(of2&&of2.value) p.set('owner_id',of2.value);
  const bf = document.getElementById('orders-filter-brand'); if(bf&&bf.value) p.set('brand_id',bf.value);
  const d = await apiFetch('/orders?'+p); if(!d) return;
  ordersData = d.results||[];
  const sc = document.getElementById('sb-count-orders'); if(sc) sc.textContent=fmtNum(d.total);
  const meta = document.getElementById('orders-meta'); if(meta) meta.textContent=d.total+' order'+(d.total!==1?'s':'');
  // Populate owner filter if empty
  var ownerSel = document.getElementById('orders-filter-owner');
  if (ownerSel && ownerSel.options.length<=1 && d.results.length) {
    var seen={};
    d.results.forEach(function(o){if(o.owner_id&&!seen[o.owner_id]){seen[o.owner_id]=1;ownerSel.innerHTML+='<option value="'+o.owner_id+'">'+escHtml(o.owner_name||'')+'</option>';}});
  }
  // Populate brand filter if empty
  var brandSel = document.getElementById('orders-filter-brand');
  if (brandSel && brandSel.options.length<=1 && d.results.length) {
    var seen2={};
    d.results.forEach(function(o){if(o.brand_id&&!seen2[o.brand_id]){seen2[o.brand_id]=1;brandSel.innerHTML+='<option value="'+o.brand_id+'">'+escHtml(o.brand_name||'')+'</option>';}});
  }
  const tbody = document.getElementById('orders-tbody');
  const isAdmin = CURRENT_USER&&CURRENT_USER.role==='admin';
  if(!ordersData.length){tbody.innerHTML='<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--warm-grey);">No orders yet.</td></tr>';return;}
  tbody.innerHTML=ordersData.map(function(o){
    var pillCls=orderStatusPillClass(o.status);
    var shipDate=o.ship_date||'—';
    var commDue=o.commission_due_date||'—';
    return '<tr style="cursor:pointer" onclick="openOrderDetail('+o.id+')">'
      +'<td class="contact-cell"><div class="nm">'+escHtml(o.contact_name||'—')+'</div><div class="co">'+escHtml(o.contact_company||'')+'</div></td>'
      +'<td>'+brandMark(o.brand_name||'—')+'</td>'
      +'<td class="value-cell">'+fmtVal(o.order_value)+'</td>'
      +'<td class="value-cell" style="color:var(--st-green-fg)">'+fmtVal(o.net_commission)+'</td>'
      +'<td><span class="pill '+pillCls+'">'+escHtml(o.status_label||o.status)+'</span></td>'
      +'<td>'+fmtDate(o.ship_date)+'</td>'
      +'<td style="color:var(--logo-blue)">'+fmtDate(o.commission_due_date)+'</td>'
      +'<td>'+ownerAv(o.owner_name)+'</td>'
      +'</tr>';
  }).join('');
}

async function openOrderDetail(orderId) {
  var o = ordersData.find(function(x){return x.id===orderId;}); if(!o) return;
  var isAdmin = CURRENT_USER&&CURRENT_USER.role==='admin';
  var ORDER_STATUSES = ['po_received','deposit_paid','shipped','fully_paid','commission_invoiced','commission_paid','bonus_paid'];
  var ORDER_STATUS_LABELS = {po_received:'PO Received',deposit_paid:'Deposit Paid',shipped:'Shipped',fully_paid:'Fully Paid',commission_invoiced:'Commission Invoiced',commission_paid:'Commission Paid',bonus_paid:'Bonus Paid'};
  var ORDER_STATUS_DATES = {po_received:'po_date',deposit_paid:'deposit_date',shipped:'ship_date',fully_paid:'fully_paid_date',commission_invoiced:'commission_invoiced_date',commission_paid:'commission_paid_date',bonus_paid:'bonus_paid_date'};
  var ORDER_STATUS_COLORS = {po_received:'blue',deposit_paid:'blue',shipped:'amber',fully_paid:'amber',commission_invoiced:'amber',commission_paid:'green',bonus_paid:'green'};
  var idx = ORDER_STATUSES.indexOf(o.status);

  // Progress bar
  var progressHtml = '<div style="display:flex;gap:0;margin-bottom:20px;border-radius:8px;overflow:hidden;background:var(--off-white)">'
    + ORDER_STATUSES.map(function(s,i){
        var active = i<=idx;
        var colors = {blue:'var(--logo-blue)',amber:'#C97B2B',green:'var(--st-green-fg)'};
        var bg = active ? colors[ORDER_STATUS_COLORS[s]] : 'transparent';
        var fg = active ? '#fff' : 'var(--warm-grey)';
        return '<div style="flex:1;padding:6px 4px;text-align:center;font-size:10px;font-weight:600;background:'+bg+';color:'+fg+';transition:background .2s">'
          + escHtml(ORDER_STATUS_LABELS[s]) + '</div>';
      }).join('')
    + '</div>';

  // Dates grid
  var datesHtml = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;font-size:13px">';
  ORDER_STATUSES.forEach(function(s){
    var df = ORDER_STATUS_DATES[s];
    var val = o[df];
    datesHtml += '<div style="padding:8px 12px;background:var(--off-white);border-radius:8px">'
      + '<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey);margin-bottom:2px">'+escHtml(ORDER_STATUS_LABELS[s])+'</div>'
      + '<div style="color:var(--navy)">'+(val||'—')+'</div>'
      + '</div>';
  });
  datesHtml += '</div>';

  // Next status button
  var nextStatusHtml = '';
  if (o.next_status && (isAdmin || o.owner_id===CURRENT_USER?.id)) {
    nextStatusHtml = '<button class="btn btn-primary" style="margin-bottom:16px" data-oid="'+o.id+'" data-ns="'+o.next_status+'" onclick="advanceOrderStatus(parseInt(this.dataset.oid),this.dataset.ns)">Mark as '+escHtml(o.next_status_label||o.next_status)+' &#8594;</button>';
  }

  // Financials
  var finHtml = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px;font-size:13px">'
    + '<div style="padding:10px 12px;background:var(--off-white);border-radius:8px"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Order Value</div><div style="font-size:16px;font-weight:700;color:var(--navy)">'+fmtVal(o.order_value)+'</div></div>'
    + '<div style="padding:10px 12px;background:var(--off-white);border-radius:8px"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Commission Rate</div><div style="font-size:16px;font-weight:700;color:var(--navy)">'+o.gross_commission_rate+'%</div></div>'
    + '<div style="padding:10px 12px;background:var(--off-white);border-radius:8px"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Net Commission</div><div style="font-size:16px;font-weight:700;color:var(--st-green-fg)">'+fmtVal(o.net_commission)+'</div></div>'
    + (isAdmin&&o.bonus_amount!=null?'<div style="padding:10px 12px;background:var(--off-white);border-radius:8px"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Bonus (5%)</div><div style="font-size:16px;font-weight:700;color:#8E44AD">'+fmtVal(o.bonus_amount)+'</div></div>':'')
    + '</div>';

  document.getElementById('modal-title').innerHTML = escHtml(o.contact_name||'—')+' · '+escHtml(o.brand_name||'—');
  var mf = document.getElementById('modal-footer');
  mf.innerHTML = '';
  var closeBtn = document.createElement('button');
  closeBtn.className='btn btn-secondary'; closeBtn.textContent='Close';
  closeBtn.onclick = function(){ document.getElementById('modal').style.display='none'; };
  mf.appendChild(closeBtn);
  if (isAdmin) {
    var delBtn = document.createElement('button');
    delBtn.className='btn btn-secondary'; delBtn.style.color='#B33A47'; delBtn.textContent='Delete';
    delBtn.onclick = function(){ deleteOrder(o.id); };
    mf.appendChild(delBtn);
  }
  document.getElementById('modal-body').innerHTML = progressHtml + nextStatusHtml + finHtml + datesHtml
    + '<div style="font-size:12px;color:var(--warm-grey);margin-top:4px">'
    + 'Owner: <b>'+escHtml(o.owner_name||'—')+'</b>'
    + (o.commission_due_date?' &nbsp;·&nbsp; Commission due: <b style="color:var(--logo-blue)">'+o.commission_due_date+'</b>':'')
    + '</div>';
  document.getElementById('modal').style.display='flex';
}

async function advanceOrderStatus(orderId, newStatus) {
  var r = await apiFetch('/orders/'+orderId+'/advance-status', {method:'POST', body:JSON.stringify({status:newStatus})});
  if (r) { document.getElementById('modal').style.display='none'; showToast('Order updated to '+newStatus.replace(/_/g,' ')); loadOrders(); }
  else showToast('Failed to update status');
}

async function deleteOrder(orderId) {
  if (!confirm('Move this order to trash?')) return;
  var r = await apiFetch('/orders/'+orderId, {method:'DELETE'});
  if (r) { document.getElementById('modal').style.display='none'; showToast('Order deleted'); loadOrders(); }
  else showToast('Failed to delete order');
}

function exportOrdersCSV() {
  if (!ordersData.length) { showToast('No orders to export'); return; }
  var cols = ['Contact','Company','Brand','Owner','Order Value','Net Commission','Status','Ship Date','Commission Due'];
  var rows = ordersData.map(function(o){return[
    o.contact_name||'',o.contact_company||'',o.brand_name||'',o.owner_name||'',
    o.order_value||0,o.net_commission||0,o.status||'',o.ship_date||'',o.commission_due_date||''
  ];});
  var csv=cols.join(',')+String.fromCharCode(10);csv+=rows.map(function(r){return r.map(function(v){return '"'+String(v).replace(/"/g,'""')+'"';}).join(',');}).join(String.fromCharCode(10));
  var a=document.createElement('a');a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);a.download='orders.csv';a.click();
}

// ---- Emails ----

// ── My Tasks view ─────────────────────────────────────────────────────────────
async function loadMyTasks() {
  const wrap = document.getElementById('tasks-view-body');
  const meta = document.getElementById('tasks-meta');
  if (!wrap) return;
  wrap.innerHTML = '<div style="padding:40px;text-align:center;color:var(--warm-grey)">Loading…</div>';
  const d = await apiFetch('/tasks?completed=false');
  if (!d) {
    wrap.innerHTML = '<div style="padding:40px;text-align:center;color:var(--warm-grey)">Failed to load tasks.</div>';
    return;
  }
  const badge = document.getElementById('sb-count-tasks');
  if (badge) badge.textContent = d.length || '';
  if (meta) meta.textContent = d.length + ' open task' + (d.length !== 1 ? 's' : '');
  if (!d.length) {
    wrap.innerHTML = '<div class="card"><div class="card-body" style="padding:40px;text-align:center;color:var(--warm-grey)">No open tasks.</div></div>';
    return;
  }

  // Group by assignee name
  const groups = {};
  for (const t of d) {
    const key = t.assigned_to || '— Unassigned';
    if (!groups[key]) groups[key] = [];
    groups[key].push(t);
  }

  const today = new Date(); today.setHours(0, 0, 0, 0);
  function dueBadge(due) {
    if (!due) return '';
    const dd = new Date(due + 'T00:00:00'); dd.setHours(0, 0, 0, 0);
    const diff = Math.round((dd - today) / 86400000);
    const color = diff < 0 ? '#B33A47' : diff === 0 ? '#C97B2B' : '#2E7D52';
    const label = diff < 0 ? Math.abs(diff) + 'd overdue' : diff === 0 ? 'Today' : 'in ' + diff + 'd';
    return '<span style="font-size:11px;padding:2px 9px;border-radius:10px;background:' + color + '22;color:' + color + ';font-weight:600;white-space:nowrap">' + label + '</span>';
  }

  const sortedKeys = Object.keys(groups).sort(function(a, b) {
    if (a === '— Unassigned') return 1;
    if (b === '— Unassigned') return -1;
    return a.localeCompare(b);
  });

  wrap.innerHTML = '<div class="card"><div class="card-body" style="padding:0 24px">' +
    sortedKeys.map(function(name) {
      const tasks = groups[name];
      return '<div style="padding:16px 0 4px">' +
        '<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--warm-grey);padding:0 0 8px;border-bottom:1px solid var(--line);margin-bottom:4px">' +
          escHtml(name) + ' <span style="font-weight:400">(' + tasks.length + ')</span>' +
        '</div>' +
        tasks.map(function(t) {
          return '<div onclick="openContactDetail(' + t.contact_id + ')" ' +
            'style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--line);cursor:pointer" ' +
            'onmouseover="this.style.background=\'var(--off-white)\'" onmouseout="this.style.background=\'\'">' +
            '<div style="flex:1;min-width:0">' +
              '<div style="font-size:13px;font-weight:600;color:var(--navy)">' + escHtml(t.title || '(no title)') + '</div>' +
              '<div style="font-size:12px;color:var(--warm-grey);margin-top:2px">' +
                escHtml(t.contact_name || '') + (t.contact_company ? ' · ' + escHtml(t.contact_company) : '') +
              '</div>' +
            '</div>' +
            '<div>' + dueBadge(t.due_date) + '</div>' +
          '</div>';
        }).join('') +
      '</div>';
    }).join('') +
  '</div></div>';
}

function openLogEmailModal(prefillContactId) {
  const now = new Date();
  const localDT = new Date(now - now.getTimezoneOffset()*60000).toISOString().slice(0,16);
  document.getElementById('modal-title').innerHTML = 'Log Email';
  document.getElementById('modal-body').innerHTML =
    `<form id="log-email-form" onsubmit="saveLogEmail(event)">`+
      `<div style="margin-bottom:12px">`+
        `<label class="fl">Direction</label>`+
        `<select name="direction" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">`+
          `<option value="inbound">Inbound (received)</option>`+
          `<option value="outbound">Outbound (sent)</option>`+
        `</select></div>`+
      `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">`+
        `<div><label class="fl">From</label>`+
          `<input name="from_address" type="email" placeholder="sender@example.com" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
        `<div><label class="fl">To</label>`+
          `<input name="to_address" type="email" placeholder="recipient@example.com" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
      `</div>`+
      `<div style="margin-bottom:12px"><label class="fl">BCC</label>`+
        `<input name="bcc_address" type="email" placeholder="bcc@example.com (optional)" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
      `<div style="margin-bottom:12px"><label class="fl">Subject</label>`+
        `<input name="subject" placeholder="Email subject" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
      `<div style="margin-bottom:12px"><label class="fl">Body snippet</label>`+
        `<textarea name="body_snippet" rows="3" placeholder="Key excerpt or summary…" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;resize:vertical"></textarea></div>`+
      `<div style="margin-bottom:20px"><label class="fl">Date &amp; Time</label>`+
        `<input name="sent_at" type="datetime-local" value="${localDT}" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>`+
      `<div id="le-error" style="display:none;color:#B33A47;font-size:13px;margin-bottom:12px;padding:10px;background:#FAE3E5;border-radius:8px"></div>`+
      `<div style="display:flex;gap:8px;justify-content:flex-end">`+
        `<button type="button" onclick="document.getElementById('modal').style.display='none'" class="btn btn-secondary">Cancel</button>`+
        `<button type="submit" class="btn btn-primary">Save</button>`+
      `</div>`+
    `</form>`;
  document.getElementById('modal').style.display = 'flex';
}

async function saveLogEmail(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = {
    direction:    fd.get('direction'),
    from_address: fd.get('from_address') || null,
    to_address:   fd.get('to_address')   || null,
    bcc_address:  fd.get('bcc_address')  || null,
    subject:      fd.get('subject')      || null,
    body_snippet: fd.get('body_snippet') || null,
    sent_at:      fd.get('sent_at')      || null,
  };
  const btn = e.target.querySelector('[type=submit]');
  btn.disabled = true; btn.textContent = 'Saving…';
  const result = await apiFetch('/emails', { method: 'POST', body: JSON.stringify(payload) });
  if (result) {
    document.getElementById('modal').style.display = 'none';
    showToast('Email logged' + (result.contact_created ? ' · new contact created' : ''));
    loadEmails();
  } else {
    document.getElementById('le-error').textContent = 'Failed to save. Please try again.';
    document.getElementById('le-error').style.display = 'block';
    btn.disabled = false; btn.textContent = 'Save';
  }
}

async function loadEmails() {
  const d = await apiFetch('/emails'); if(!d) return;
  document.getElementById('emails-meta').textContent=d.total+' emails';
  const el=document.getElementById('emails-list');
  if(!d.results.length){el.innerHTML='<div style="padding:40px;text-align:center;color:var(--warm-grey);">No emails logged yet.</div>';return;}
  el.innerHTML=d.results.map(e=>`
    <div class="email-row">
      <div class="email-avatar av-b">${(e.from_address||e.subject||'?')[0].toUpperCase()}</div>
      <div>
        <div class="em-line1"><span class="em-from">${escHtml(e.from_address||'—')}</span>${e.contact_name?`<span class="em-co">· ${escHtml(e.contact_name)}</span>`:''}
          <span class="em-dir ${e.direction==='inbound'?'in':'out'}">${e.direction==='inbound'?'In':'Out'}</span></div>
        <div class="em-subj">${escHtml(e.subject||'(no subject)')}</div>
        <div class="em-snip">${escHtml(e.body_snippet||'')}</div>
        ${e.bcc_address?`<div style="font-size:11px;color:var(--warm-grey)">BCC: ${escHtml(e.bcc_address)}</div>`:''}
      </div>
      <div class="em-meta">${e.sent_at?new Date(e.sent_at).toLocaleDateString('en-GB',{day:'numeric',month:'short'}):''}</div>
    </div>`).join('');
}

// ---- Admin ----
async function loadAdmin() {
  // Show users card to admin only
  if (CURRENT_USER?.role==='admin') {
    document.getElementById('admin-users-card').style.display='';
    await loadAdminUsers();
  }
  await loadBrands();
  await loadStageProbs();
  renderRefLists();
}

async function loadAdminUsers() {
  const d = await apiFetch('/users'); if(!d) return;
  document.getElementById('admin-meta').textContent=d.length+' users';
  document.getElementById('admin-users-tbody').innerHTML=d.map(u=>`
    <tr>
      <td class="contact-cell"><div class="nm">${escHtml(u.name.split(' ').slice(1).join(' ')||'—')}</div><div class="co">${escHtml(u.name.split(' ')[0])}</div></td>
      <td style="color:var(--warm-grey)">${escHtml(u.email)}</td>
      <td><span class="pill ${u.role==='admin'?'green':'blue'}">${u.role}</span></td>
      <td style="display:flex;gap:6px">
        <button class="btn btn-secondary" style="padding:4px 10px;font-size:12px" onclick="openEditUserModal(${u.id},'${u.name}','${u.email}','${u.role}')">Edit</button>
        ${u.email!==CURRENT_USER?.email?`<button class="btn btn-secondary" style="padding:4px 10px;font-size:12px;color:var(--accent-coral)" onclick="deleteUser(${u.id},'${u.name}')">Remove</button>`:''}
      </td>
    </tr>`).join('');
}

var _stageProbs = {};
var _stageList = {pipeline: [], order: []};
async function loadStageProbs() {
  var r = await fetch('/crm-staging/api/admin/stages', {headers:{Authorization:'Bearer '+TOKEN}});
  if (!r.ok) return;
  var d = await r.json();
  _stageProbs = {};
  _stageList = {pipeline: d.pipeline||[], order: d.order||[], close_reason: d.close_reason||[]};
  (d.pipeline||[]).concat(d.order||[]).forEach(function(s){ _stageProbs[s.name] = s; });
}
async function updateStageProb(id, value) {
  await fetch('/crm-staging/api/admin/stages/' + id, {
    method: 'PUT',
    headers: {Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
    body: JSON.stringify({probability: value})
  });
}
function renderRefLists() {
  const renderList = (elId, items, type) => {
    const el=document.getElementById(elId); if(!el) return;
    el.innerHTML = items.map((item,i)=>`
      <div style="display:flex;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--line)">
        <span style="font-size:13px">${item}</span>
        <button onclick="removeRefItem('${type}',${i})" style="color:var(--accent-coral);font-size:12px;background:none;border:none;cursor:pointer">Remove</button>
      </div>`).join('');
  };
  const renderStatusList = (elId, items, type) => {
    const el=document.getElementById(elId); if(!el) return;
    el.innerHTML = items.map((item,i)=>{
      const s = _stageProbs[item];
      const probHtml = s
        ? `<input type="number" min="0" max="100" value="${s.probability||0}" data-sid="${s.id}" style="width:50px;text-align:center;border:1px solid var(--line);border-radius:4px;padding:2px 4px;font-size:12px" onchange="updateStageProb(parseInt(this.dataset.sid),parseInt(this.value))">%`
        : `<span style="color:var(--warm-grey);font-size:12px">—</span>`;
      return `<div style="display:flex;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--line)"><span style="font-size:13px;flex:1">${item}</span><div style="display:flex;align-items:center;gap:10px">${probHtml}<button onclick="removeRefItem('${type}',${i})" style="color:var(--accent-coral);font-size:12px;background:none;border:none;cursor:pointer">Remove</button></div></div>`;
    }).join('');
  };
  renderList('admin-regions-list',  getRegions(),   'region');
  renderList('admin-tags-list',     getTags(),      'tag');
  renderList('admin-countries-list',getCountries(), 'country');
  renderDbStageList('admin-statuses-list', 'pipeline');
  renderDbStageList('admin-order-statuses-list', 'order');
  renderDbStageListSimple('admin-close-reasons-list', 'close_reason');
}

function renderDbStageList(elId, stageType) {
  const el = document.getElementById(elId); if (!el) return;
  const stages = (_stageList[stageType] || []).slice().sort((a,b)=>a.position-b.position);
  el.innerHTML = stages.map(s =>
    `<div style="display:flex;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--line)">
      <span style="font-size:13px;flex:1">${s.label||s.name}</span>
      <div style="display:flex;align-items:center;gap:10px">
        <input type="number" min="0" max="100" value="${s.probability||0}" data-sid="${s.id}" style="width:50px;text-align:center;border:1px solid var(--line);border-radius:4px;padding:2px 4px;font-size:12px" onchange="updateStageProb(parseInt(this.dataset.sid),parseInt(this.value))">%
        <button onclick="deleteStageById(${s.id})" style="color:var(--accent-coral);font-size:12px;background:none;border:none;cursor:pointer">Remove</button>
      </div></div>`
  ).join('');
}
function renderDbStageListSimple(elId, stageType) {
  const el = document.getElementById(elId); if (!el) return;
  const stages = (_stageList[stageType] || []).slice().sort((a,b)=>a.position-b.position);
  el.innerHTML = stages.map(s =>
    `<div style="display:flex;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--line)">
      <span style="font-size:13px;flex:1">${s.label||s.name}</span>
      <button onclick="deleteStageById(${s.id})" style="color:var(--accent-coral);font-size:12px;background:none;border:none;cursor:pointer">Remove</button>
    </div>`
  ).join('');
}
async function deleteStageById(id) {
  if (!confirm('Remove this stage?')) return;
  await fetch('/crm-staging/api/admin/stages/'+id, {method:'DELETE', headers:{Authorization:'Bearer '+TOKEN}});
  await loadStageProbs(); renderRefLists();
}
function addRefItem(type) {
  const inputId = type === 'close_reason' ? 'new-close-reason-input' : 'new-'+type+'-input';
  const el = document.getElementById(inputId);
  const val = el.value.trim(); if(!val) return;
  if (type==='region') { const r=getRegions(); if(!r.includes(val)){r.push(val);r.sort();saveRegions(r);} el.value=''; renderRefLists(); populateFilterDropdowns(); return; }
  if (type==='tag')    { const t=getTags();    if(!t.includes(val)){t.push(val);t.sort();saveTags(t);}     el.value=''; renderRefLists(); populateFilterDropdowns(); return; }
  if (type==='country'){ const c=getCountries();if(!c.includes(val)){c.push(val);c.sort();saveCountries(c);} el.value=''; renderRefLists(); populateFilterDropdowns(); return; }
  // status + order_status → write to DB
  const stageType = type==='status' ? 'pipeline' : type==='order_status' ? 'order' : 'close_reason';
  const prob = (stageType === 'close_reason') ? null : 0;
  fetch('/crm-staging/api/admin/stages', {
    method:'POST',
    headers:{Authorization:'Bearer '+TOKEN,'Content-Type':'application/json'},
    body: JSON.stringify({stage_type:stageType, name:val, label:val, probability:prob})
  }).then(()=>loadStageProbs()).then(()=>{ renderRefLists(); populateFilterDropdowns(); });
  el.value='';
}
function removeRefItem(type, idx) {
  if (type==='region') { const r=getRegions(); r.splice(idx,1); saveRegions(r); }
  if (type==='tag')    { const t=getTags();    t.splice(idx,1); saveTags(t);    }
  if (type==='country'){ const c=getCountries();c.splice(idx,1);saveCountries(c); }
  renderRefLists(); populateFilterDropdowns();
}

function openNewUserModal() {
  document.getElementById('modal-title').innerHTML='New User';
  document.getElementById('modal-body').innerHTML=`
    <form onsubmit="saveNewUser(event)">
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Full Name</label>
        <input name="name" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Email</label>
        <input name="email" type="email" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Password</label>
        <input name="password" type="password" required minlength="8" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div style="margin-bottom:24px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Role</label>
        <select name="role" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
          <option value="agent">Agent</option><option value="admin">Admin</option>
        </select></div>
      <div id="nu-error" style="display:none;color:#B33A47;font-size:13px;margin-bottom:12px;padding:10px;background:#FAE3E5;border-radius:8px"></div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" onclick="document.getElementById('modal').style.display='none'" class="btn btn-secondary">Cancel</button>
        <button type="submit" class="btn btn-primary">Create User</button>
      </div>
    </form>`;
  document.getElementById('modal').style.display='flex';
}
async function saveNewUser(e) {
  e.preventDefault();
  const fd=new FormData(e.target);
  const r=await apiFetch('/users',{method:'POST',body:JSON.stringify({name:fd.get('name'),email:fd.get('email'),password:fd.get('password'),role:fd.get('role')})});
  if(r){document.getElementById('modal').style.display='none';loadAdminUsers();populateOwnerFilter();}
  else{document.getElementById('nu-error').textContent='Failed. Email may be in use.';document.getElementById('nu-error').style.display='block';}
}

function openEditUserModal(id,name,email,role) {
  document.getElementById('modal-title').innerHTML='Edit User';
  document.getElementById('modal-body').innerHTML=`
    <form onsubmit="saveEditUser(event,${id})">
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Full Name</label>
        <input name="name" value="${name}" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Email</label>
        <input name="email" type="email" value="${email}" required style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">New Password <span style="font-weight:400;text-transform:none;letter-spacing:0">(leave blank to keep)</span></label>
        <input name="password" type="password" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit"/></div>
      <div style="margin-bottom:24px"><label style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--warm-grey);display:block;margin-bottom:4px">Role</label>
        <select name="role" style="width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;background:var(--white)">
          <option value="agent" ${role==='agent'?'selected':''}>Agent</option>
          <option value="admin" ${role==='admin'?'selected':''}>Admin</option>
        </select></div>
      <div id="eu-error" style="display:none;color:#B33A47;font-size:13px;margin-bottom:12px;padding:10px;background:#FAE3E5;border-radius:8px"></div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" onclick="document.getElementById('modal').style.display='none'" class="btn btn-secondary">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Changes</button>
      </div>
    </form>`;
  document.getElementById('modal').style.display='flex';
}
async function saveEditUser(e,id) {
  e.preventDefault();
  const fd=new FormData(e.target);
  const payload={name:fd.get('name'),email:fd.get('email'),role:fd.get('role')};
  if(fd.get('password')) payload.password=fd.get('password');
  const btn=e.target.querySelector('[type=submit]'); btn.textContent='Saving…'; btn.disabled=true;
  const r=await apiFetch('/users/'+id,{method:'PUT',body:JSON.stringify(payload)});
  if(r){document.getElementById('modal').style.display='none';loadAdminUsers();populateOwnerFilter();}
  else{document.getElementById('eu-error').textContent='Failed.';document.getElementById('eu-error').style.display='block';btn.textContent='Save Changes';btn.disabled=false;}
}
async function deleteUser(id,name) {
  if(!confirm('Remove '+name+'? This cannot be undone.')) return;
  const r=await fetch(API+'/users/'+id,{method:'DELETE',headers:{'Authorization':'Bearer '+TOKEN}});
  if(r.ok) loadAdminUsers();
}

// ---- Filter dropdowns ----
function populateFilterDropdowns() {
  const regions=getRegions(), tags=getTags(), countries=getCountries();
  ['contact-filter-region','company-filter-region'].forEach(id=>{
    const el=document.getElementById(id); if(!el) return;
    el.innerHTML='<option value="">All regions</option>'+regions.map(r=>`<option>${r}</option>`).join('');
  });
  ['contact-filter-tag','company-filter-tag'].forEach(id=>{
    const el=document.getElementById(id); if(!el) return;
    el.innerHTML='<option value="">All groups</option>'+tags.map(t=>`<option>${t}</option>`).join('');
  });
  ['contact-filter-country','company-filter-country'].forEach(id=>{
    const el=document.getElementById(id); if(!el) return;
    el.innerHTML='<option value="">All countries</option>'+countries.map(c=>`<option>${c}</option>`).join('');
  });
  var fs = document.getElementById('filter-status');
  if (fs) {
    var curStatus = fs.value;
    fs.innerHTML = '<option value="">All statuses</option>' + getPipelineStatuses().map(function(s){ return '<option' + (s===curStatus?' selected':'') + '>' + s + '</option>'; }).join('');
  }
}

async function populateOwnerFilter() {
  const d=await apiFetch('/users'); if(!d) return;
  window._crmUsers = d;
  const of=document.getElementById('filter-owner');
  if(of) of.innerHTML='<option value="">All owners</option>'+d.map(u=>`<option value="${u.id}">${u.name}</option>`).join('');
}


// ---- Attachments ----
async function loadContactAttachments(contactId) {
  const el = document.getElementById('contact-attachments-list');
  if (!el) return;
  const data = await apiFetch('/contacts/'+contactId+'/attachments');
  if (!data || !data.length) {
    el.innerHTML = '<div style="font-size:13px;color:var(--warm-grey);margin-bottom:8px">No attachments.</div>';
    return;
  }
  el.innerHTML = data.map(a=>`
    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;background:var(--off-white);border-radius:8px;margin-bottom:6px">
      <div>
        <div style="font-size:13px;font-weight:500">${escHtml(a.filename)}</div>
        <div style="font-size:11px;color:var(--warm-grey)">${escHtml(a.uploaded_by)} · ${new Date(a.created_at).toLocaleDateString('en-GB')} · ${a.file_size?Math.ceil(a.file_size/1024)+'KB':''}</div>
      </div>
      <div style="display:flex;gap:6px">
        <button onclick="downloadAttachment(${contactId},${a.id},'${escHtml(a.filename).replace(/'/g,"\'")}')" class="btn btn-secondary" style="font-size:11px;padding:4px 10px">Download</button>
        <button onclick="deleteAttachment(${contactId},${a.id})" class="btn btn-secondary" style="font-size:11px;padding:4px 10px;color:#B33A47">Delete</button>
      </div>
    </div>`).join('');
}
async function uploadContactAttachment(contactId, input) {
  const files = input.files; if (!files.length) return;
  for (const file of files) {
    const fd = new FormData(); fd.append('file', file);
    const token = localStorage.getItem('crm_token')||'';
    const res = await fetch('/api/contacts/'+contactId+'/attachments', {method:'POST', headers:{'Authorization':'Bearer '+token}, body:fd});
    if (!res.ok) { showToast('Upload failed: '+file.name); }
  }
  input.value = '';
  loadContactAttachments(contactId);
  showToast('Uploaded');
}
async function downloadAttachment(contactId, attId, filename) {
  const token = localStorage.getItem('crm_token')||'';
  const res = await fetch('/api/contacts/'+contactId+'/attachments/'+attId+'/download', {headers:{'Authorization':'Bearer '+token}});
  if (!res.ok) { showToast('Download failed'); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=filename; a.click();
  setTimeout(()=>URL.revokeObjectURL(url), 5000);
}
async function deleteAttachment(contactId, attId) {
  if (!confirm('Delete this attachment?')) return;
  const r = await apiFetch('/contacts/'+contactId+'/attachments/'+attId, {method:'DELETE'});
  if (r) { loadContactAttachments(contactId); showToast('Deleted'); }
}

// ---- Contact Tasks ----
async function loadContactTasks(contactId) {
  const el = document.getElementById('contact-tasks-list');
  if (!el) return;
  const data = await apiFetch('/contacts/'+contactId+'/tasks');
  if (!data || !data.length) {
    el.innerHTML = '<div style="font-size:13px;color:var(--warm-grey);margin-bottom:8px">No tasks.</div>';
    return;
  }
  const today = new Date().toISOString().slice(0,10);
  el.innerHTML = data.map(t=>{
    const overdue = !t.completed && t.due_date && t.due_date < today;
    return `<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 12px;background:var(--off-white);border-radius:8px;margin-bottom:6px;${t.completed?'opacity:.6':''}">
      <input type="checkbox" ${t.completed?'checked':''} onchange="completeContactTask(${contactId},${t.id},this.checked)" style="margin-top:2px;cursor:pointer"/>
      <div style="flex:1">
        <div style="font-size:13px;${t.completed?'text-decoration:line-through':''}">${escHtml(t.title)}</div>
        <div style="font-size:11px;color:${overdue?'#B33A47':'var(--warm-grey)'}">
          ${t.due_date?'Due '+t.due_date:'No due date'}
          ${t.assigned_to?' · Assigned to '+escHtml(t.assigned_to):''}
          · Added by ${escHtml(t.created_by||'')}
        </div>
      </div>
    </div>`;
  }).join('');
}
async function addContactTask(contactId) {
  const title = (document.getElementById('new-task-title').value||'').trim();
  if (!title) return;
  const due   = document.getElementById('new-task-due').value||null;
  const asgEl = document.getElementById('new-task-assignee');
  const aid   = asgEl && asgEl.value ? parseInt(asgEl.value) : null;
  const r = await apiFetch('/contacts/'+contactId+'/tasks', {method:'POST', body:JSON.stringify({title, due_date:due, assigned_to_id:aid})});
  if (r) {
    document.getElementById('new-task-title').value = '';
    document.getElementById('new-task-due').value = '';
    loadContactTasks(contactId);
    showToast('Task added');
  }
}
async function completeContactTask(contactId, taskId, completed) {
  await apiFetch('/contacts/'+contactId+'/tasks/'+taskId, {method:'PUT', body:JSON.stringify({completed})});
  loadContactTasks(contactId);
}

// ---- Pipeline Notes ----
async function loadPipelineNotes(pipelineId) {
  const el = document.getElementById('pipeline-notes-list');
  if (!el) return;
  const data = await apiFetch('/pipeline/'+pipelineId+'/notes');
  if (!data || !data.length) {
    el.innerHTML = '<div style="font-size:13px;color:var(--warm-grey);margin-bottom:8px">No notes yet.</div>';
    return;
  }
  el.innerHTML = data.map(n=>`
    <div id="pnote-${n.id}" style="margin-bottom:8px;padding:10px 12px;background:var(--off-white);border-radius:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <div style="font-size:11px;color:var(--warm-grey)">
          <strong style="color:var(--navy)">${escHtml(n.author_name)}</strong>
          &nbsp;·&nbsp;${new Date(n.created_at).toLocaleString('en-GB',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})}
          ${n.updated_at?`<span style="color:var(--warm-grey)"> · edited by ${escHtml(n.updated_by||'')} ${new Date(n.updated_at).toLocaleString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}</span>`:''}
        </div>
        <button onclick="startEditPipelineNote(${pipelineId},${n.id})" class="btn btn-secondary" style="font-size:10px;padding:2px 8px">Edit</button>
      </div>
      <div id="pnote-body-${n.id}" style="font-size:13px;white-space:pre-wrap">${escHtml(n.body)}</div>
    </div>`).join('');
}
function startEditPipelineNote(pipelineId, noteId) {
  const bodyEl = document.getElementById('pnote-body-'+noteId);
  if (!bodyEl) return;
  const current = bodyEl.textContent;
  bodyEl.innerHTML = `<textarea style="width:100%;border:1px solid var(--line);border-radius:6px;padding:6px 10px;font:inherit;resize:vertical;box-sizing:border-box" rows="3">${escHtml(current)}</textarea>`+
    `<div style="display:flex;gap:6px;margin-top:6px;justify-content:flex-end">`+
    `<button onclick="savePipelineNoteEdit(${pipelineId},${noteId})" class="btn btn-primary" style="font-size:12px;padding:4px 12px">Save</button>`+
    `<button onclick="loadPipelineNotes(${pipelineId})" class="btn btn-secondary" style="font-size:12px;padding:4px 12px">Cancel</button>`+
    `</div>`;
}
async function savePipelineNoteEdit(pipelineId, noteId) {
  const bodyEl = document.getElementById('pnote-body-'+noteId);
  if (!bodyEl) return;
  const ta = bodyEl.querySelector('textarea');
  if (!ta) return;
  const body = ta.value.trim();
  if (!body) return;
  const r = await apiFetch('/pipeline/'+pipelineId+'/notes/'+noteId, {method:'PUT', body:JSON.stringify({body})});
  if (r) { loadPipelineNotes(pipelineId); showToast('Note updated'); }
}
async function addPipelineNote(pipelineId) {
  const bodyEl = document.getElementById('new-pipeline-note-body');
  const body   = (bodyEl ? bodyEl.value : '').trim();
  if (!body) return;
  const btn = document.querySelector('[onclick="addPipelineNote('+pipelineId+')"]');
  if (btn) { btn.textContent='Saving…'; btn.disabled=true; }
  const r = await apiFetch('/pipeline/'+pipelineId+'/notes', {method:'POST', body:JSON.stringify({body})});
  if (r) {
    if (bodyEl) bodyEl.value='';
    loadPipelineNotes(pipelineId);
    showToast('Note added');
  }
  if (btn) { btn.textContent='Add Note'; btn.disabled=false; }
}

// ---- Task Report ----
async function loadTaskReport() {
  const tbody = document.getElementById('task-report-body');
  if (!tbody) return;
  const sel = document.getElementById('task-report-filter');
  const filter = sel ? sel.value : 'open';
  tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--warm-grey)">Loading…</td></tr>';
  const data = await apiFetch('/reports/tasks?filter='+filter);
  if (!data) { tbody.innerHTML='<tr><td colspan="5" style="text-align:center;padding:24px;color:#B33A47">Failed to load.</td></tr>'; return; }
  if (!data.length) { tbody.innerHTML='<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--warm-grey)">No tasks found.</td></tr>'; return; }
  const today = new Date().toISOString().slice(0,10);
  tbody.innerHTML = data.map(t=>{
    const overdue = !t.completed && t.due_date && t.due_date < today;
    return `<tr onclick="openContactDetail(${t.contact_id})" style="cursor:pointer">
      <td class="contact-cell"><div class="nm">${escHtml(t.contact_company||t.contact_name||'—')}</div><div class="co">${escHtml(t.contact_company?t.contact_name||'':'')}</div></td>
      <td>${escHtml(t.title)}</td>
      <td>${escHtml(t.assigned_to||'—')}</td>
      <td style="color:${overdue?'#B33A47':'inherit'}">${t.due_date||'—'}</td>
      <td>${t.completed?'<span style="color:#4CAF50;font-weight:600">Done</span>':overdue?'<span style="color:#B33A47;font-weight:600">Overdue</span>':'<span style="color:var(--warm-grey)">Open</span>'}</td>
    </tr>`;
  }).join('');
}


// ---- Pipeline status multi-select ----
function toggleStatusDropdown() {
  var panel = document.getElementById('status-filter-panel');
  if (!panel) return;
  if (panel.style.display !== 'none') { panel.style.display = 'none'; return; }
  panel.innerHTML = getPipelineStatuses().map(function(s) {
    var checked = pipelineFilters.statuses.includes(s) ? 'checked' : '';
    var safe = s.replace(/'/g, '&#39;');
    return '<label style="display:flex;align-items:center;gap:8px;padding:7px 14px;cursor:pointer;font-size:13px" onmouseover="this.style.background=\x27var(--logo-blue-pale)\x27" onmouseout="this.style.background=\x27\x27">'
      + '<input type="checkbox" value="'+escHtml(s)+'" '+checked+' onclick="event.stopPropagation();toggleStatusFilter(\x27'+safe+'\x27)" style="cursor:pointer"/>'
      + '<span class="pill '+statusClass(s)+'">'+escHtml(s)+'</span></label>';
  }).join('');
  panel.style.display = 'block';
  setTimeout(function() { document.addEventListener('click', _closeStatusDropdown, {once:true}); }, 10);
}
function _closeStatusDropdown(e) {
  var wrap = document.getElementById('status-filter-wrap');
  if (wrap && wrap.contains(e.target)) {
    setTimeout(function(){ document.addEventListener('click', _closeStatusDropdown, {once:true}); }, 10);
    return;
  }
  var p = document.getElementById('status-filter-panel'); if (p) p.style.display = 'none';
}
function toggleStatusFilter(status) {
  var i = pipelineFilters.statuses.indexOf(status);
  if (i === -1) pipelineFilters.statuses.push(status);
  else pipelineFilters.statuses.splice(i, 1);
  updateStatusFilterBtn();
  pipelinePage = 1; loadPipeline();
}
function updateStatusFilterBtn() {
  var btn = document.getElementById('status-filter-btn'); if (!btn) return;
  var n = pipelineFilters.statuses.length;
  btn.textContent = n === 0 ? 'All statuses ▾' : n + ' status' + (n>1?'es':'') + ' selected ▾';
  btn.style.color = n > 0 ? 'var(--logo-blue-dark)' : 'var(--navy)';
  btn.style.borderColor = n > 0 ? 'var(--logo-blue-dark)' : 'var(--line)';
  btn.style.fontWeight = n > 0 ? '600' : '';
}

// ---- View router ----
async function loadView(view) {
  if(view==='dashboard') await loadDashboard();
  if(view==='contacts')  await loadContacts();
  if(view==='companies') await loadCompanies();
  if(view==='pipeline')  await loadPipeline();
  if(view==='brands')    await loadBrands();
  if(view==='reports')   await loadReports();
  if(view==='orders') await loadOrders();
  if(view==='tasks')     await loadMyTasks();
  if(view==='email')     await loadEmails();
  if(view==='admin')     await loadAdmin();
  if(view==='trash')     await loadTrash();
}

// ---- Event listeners ----
document.getElementById('pipeline-search')?.addEventListener('input',function(){pipelineFilters.search=this.value;pipelinePage=1;loadPipeline();});
document.getElementById('filter-brand')?.addEventListener('change',function(){pipelineFilters.brand_id=this.value;pipelinePage=1;loadPipeline();});
document.getElementById('filter-owner')?.addEventListener('change',function(){pipelineFilters.owner_id=this.value;pipelinePage=1;loadPipeline();});
document.getElementById('filter-clear')?.addEventListener('click',function(){
  pipelineFilters={search:'',brand_id:'',owner_id:'',statuses:[]};pipelinePage=1;
  ['pipeline-search','filter-brand','filter-owner'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  updateStatusFilterBtn(); loadPipeline();
});
document.getElementById('contact-search')?.addEventListener('input',function(){contactSearch=this.value;contactPage=1;loadContacts();});
document.getElementById('company-search')?.addEventListener('input',function(){companySearch=this.value;companyPage=1;loadCompanies();});
document.getElementById('modal-close')?.addEventListener('click',()=>{document.getElementById('modal').style.display='none';window._editFromReport=false;});
document.getElementById('modal')?.addEventListener('click',function(e){if(e.target===this){this.style.display='none';window._editFromReport=false;}});
document.getElementById('logout-btn')?.addEventListener('click', function() {
  var popup = document.createElement('div');
  popup.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999';
  popup.innerHTML = '<div style="background:#fff;border-radius:12px;padding:28px 32px;min-width:280px;box-shadow:0 8px 32px rgba(0,0,0,.18);text-align:center">'
    + '<div style="font-family:Playfair Display,serif;font-size:17px;color:var(--navy);font-weight:700;margin-bottom:8px">Sign out?</div>'
    + '<div style="font-size:13px;color:var(--warm-grey);margin-bottom:24px">You will need to sign in again to access the CRM.</div>'
    + '<div style="display:flex;gap:10px;justify-content:center">'
    + '<button onclick="this.closest(\'[style*=inset]\').remove()" style="padding:8px 20px;border:1px solid var(--line);border-radius:8px;background:#fff;font:inherit;font-size:13px;cursor:pointer">Cancel</button>'
    + '<button onclick="logout()" style="padding:8px 20px;background:var(--navy);color:#fff;border:none;border-radius:8px;font:inherit;font-size:13px;cursor:pointer">Sign out</button>'
    + '</div></div>';
  document.body.appendChild(popup);
});
document.getElementById('login-form')?.addEventListener('submit',async function(e){
  e.preventDefault();
  const btn=document.getElementById('login-btn'), err=document.getElementById('login-error');
  btn.textContent='Signing in…'; btn.disabled=true; err.style.display='none';
  try {
    await login(document.getElementById('login-email').value, document.getElementById('login-password').value);
    showApp();
    await loadBrands(); await populateOwnerFilter(); populateFilterDropdowns();
    activate('dashboard');
  } catch(ex) {
    err.textContent='Incorrect email or password.'; err.style.display='block';
    btn.textContent='Sign in'; btn.disabled=false;
  }
});

// ---- Collapsible sections ----
function toggleSection(id) {
  var el = document.getElementById(id);
  if (!el) return;
  var hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  var chevId = id.replace('-body', '-chevron');
  var chev = document.getElementById(chevId);
  if (chev) chev.textContent = hidden ? '▼' : '▶';
}

// ---- Boot ----
if (TOKEN) {
  showApp();
  loadBrands().then(()=>populateOwnerFilter()).then(()=>{ populateFilterDropdowns(); activate('dashboard'); });
} else {
  showLogin();
}



(function () {
  function reportError(data) {
    fetch('/api/log-client-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      keepalive: true
    }).catch(function () {});
  }
  window.onerror = function (message, source, lineno, colno, error) {
    reportError({
      message: String(message),
      source: source || '',
      lineno: lineno || 0,
      colno: colno || 0,
      stack: error && error.stack ? error.stack : '',
      url: window.location.href
    });
  };
  window.addEventListener('unhandledrejection', function (e) {
    var err = e.reason;
    reportError({
      message: err && err.message ? err.message : String(err),
      source: '',
      lineno: 0,
      colno: 0,
      stack: err && err.stack ? err.stack : '',
      url: window.location.href
    });
  });
})();

// ============================================================
// Stage 6 — Soft delete helpers
// ============================================================

async function deleteContactFromModal(contactId) {
  if (!confirm('Move this contact to trash?')) return;
  const r = await apiFetch('/contacts/'+contactId, {method:'DELETE'});
  if (r) {
    document.getElementById('modal').style.display='none';
    showToast('Contact moved to trash');
    loadContacts();
  }
}

async function deletePipelineEntry(entryId) {
  if (!confirm('Move this pipeline entry to trash?')) return;
  const r = await apiFetch('/pipeline/'+entryId, {method:'DELETE'});
  if (r) {
    document.getElementById('modal').style.display='none';
    showToast('Pipeline entry moved to trash');
    loadPipeline();
  }
}

// ---- Trash view ----
let trashData = null;
let trashTab = 'contacts';

function switchTrashTab(tab) {
  trashTab = tab;
  document.querySelectorAll('.trash-tab-btn').forEach(function(btn) {
    var active = btn.id === 'ttab-' + tab;
    btn.style.borderBottomColor = active ? 'var(--logo-blue-dark)' : 'transparent';
    btn.style.color = active ? 'var(--logo-blue-dark)' : 'var(--warm-grey)';
    btn.style.fontWeight = active ? '600' : '';
  });
  renderTrashTab();
}

function renderTrashTab() {
  var el = document.getElementById('trash-content');
  if (!el) return;
  if (!trashData) { el.innerHTML = '<div style="text-align:center;padding:40px;color:var(--warm-grey)">Loading…</div>'; return; }

  if (trashTab === 'contacts') {
    var items = trashData.contacts;
    if (!items || !items.length) { el.innerHTML = '<div style="padding:24px;color:var(--warm-grey);font-size:13px">No contacts in trash.</div>'; return; }
    var rows = items.map(function(i) {
      return '<tr>' +
        '<td style="padding:10px 12px;font-size:13px"><strong>' + escHtml(i.name||'—') + '</strong>' + (i.company ? '<br><span style="font-size:11px;color:var(--warm-grey)">'+escHtml(i.company)+'</span>' : '') + '</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey)">' + escHtml(i.email||'—') + '</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey)">' + i.days_since + ' day' + (i.days_since!==1?'s':'') + ' ago</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:' + (i.days_remaining <= 3 ? '#B33A47' : 'var(--warm-grey)') + '">' + i.days_remaining + ' day' + (i.days_remaining!==1?'s':'') + ' left</td>' +
        '<td style="padding:10px 12px;white-space:nowrap">' +
          '<button onclick="restoreTrashItem(\x27contact\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;margin-right:4px">Restore</button>' +
          '<button onclick="hardDeleteTrashItem(\x27contact\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;color:#B33A47">Delete</button>' +
        '</td></tr>';
    });
    el.innerHTML = '<table style="width:100%;border-collapse:collapse"><thead><tr style="border-bottom:1px solid var(--line)">' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Name</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Email</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Deleted</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Remaining</th>' +
      '<th></th></tr></thead><tbody>' + rows.join('') + '</tbody></table>';
  } else if (trashTab === 'pipeline') {
    var items = trashData.pipeline;
    if (!items || !items.length) { el.innerHTML = '<div style="padding:24px;color:var(--warm-grey);font-size:13px">No pipeline entries in trash.</div>'; return; }
    var rows = items.map(function(i) {
      return '<tr>' +
        '<td style="padding:10px 12px;font-size:13px">' + escHtml(i.contact_name||'—') + '</td>' +
        '<td style="padding:10px 12px;font-size:13px">' + escHtml(i.brand_name||'—') + '</td>' +
        '<td style="padding:10px 12px;font-size:12px"><span class="pill blue">' + escHtml(i.status||'') + '</span></td>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey)">' + i.days_since + ' day' + (i.days_since!==1?'s':'') + ' ago</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:' + (i.days_remaining <= 3 ? '#B33A47' : 'var(--warm-grey)') + '">' + i.days_remaining + ' day' + (i.days_remaining!==1?'s':'') + ' left</td>' +
        '<td style="padding:10px 12px;white-space:nowrap">' +
          '<button onclick="restoreTrashItem(\x27pipeline\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;margin-right:4px">Restore</button>' +
          '<button onclick="hardDeleteTrashItem(\x27pipeline\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;color:#B33A47">Delete</button>' +
        '</td></tr>';
    });
    el.innerHTML = '<table style="width:100%;border-collapse:collapse"><thead><tr style="border-bottom:1px solid var(--line)">' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Contact</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Brand</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Status</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Deleted</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Remaining</th>' +
      '<th></th></tr></thead><tbody>' + rows.join('') + '</tbody></table>';
  } else if (trashTab === 'orders') {
    var items = trashData.orders;
    if (!items || !items.length) { el.innerHTML = '<div style="padding:24px;color:var(--warm-grey);font-size:13px">No orders in trash.</div>'; return; }
    var rows = items.map(function(i) {
      return '<tr>' +
        '<td style="padding:10px 12px;font-size:13px">' + escHtml(i.contact_name||'—') + '</td>' +
        '<td style="padding:10px 12px;font-size:13px">' + escHtml(i.brand_name||'—') + '</td>' +
        '<td style="padding:10px 12px;font-size:13px;font-weight:600">' + fmtVal(i.order_value) + '</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey)">' + i.days_since + ' day' + (i.days_since!==1?'s':'') + ' ago</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:' + (i.days_remaining <= 3 ? '#B33A47' : 'var(--warm-grey)') + '">' + i.days_remaining + ' day' + (i.days_remaining!==1?'s':'') + ' left</td>' +
        '<td style="padding:10px 12px;white-space:nowrap">' +
          '<button onclick="restoreTrashItem(\x27order\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;margin-right:4px">Restore</button>' +
          '<button onclick="hardDeleteTrashItem(\x27order\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;color:#B33A47">Delete</button>' +
        '</td></tr>';
    });
    el.innerHTML = '<table style="width:100%;border-collapse:collapse"><thead><tr style="border-bottom:1px solid var(--line)">' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Contact</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Brand</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Value</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Deleted</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Remaining</th>' +
      '<th></th></tr></thead><tbody>' + rows.join('') + '</tbody></table>';
  } else if (trashTab === 'notes') {
    var cNotes = (trashData.contact_notes || []).map(function(i) {
      return '<tr>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey)">Contact</td>' +
        '<td style="padding:10px 12px;font-size:13px">' + escHtml(i.contact_name||'—') + '</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey);max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escHtml(i.body_preview||'') + '</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey)">' + i.days_since + ' day' + (i.days_since!==1?'s':'') + ' ago</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:' + (i.days_remaining <= 3 ? '#B33A47' : 'var(--warm-grey)') + '">' + i.days_remaining + ' day' + (i.days_remaining!==1?'s':'') + ' left</td>' +
        '<td style="padding:10px 12px;white-space:nowrap">' +
          '<button onclick="restoreTrashItem(\x27contact_note\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;margin-right:4px">Restore</button>' +
          '<button onclick="hardDeleteTrashItem(\x27contact_note\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;color:#B33A47">Delete</button>' +
        '</td></tr>';
    });
    var pNotes = (trashData.pipeline_notes || []).map(function(i) {
      return '<tr>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey)">Pipeline</td>' +
        '<td style="padding:10px 12px;font-size:13px">' + escHtml((i.contact_name||'—') + (i.brand_name?' / '+i.brand_name:'')) + '</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey);max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escHtml(i.body_preview||'') + '</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:var(--warm-grey)">' + i.days_since + ' day' + (i.days_since!==1?'s':'') + ' ago</td>' +
        '<td style="padding:10px 12px;font-size:12px;color:' + (i.days_remaining <= 3 ? '#B33A47' : 'var(--warm-grey)') + '">' + i.days_remaining + ' day' + (i.days_remaining!==1?'s':'') + ' left</td>' +
        '<td style="padding:10px 12px;white-space:nowrap">' +
          '<button onclick="restoreTrashItem(\x27pipeline_note\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;margin-right:4px">Restore</button>' +
          '<button onclick="hardDeleteTrashItem(\x27pipeline_note\x27,'+i.id+')" class="btn btn-secondary" style="font-size:11px;padding:3px 10px;color:#B33A47">Delete</button>' +
        '</td></tr>';
    });
    var allRows = cNotes.concat(pNotes);
    if (!allRows.length) { el.innerHTML = '<div style="padding:24px;color:var(--warm-grey);font-size:13px">No notes in trash.</div>'; return; }
    el.innerHTML = '<table style="width:100%;border-collapse:collapse"><thead><tr style="border-bottom:1px solid var(--line)">' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Type</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Contact / Brand</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Preview</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Deleted</th>' +
      '<th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--warm-grey)">Remaining</th>' +
      '<th></th></tr></thead><tbody>' + allRows.join('') + '</tbody></table>';
  }
}

async function loadTrash() {
  trashData = null;
  var el = document.getElementById('trash-content');
  if (el) el.innerHTML = '<div style="text-align:center;padding:40px;color:var(--warm-grey)">Loading…</div>';
  var data = await apiFetch('/trash');
  if (data) {
    trashData = data;
    renderTrashTab();
  } else {
    if (el) el.innerHTML = '<div style="text-align:center;padding:40px;color:#B33A47">Failed to load trash.</div>';
  }
}

async function restoreTrashItem(itemType, itemId) {
  const r = await apiFetch('/trash/'+itemType+'/'+itemId+'/restore', {method:'POST'});
  if (r) {
    showToast('Item restored');
    await loadTrash();
  }
}

async function hardDeleteTrashItem(itemType, itemId) {
  if (!confirm('Permanently delete? This cannot be undone.')) return;
  const r = await apiFetch('/trash/'+itemType+'/'+itemId, {method:'DELETE'});
  if (r) {
    showToast('Permanently deleted');
    await loadTrash();
  }
}

