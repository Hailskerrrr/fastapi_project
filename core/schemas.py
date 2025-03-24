from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, HttpUrl
from fastapi_users import schemas

class UserRead(schemas.BaseUser[int]):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass

class LinkBase(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkCreate(LinkBase):
    pass

class LinkUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    expires_at: Optional[datetime] = None

class LinkRead(LinkBase):
    id: int
    short_code: str
    created_at: datetime
    last_accessed_at: Optional[datetime]
    access_count: int
    is_active: bool
    is_expired: bool
    user_id: Optional[int]
    project_id: Optional[int]

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    user_id: int
    is_active: bool

    class Config:
        from_attributes = True 