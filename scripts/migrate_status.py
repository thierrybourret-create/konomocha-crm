import sys
sys.path.insert(0, '/home/thierry/konomocha-crm')
from dotenv import load_dotenv
load_dotenv('/home/thierry/konomocha-crm/.env')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

r = db.execute(text("SELECT count(*) FROM pipeline_entries WHERE status::text = 'Pricing Sent'")).scalar()
print('Pricing Sent records to merge:', r)

db.execute(text('ALTER TABLE pipeline_entries ADD COLUMN status_text VARCHAR(100)'))
db.execute(text("UPDATE pipeline_entries SET status_text = CASE WHEN status::text = 'Pricing Sent' THEN 'Price List Sent' ELSE status::text END"))
db.execute(text('ALTER TABLE pipeline_entries ALTER COLUMN status_text SET NOT NULL'))
db.execute(text('ALTER TABLE pipeline_entries DROP COLUMN status'))
db.execute(text('ALTER TABLE pipeline_entries RENAME COLUMN status_text TO status'))
db.execute(text('DROP TYPE IF EXISTS pipelinestatus'))
db.commit()
print('Done.')
db.close()
