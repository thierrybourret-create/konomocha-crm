#!/usr/bin/env python3
"""Check and fix pipeline POST endpoint."""
import sys
sys.path.insert(0, '/home/thierry/konomocha-crm')

target = '/home/thierry/konomocha-crm/app/routers/pipeline.py'
with open(target, 'r') as f:
    content = f.read()

print("Has POST endpoint:", '@router.post' in content)
print("Has contact_id in create:", 'contact_id' in content)

if '@router.post' not in content:
    print("Adding POST endpoint...")
    addition = '''

class PipelineCreate(BaseModel):
    contact_id: int
    brand_id: int
    status: str
    potential_value: float = 0
    owner_id: int
    due_date: Optional[str] = None
    next_action: Optional[str] = None
    notes: Optional[str] = None

@router.post("")
def create_pipeline_entry(data: PipelineCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import PipelineStatus
    from datetime import date
    due = None
    if data.due_date:
        try: due = date.fromisoformat(data.due_date)
        except: pass
    try:
        status_enum = PipelineStatus(data.status)
    except:
        status_enum = PipelineStatus.in_progress
    e = PipelineEntry(
        contact_id=data.contact_id, brand_id=data.brand_id,
        status=status_enum, potential_value=data.potential_value,
        owner_id=data.owner_id, due_date=due,
        next_action=data.next_action, notes=data.notes
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"id": e.id, "status": "created"}
'''
    with open(target, 'a') as f:
        f.write(addition)
    print("POST endpoint added.")
else:
    print("POST endpoint already exists — no change needed.")

# Also check imports
if 'from pydantic import BaseModel' not in content and '@router.post' not in content:
    print("WARNING: BaseModel import may be missing — check manually")
