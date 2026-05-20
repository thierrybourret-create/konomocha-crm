#!/usr/bin/env python3
"""
Adds PUT and DELETE endpoints to users router.
Run from: /home/thierry/konomocha-crm (with venv active)
"""
import sys
sys.path.insert(0, '/home/thierry/konomocha-crm')

target = '/home/thierry/konomocha-crm/app/routers/users.py'

with open(target, 'r') as f:
    content = f.read()

additions = ''

if 'def update_user' not in content:
    additions += '''

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None

@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    if data.name:  u.name  = data.name
    if data.email: u.email = data.email
    if data.role:  u.role  = data.role
    if data.password: u.hashed_password = hash_password(data.password)
    db.commit()
    db.refresh(u)
    return user_to_dict(u)
'''
    print("PUT endpoint added")
else:
    print("PUT endpoint already exists")

if 'def delete_user' not in content:
    additions += '''

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if current_user.id == user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u)
    db.commit()
    return {"ok": True}
'''
    print("DELETE endpoint added")
else:
    print("DELETE endpoint already exists")

if additions:
    with open(target, 'a') as f:
        f.write(additions)
    print("Router patched.")
else:
    print("Nothing to add.")
