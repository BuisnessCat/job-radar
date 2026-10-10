from ast import stmt
from db import Session
from sqlalchemy import select
from models import Job, Tag, JobTag
from sqlalchemy import func

ALLOWED_LOCATIONS = {"Praha", "Brno"}

def read_jobs_from_db(offset, limit, location, tag):
    with Session() as session:
        stmt = select(Job).offset(offset).limit(limit)
        
        if location is not None:
            stmt = stmt.where(Job.location == location.title())
            
        if tag is not None:
            stmt = (
                stmt.join(JobTag, Job.id == JobTag.job_id)
                .join(Tag, JobTag.tag_id == Tag.id)
                .where(Tag.name == tag.lower())
            )    
        return session.scalars(stmt).all()

def read_job_from_db(job_id):
    with Session() as session:
        stmt = select(Job).where(Job.id == job_id)
        job = session.scalars(stmt).one_or_none()
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

def load_tags_to_db(jobs):
    with Session.begin() as session:
        for job in jobs:
            db_job = session.scalars(select(Job).where(Job.source_id == job["url"])).one_or_none()
            
            if db_job is None:
                continue
            
            for tag_name in job["tags"]:
                stmt = select(Tag).where(Tag.name == tag_name)              
                tag = session.scalars(stmt).one_or_none()
                if tag is None:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                    session.flush()
                 
                if session.scalars(select(JobTag).where(JobTag.job_id == db_job.id, JobTag.tag_id == tag.id)).one_or_none() is None: 
                    session.add(JobTag(job_id=db_job.id, tag_id=tag.id))   
            
def count_tags():
    with Session() as session:
        job_count = func.count(JobTag.job_id)
        stmt = (
            select(Tag.name, job_count)
            .join(JobTag, JobTag.tag_id == Tag.id)
            .group_by(Tag.name)
            .order_by(job_count.desc(), Tag.name)
        )

        return [{"tag": row[0], "count": row[1]} for row in session.execute(stmt).all()
]















