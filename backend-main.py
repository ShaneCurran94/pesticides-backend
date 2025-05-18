from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
import requests
import csv
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Create table if not exists
@app.on_event("startup")
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

class LogEntry(BaseModel):
    name: str
    amount: float

@app.post("/api/log")
def log_pesticide(entry: LogEntry):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (name, amount) VALUES (%s, %s)", (entry.name, entry.amount))
    conn.commit()
    conn.close()
    return {"message": "Logged successfully"}

# Global cache for pesticide data
cached_pesticides = []

@app.on_event("startup")
def fetch_pesticides_csv():
    global cached_pesticides
    url = "https://raw.githubusercontent.com/ShaneCurran94/PesticidesApp/b0256ce028368b627666aa82007720e2e325637e/active_substances.csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        cached_pesticides = [
            {"id": idx + 1, "name": row.get("Substance Name") or row.get("substance_name", "Unknown")}
            for idx, row in enumerate(reader)
        ]
        print(f"✅ Fetched {len(cached_pesticides)} pesticide substances.")
    except Exception as e:
        print(f"❌ Error fetching pesticides: {e}")

@app.get("/api/pesticides")
def get_pesticides():
    return cached_pesticides
