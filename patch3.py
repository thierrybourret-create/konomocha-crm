with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

changes = []

# 1. Remove Brands from sidebar
changes.append((
    '      <button class="sb-item" data-view="brands">\n'
    '        <svg class="sb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><circle cx="7" cy="7" r="1.5"></circle></svg>\n'
    '        <span>Brands</span>\n'
    '        <span class="sb-count" id="sb-count-brands">—</span>\n'
    '      </button>\n',
    ''
))

# 2. Remove +New Deal button from header
changes.append((
    '        <button class="btn btn-primary" onclick="openNewDealModal()">\n'
    '          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>\n'
    '          New deal\n'
    '        </button>\n',
    ''
))

# 3. Fix fmtNum to use explicit en-GB locale so commas always appear
changes.append((
    'function fmtNum(n) { return Number(n||0).toLocaleString(); }',
    "function fmtNum(n) { return Number(n||0).toLocaleString('en-GB'); }"
))

for old, new in changes:
    if old not in h:
        print('NOT FOUND: ' + old[:80])
    else:
        h = h.replace(old, new)
        print('OK: ' + old[:60])

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved.')
