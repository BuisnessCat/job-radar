from pydantic import BaseModel, ConfigDict
from datetime import datetime

model_config = ConfigDict(from_attributes=True)

class JobOut(BaseModel):
    id: int
    title: str
    company: str
    url: str
    location: str
    created_at: datetime








