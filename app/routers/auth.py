from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
import json
from app.auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token({"sub": user.email, "role": user.role, "name": user.name})
    crm = None
    if user.crm_role:
        # #9: fixed bare except
        try:
            p = json.loads(user.crm_role.permissions) if user.crm_role.permissions else None
        except Exception:
            p = None
        crm = {"id": user.crm_role.id, "name": user.crm_role.name, "permissions": p}
    return {"access_token": token, "token_type": "bearer", "role": user.role, "name": user.name, "crm_role": crm}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """#33: Logout endpoint — client must discard the JWT token.
    JWTs are stateless so there is no server-side revocation here;
    the short ACCESS_TOKEN_EXPIRE_MINUTES (60 min) limits exposure.
    """
    return {"ok": True}
