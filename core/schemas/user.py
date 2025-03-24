from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    created_at: str
    password: int

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    


