from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional

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







