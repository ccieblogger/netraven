from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class JobResultBase(BaseModel):
    job_id: int
    device_id: int
    job_type: str
    status: str
    result_time: datetime
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

class JobResultRead(JobResultBase):
    id: int

    model_config = {"from_attributes": True}

class JobResultFilter(BaseModel):
    device_id: Optional[int] = None
    job_id: Optional[int] = None
    tag_id: Optional[int] = None
    job_type: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    size: int = 20

class JobResultWithNamesRead(JobResultRead):
    job_name: str
    device_name: str

class PaginatedJobResultResponse(BaseModel):
    items: List[JobResultWithNamesRead]
    total: int
    page: int
    size: int
    pages: int 