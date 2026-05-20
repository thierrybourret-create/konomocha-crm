with open('/home/thierry/konomocha-crm/static/index.html', encoding='utf-8') as f:
    h = f.read()

# 1. Add modal-footer div (actual string has style="padding:24px;")
old_modal = '    <div id="modal-body" style="padding:24px;"></div>\n  </div>\n</div>'
new_modal = ('    <div id="modal-body" style="padding:24px;"></div>\n'
             '    <div id="modal-footer" style="display:flex;gap:8px;justify-content:flex-end;padding:0 24px 20px;margin-top:8px;border-top:1px solid var(--line)"></div>\n'
             '  </div>\n</div>')
if old_modal not in h:
    print('NOT FOUND: modal-body with padding style')
else:
    h = h.replace(old_modal, new_modal)
    print('OK: modal-footer div added')

# 2. Wire Convert to Order button in openPipelineDetail
old_detail_end = (
    "  document.getElementById('modal').style.display = 'flex';\n"
    "}\n"
    "\n"
    "\nfunction sortPipeline(col) {"
)
new_detail_end = (
    "  document.getElementById('modal-footer').innerHTML = "
    "`<button class=\"btn btn-secondary\" onclick=\"document.getElementById('modal').style.display='none'\">Close</button>"
    "<button class=\"btn btn-primary\" onclick=\"openConvertToOrderModal(${e.id})\">Convert to Order</button>`;\n"
    "  document.getElementById('modal').style.display = 'flex';\n"
    "}\n"
    "\n"
    "\nfunction sortPipeline(col) {"
)
if old_detail_end not in h:
    print('NOT FOUND: openPipelineDetail end')
else:
    h = h.replace(old_detail_end, new_detail_end)
    print('OK: Convert to Order button wired in openPipelineDetail')

with open('/home/thierry/konomocha-crm/static/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
print('Saved index.html.')
