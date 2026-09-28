from fastapi import FastAPI, Query
from load import read_jobs_from_db
from load import read_job_from_db
from load import count_tags
from schemas import JobOut
from fastapi import HTTPException

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/jobs", response_model=list[JobOut])
def get_jobs(offset: int = Query(ge=0, default=0), 
             limit: int | None = Query(ge=1, default=20), 
             location: str | None = Query(default=None),
             tag: str | None = Query(default=None)):
    return read_jobs_from_db(offset, limit, location, tag)

@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int):
    job = read_job_from_db(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/stats/tags")
def get_tags():
    return count_tags()












