from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy.pool as pool
import psycopg2




# settings = {
#     'username': 'postgres.smjwpofcgfkjdwvwdtao',
#     'password': '6(eivQYD?i88b(H',
#     'hostname': 'aws-0-ap-south-1.pooler.supabase.com',
#     'port': '5432',
#     'database_name': 'postgres'
# }

settings = {
    'username': 'root',
    'password': 'root',
    'hostname': '127.0.0.1',
    'port': '5432',
    'database_name': 'blade'
}

SQLALCHEMY_DATABASE_URL = f'postgresql://{settings["username"]}:{settings["password"]}@{settings["hostname"]}:{settings["port"]}/{settings["database_name"]}'

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=20, max_overflow=0)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:    
        db.commit()
        yield db
    finally:
        db.close()
        
# Base.metadata.create_all(engine)
