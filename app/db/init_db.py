# app/db/init_db.py
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL non impostata nel .env")

INIT_SQL = """
CREATE TABLE IF NOT EXISTS brews (
  id BIGSERIAL PRIMARY KEY,
  coffee TEXT NOT NULL,
  dose DOUBLE PRECISION NOT NULL,
  ratio DOUBLE PRECISION NOT NULL,
  water DOUBLE PRECISION NOT NULL,
  temperature INTEGER NOT NULL DEFAULT 94,
  grind TEXT NOT NULL DEFAULT 'medium',
  rating INTEGER NULL,
  notes TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

def init_db():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(INIT_SQL)
        conn.commit()
