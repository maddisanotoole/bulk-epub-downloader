from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
# uvicorn server:app --host 0.0.0.0 --port 8000

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)