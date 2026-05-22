"""Audit log helper — write one row per field change."""
from app.models.models import AuditLog


def log_audit(db, *, entity_type, entity_id,
              contact_name=None, brand_name=None,
              action, field_name=None,
              old_value=None, new_value=None,
              user_id, user_name):
    """Append one audit row. Caller is responsible for db.commit()."""
    entry = AuditLog(
        entity_type  = entity_type,
        entity_id    = entity_id,
        contact_name = contact_name,
        brand_name   = brand_name,
        action       = action,
        field_name   = field_name,
        old_value    = str(old_value) if old_value is not None else None,
        new_value    = str(new_value) if new_value is not None else None,
        user_id      = user_id,
        user_name    = user_name,
    )
    db.add(entry)


# Fields we track for pipeline entry updates (in display order)
PIPELINE_TRACKED = [
    'status', 'potential_value', 'close_reason',
    'owner_id', 'brand_id', 'fob_date', 'next_action',
]

# Fields we track for order updates
ORDER_TRACKED = [
    'order_value', 'gross_commission_rate', 'testing_cost_deduction',
    'owner_id', 'brand_id', 'order_date', 'notes',
]


def diff_and_log(db, *, entity_type, entity_id, contact_name, brand_name,
                 old_obj, new_data, tracked_fields,
                 resolve=None, user_id, user_name):
    """
    Compare old_obj fields against new_data dict, log a row for each change.
    resolve: optional dict {field: callable(val)->str} for human-readable values.
    """
    resolve = resolve or {}
    for field in tracked_fields:
        if field not in new_data:
            continue
        old = getattr(old_obj, field, None)
        new = new_data[field]
        if str(old) == str(new):
            continue
        fmt = resolve.get(field, str)
        log_audit(db,
                  entity_type  = entity_type,
                  entity_id    = entity_id,
                  contact_name = contact_name,
                  brand_name   = brand_name,
                  action       = 'updated',
                  field_name   = field,
                  old_value    = fmt(old) if old is not None else None,
                  new_value    = fmt(new) if new is not None else None,
                  user_id      = user_id,
                  user_name    = user_name)
