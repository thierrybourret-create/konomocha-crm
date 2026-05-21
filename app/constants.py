from datetime import date
from decimal import Decimal

PIPELINE_PROBABILITIES = {
    'Awaiting Info':      10,
    'Awaiting Feedback':  10,
    'Form Completed':     10,
    'On Hold':            10,
    'Awaiting Samples':   20,
    'Samples Requested':  20,
    'Samples Sent':       20,
    'Samples Delivered':  20,
    'Catalogue Sent':     30,
    'Price List Sent':    30,
    'Pricing Sent':       30,
    'Quotation Sent':     30,
    'In Progress':        30,
    'Deposit Paid':       80,
    'Order Placed':       50,
    'Stalled':             0,
    'Closed / No Action':  0,
    'Cancelled':           0,
}

ORDER_STATUSES = [
    'po_received', 'deposit_paid', 'shipped', 'fully_paid',
    'commission_invoiced', 'commission_paid', 'bonus_paid',
]

ORDER_STATUS_LABELS = {
    'po_received':         'PO Received',
    'deposit_paid':        'Deposit Paid',
    'shipped':             'Shipped',
    'fully_paid':          'Fully Paid',
    'commission_invoiced': 'Commission Invoiced',
    'commission_paid':     'Commission Paid',
    'bonus_paid':          'Bonus Paid',
}

ORDER_STATUS_DATES = {
    'po_received':         'po_date',
    'deposit_paid':        'deposit_date',
    'shipped':             'ship_date',
    'fully_paid':          'fully_paid_date',
    'commission_invoiced': 'commission_invoiced_date',
    'commission_paid':     'commission_paid_date',
    'bonus_paid':          'bonus_paid_date',
}

BONUS_RATE = Decimal('0.05')
COMMISSION_LAG_DAYS = 30


def fy_start_year(dt):
    return dt.year if dt.month >= 4 else dt.year - 1


def fy_label(fsy):
    return f"FY{fsy}-{str(fsy+1)[2:]}"


def quarter_of(dt):
    fsy = fy_start_year(dt)
    q = ((dt.month - 4) % 12) // 3 + 1
    return fsy, q


def quarter_label(fsy, q):
    return f"Q{q} {fy_label(fsy)}"


def quarter_date_range(fsy, q):
    sm = {1: 4, 2: 7, 3: 10, 4: 1}[q]
    sy = fsy + 1 if q == 4 else fsy
    start = date(sy, sm, 1)
    em = sm + 3
    if em > 12:
        end = date(sy + 1, em - 12, 1)
    else:
        end = date(sy, em, 1)
    return start, end


def add_months(d, n):
    total = (d.year * 12 + d.month - 1) + n
    return date(total // 12, total % 12 + 1, 1)
