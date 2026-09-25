import os
from dotenv import load_dotenv
from fastapi import HTTPException
from db import Session
from sqlalchemy import select
from models import Job

load_dotenv()
db_password = os.getenv("DB_PASSWORD")
DSN = f"dbname=postgres user=postgres password={db_password} port=5433"

ALLOWED_LOCATIONS = {"Praha", "Brno"}

def read_jobs_from_db(offset, limit, location):
    if location and location.title() not in ALLOWED_LOCATIONS:
        raise HTTPException(status_code=400, detail="Invalid location")

    with Session() as session:
        stmt = select(Job).offset(offset).limit(limit).where(Job.location == location.title()) 
        stmt = select(Job).offset(offset).limit(limit) if location is None else stmt
        return session.scalars(stmt).all()
    
    
def read_job_from_db(job_id):
    with Session() as session:
        stmt = select(Job).where(Job.id == job_id)
        job = session.scalars(stmt).one_or_none()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    
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


    

















