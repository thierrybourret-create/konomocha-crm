"""Audit log helper — write one row per field change."""
from app.models.models import AuditLog
from decimal import Decimal


def _values_equal(a, b):
    """Compare two values; treat numerically-equal floats/decimals as equal."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except Exception:
        return str(a).strip() == str(b).strip()


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
    Skips fields where values are numerically equal to avoid float/decimal noise.
    """
    resolve = resolve or {}
    for field in tracked_fields:
        if field not in new_data:
            continue
        old = getattr(old_obj, field, None)
        new = new_data[field]
        if _values_equal(old, new):
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


def log_created_pipeline(db, e, user_id, user_name):
    """Log a pipeline entry creation with its key initial values as new_value summary."""
    parts = []
    if e.status:
        parts.append('Status: ' + e.status)
    if e.potential_value:
        parts.append('Value: $' + '{:,.0f}'.format(float(e.potential_value)))
    if e.owner:
        parts.append('Owner: ' + e.owner.name)
    if e.fob_date:
        parts.append('FOB: ' + str(e.fob_date))
    summary = ' · '.join(parts) if parts else None
    cname = e.contact.name if e.contact else None
    bname = e.brand.name   if e.brand   else None
    log_audit(db, entity_type='pipeline', entity_id=e.id,
              contact_name=cname, brand_name=bname,
              action='created', new_value=summary,
              user_id=user_id, user_name=user_name)


def log_created_order(db, o, user_id, user_name):
    """Log an order creation with its key initial values as new_value summary."""
    parts = []
    if o.order_value:
        parts.append('Value: $' + '{:,.0f}'.format(float(o.order_value)))
    if o.status:
        parts.append('Status: ' + o.status)
    if o.owner:
        parts.append('Owner: ' + o.owner.name)
    if o.order_date:
        parts.append('Date: ' + str(o.order_date))
    summary = ' · '.join(parts) if parts else None
    cname = o.contact.name if o.contact else None
    bname = o.brand.name   if o.brand   else None
    log_audit(db, entity_type='order', entity_id=o.id,
              contact_name=cname, brand_name=bname,
              action='created', new_value=summary,
              user_id=user_id, user_name=user_name)
