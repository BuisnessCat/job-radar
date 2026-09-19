from fastapi import FastAPI, Query
from load import read_jobs_from_db
from load import read_job_from_db

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/jobs")
def get_jobs(offset: int = Query(ge=0, default=0), limit: int | None = Query(ge=1, default=20)):
    return read_jobs_from_db(offset, limit)

@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    return read_job_from_db(job_id)














