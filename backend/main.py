from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from database import SessionLocal, engine, Base
from datetime import datetime 
from schemas import TodoCreate, TodoResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
