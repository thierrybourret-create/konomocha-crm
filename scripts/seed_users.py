import sys

sys.path.insert(0, '/home/thierry/konomocha-crm')

from app.database import SessionLocal

from app.models.models import User, UserRole

from app.auth import hash_password

from dotenv import load_dotenv

load_dotenv()

db = SessionLocal()

users = [

    {"name": "Thierry", "email": "thierry@konomocha.com", "password": "thierry@2484!", "role": UserRole.admin},

    {"name": "Zeal",    "email": "zeal@konomocha.com",    "password": "zeal@2484!", "role": UserRole.agent},

    {"name": "Erna",    "email": "erna@konomocha.com",    "password": "erna@2484!", "role": UserRole.agent},

]

for u in users:

    if not db.query(User).filter(User.email == u["email"]).first():

        db.add(User(

            name=u["name"],

            email=u["email"],

            hashed_password=hash_password(u["password"]),

            role=u["role"]

        ))

        print(f"Created user: {u['name']}")

    else:

        print(f"User already exists: {u['name']}")

db.commit()

db.close()

print("Done.")

