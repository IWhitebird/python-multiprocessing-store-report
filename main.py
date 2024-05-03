import sys
sys.dont_write_bytecode = True

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import StoreReport
from models import Store
from database import engine
from scripts import Seeding , TimeUtils


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(StoreReport.router)

@app.get("/")
def root():
    return {"Server Status": "Running"}

def create():
    Store.Base.metadata.create_all(engine)

def delete():
    Store.Base.metadata.drop_all(engine)


# def seed():
#     delete()
#     create()
#     Seeding.Seed().SeedIt()
# seed()



