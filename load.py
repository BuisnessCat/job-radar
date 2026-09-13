import psycopg
import os
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()
db_password = os.getenv("DB_PASSWORD")
DSN = f"dbname=postgres user=postgres password={db_password} port=5433"

def read_jobs_from_db():
    with psycopg.connect(DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT title, company, url, location FROM job")
            return cur.fetchall()

def load_jobs_to_db(jobs):
    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            for job in jobs:
                cur.execute(
                    "INSERT INTO job (title, company, url, location, source_id) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (source_id) DO NOTHING",
                    (job["title"], job["company"], job["url"], job["location"], job["url"])
                )


















