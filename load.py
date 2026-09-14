import psycopg
import os
from dotenv import load_dotenv
from psycopg.rows import dict_row
from db import Session
from sqlalchemy import select
from models import Job

load_dotenv()
db_password = os.getenv("DB_PASSWORD")
DSN = f"dbname=postgres user=postgres password={db_password} port=5433"

def read_jobs_from_db():
    with psycopg.connect(DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT title, company, url, location FROM job")
            return cur.fetchall()

def load_jobs_to_db(jobs):
    with Session.begin() as session:
        for job in jobs:
            stmt = select(Job).where(Job.source_id == job["url"])
            if session.scalars(stmt).one_or_none() is None:
                session.add(Job(title=job["title"], 
                                company=job["company"], 
                                url=job["url"], 
                                location=job["location"], 
                                source_id=job["url"]))


    

















