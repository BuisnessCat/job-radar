import psycopg
import os
from dotenv import load_dotenv

load_dotenv()
db_password = os.getenv("DB_PASSWORD")

def load_jobs_to_db(jobs):
    with psycopg.connect(f"dbname=postgres user=postgres password={db_password} port=5433") as conn:
        with conn.cursor() as cur:
            for job in jobs:
                cur.execute(
                    "INSERT INTO job (title, company, url, location, source_id) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (source_id) DO NOTHING",
                    (job["title"], job["company"], job["url"], job["location"], job["url"])
                )


















