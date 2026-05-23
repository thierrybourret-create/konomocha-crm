"""
Centralised permission helpers.

Usage:
    from app.permissions import get_page_scope, has_scope_all

    scope = get_page_scope(current_user, "contacts")  # 'all' | 'own'
    if not has_scope_all(current_user, "orders"):
        q = q.filter(Order.owner_id == current_user.id)
"""
import json
from app.models.models import User


def get_page_scope(user: User, page: str) -> str:
    """Return 'all' or 'own' for *user* on *page*.

    Admins always get 'all'.  For other roles the value comes from the CRM-role
    permissions JSON; the default when nothing is configured is 'own'.
    """
    if user.role == "admin":
        return "all"
    _perms = None
    if user.crm_role and user.crm_role.permissions:
        try:
            _perms = json.loads(user.crm_role.permissions)
        except Exception:
            pass
    return (_perms or {}).get("pages", {}).get(page, "own")


def has_scope_all(user: User, page: str) -> bool:
    """Shorthand: True if *user* has 'all' access to *page*."""
    return get_page_scope(user, page) == "all"
