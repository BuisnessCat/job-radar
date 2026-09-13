from fastapi import FastAPI
from load import read_jobs_from_db

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/jobs")
def get_jobs():
    return read_jobs_from_db()














