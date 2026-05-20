#!/usr/bin/env python3
"""
Konomocha CRM — Data Reset Script
Deletes ALL contacts, brands, pipeline entries, orders and email logs.
Users are preserved.
Usage: python3 reset_data.py
Run from: /home/thierry/konomocha-crm (with venv active)
"""

import sys
sys.path.insert(0, '/home/thierry/konomocha-crm')
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.models import Contact, Brand, PipelineEntry, Order, EmailLog

def reset():
    confirm = input("This will delete ALL contacts, brands, pipeline, orders and emails. Type YES to confirm: ")
    if confirm.strip() != 'YES':
        print("Aborted.")
        return

    db = SessionLocal()
    try:
        el = db.query(EmailLog).delete()
        o  = db.query(Order).delete()
        p  = db.query(PipelineEntry).delete()
        c  = db.query(Contact).delete()
        b  = db.query(Brand).delete()
        db.commit()
        print(f"Deleted: {el} emails, {o} orders, {p} pipeline entries, {c} contacts, {b} brands.")
        print("Users preserved. Ready for production import.")
    finally:
        db.close()

if __name__ == '__main__':
    reset()
