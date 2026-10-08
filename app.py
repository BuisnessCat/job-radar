from fastapi import FastAPI, Query
from load import read_jobs_from_db
from load import read_job_from_db
from load import count_tags
from schemas import JobOut
from fastapi import HTTPException

app = FastAPI(
    title="job-radar",
    description="Junior IT jobs scraped from [junior.guru](https://junior.guru/jobs/praha/) "
                "and served from Postgres. Run `python main.py` first to fill the database.",
)

@app.get("/health",
         description="Checks that the server is up. Always returns `{\"status\": \"ok\"}`, "
                     "doesn't touch the database.")
def health_check():
    return {"status": "ok"}

@app.get("/jobs", response_model=list[JobOut],
         description="Jobs from the database, 20 at a time by default. Page through them with "
                     "`offset` and `limit`. `location` and `tag` filters can be combined.")
def get_jobs(offset: int = Query(ge=0, default=0,
                                 description="How many jobs to skip."),
             limit: int | None = Query(ge=1, default=20,
                                       description="How many jobs to return at most."),
             location: str | None = Query(default=None,
                                          description="City, case-insensitive: `praha`, `Brno`. "
                                                      "Has to match the whole location, so `Brno` "
                                                      "won't find `Brno, Prostějov (Olomouc)`."),
             tag: str | None = Query(default=None,
                                     description="Tag, case-insensitive: `python`, `react`. "
                                                 "`/stats/tags` lists all of them.")):
    return read_jobs_from_db(offset, limit, location, tag)

@app.get("/jobs/{job_id}", response_model=JobOut,
         description="One job by its id. 404 if there's no job with that id.")
def get_job(job_id: int):
    job = read_job_from_db(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/stats/tags",
         description="Every tag with the number of jobs that have it, in no particular order.")
def get_tags():
    return count_tags()
