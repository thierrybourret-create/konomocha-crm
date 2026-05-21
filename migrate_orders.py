import sys
sys.path.insert(0, '/home/thierry/konomocha-crm')
from dotenv import load_dotenv
load_dotenv('/home/thierry/konomocha-crm/.env')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

for col, dtype in [('po_date','DATE'),('pi_date','DATE'),('deposit_date','DATE'),('fob_date','DATE'),('payment_date','DATE')]:
    try:
        db.execute(text(f'ALTER TABLE orders ADD COLUMN {col} {dtype}'))
        db.commit()
        print(f'Added {col}')
    except Exception as e:
        db.rollback()
        print(f'Skip {col}: already exists')

try:
    db.execute(text('ALTER TABLE orders ADD COLUMN status_text VARCHAR(100)'))
    db.execute(text("UPDATE orders SET status_text = status::text"))
    db.execute(text("ALTER TABLE orders ALTER COLUMN status_text SET DEFAULT 'PO Received'"))
    db.execute(text('ALTER TABLE orders DROP COLUMN status'))
    db.execute(text('ALTER TABLE orders RENAME COLUMN status_text TO status'))
    db.execute(text('DROP TYPE IF EXISTS orderstatus'))
    db.commit()
    print('Status converted to VARCHAR')
except Exception as e:
    db.rollback()
    print(f'Status conversion: {e}')

try:
    db.execute(text('ALTER TABLE orders ALTER COLUMN gross_commission_rate TYPE NUMERIC(12,2)'))
    db.commit()
    print('gross_commission_rate precision updated')
except Exception as e:
    db.rollback()
    print(f'Rate precision: {e}')

print('Done.')
db.close()
