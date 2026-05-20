#!/usr/bin/env python3
"""Fix Thierry's name to Thierry Bourret in the database."""
import sys
sys.path.insert(0, '/home/thierry/konomocha-crm')
from dotenv import load_dotenv
load_dotenv()
from app.database import SessionLocal
from app.models.models import User

db = SessionLocal()
u = db.query(User).filter(User.email == 'thierry@konomocha.com').first()
if u:
    u.name = 'Thierry Bourret'
    db.commit()
    print("Updated: Thierry Bourret")
else:
    print("User not found")
db.close()
