from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class Job(Base):
    __tablename__ = "job"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]]
    company: Mapped[Optional[str]]
    url: Mapped[Optional[str]]
    location: Mapped[Optional[str]]
    source_id: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    
class Tag(Base):
    __tablename__ = "tag"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    
class JobTag(Base):
    __tablename__ = "job_tag"
    
    job_id: Mapped[int] = mapped_column(ForeignKey("job.id"),primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tag.id"),primary_key=True)







