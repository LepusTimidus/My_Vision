from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session
from sqlalchemy import func


# ------------------------------
# 1. 用户表 users
# ------------------------------
class UserBase(SQLModel):
    username: str = Field(unique=True, max_length=50)
    email: str = Field(unique=True, max_length=100)

class User(UserBase, table=True):
    __tablename__ = "users"  # 对应你MySQL表名

    id: Optional[int] = Field(default=None, primary_key=True)
    password: str  # 加密密码
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now()}
    )

class UserPublic(UserBase):
    id: int
    created_at: Optional[datetime]


# ------------------------------
# 2. 图片表 images
# ------------------------------
class ImageBase(SQLModel):
    user_id: int
    filename: str = Field(max_length=255)
    filepath: str = Field(max_length=500)
    filesize: int

class Image(ImageBase, table=True):
    __tablename__ = "images"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now()}
    )

class ImagePublic(ImageBase):
    id: int
    created_at: Optional[datetime]


# ------------------------------
# 3. 任务表 tasks
# ------------------------------
class TaskBase(SQLModel):
    user_id: int
    image_id: int
    task_type: str = Field(max_length=20)
    status: Optional[str] = Field(default="pending", max_length=20)
    result_path: Optional[str] = Field(default=None, max_length=500)

class Task(TaskBase, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now()}
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )

class TaskPublic(TaskBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]