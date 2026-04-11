from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ------------------------------
# 用户相关 schemas
# ------------------------------
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


# ------------------------------
# 图片相关 schemas
# ------------------------------
class ImageCreate(BaseModel):
    user_id: int
    filename: str
    filepath: str
    filesize: int

class ImageOut(BaseModel):
    id: int
    user_id: int
    filename: str
    filepath: str
    filesize: int
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


# ------------------------------
# 任务相关 schemas
# ------------------------------
class TaskCreate(BaseModel):
    user_id: int
    image_id: int
    task_type: str

class TaskOut(BaseModel):
    id: int
    user_id: int
    image_id: int
    task_type: str
    status: str
    result_path: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True