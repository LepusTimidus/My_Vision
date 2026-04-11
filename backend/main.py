from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text  # 已添加 text
from pydantic import BaseModel
import bcrypt

from database import get_db
from models import User, Image, Task

app = FastAPI(title="图片处理任务系统", version="1.0")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


# ------------------- 测试接口（已修复） -------------------
@app.get("/", tags=["测试"])
async def test_connection(db: AsyncSession = Depends(get_db)):
    try:
        # 修复：用 text() 包裹原生SQL
        await db.execute(text("SELECT 1"))
        await db.commit()
        return {
            "status": "✅ 连接成功",
            "message": "FastAPI + MySQL 已打通",
            "数据表": ["users", "images", "tasks"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库连接失败: {str(e)}"
        )


# ------------------- 用户接口 -------------------
@app.post("/user/register", tags=["用户"])
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == user.username)
    result = await db.execute(stmt)
    exist_user = result.scalar_one_or_none()

    if exist_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    hashed_pwd = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, password=hashed_pwd)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"message": "注册成功", "user_id": new_user.id, "username": new_user.username}


@app.post("/user/login", tags=["用户"])
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == user.username)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return {"message": "登录成功", "user_id": db_user.id}


@app.get("/user/{user_id}", tags=["用户"])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {"id": user.id, "username": user.username, "email": user.email, "created_at": user.created_at}


# ------------------- 图片接口 -------------------
@app.post("/image/upload", tags=["图片"])
async def upload_image(
        user_id: int,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="用户不存在")

    filename = file.filename
    filesize = len(await file.read())
    filepath = f"uploads/{filename}"

    new_image = Image(user_id=user_id, filename=filename, filepath=filepath, filesize=filesize)
    db.add(new_image)
    await db.commit()
    await db.refresh(new_image)

    return {"message": "图片上传成功", "image_id": new_image.id, "filename": filename}


# ------------------- 任务接口 -------------------
@app.post("/task/create", tags=["任务"])
async def create_task(
        user_id: int,
        image_id: int,
        task_type: str,
        db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == user_id)
    if not await db.execute(stmt).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="用户不存在")

    stmt = select(Image).where(Image.id == image_id)
    if not await db.execute(stmt).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="图片不存在")

    new_task = Task(user_id=user_id, image_id=image_id, task_type=task_type)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return {"message": "任务创建成功", "task_id": new_task.id, "status": new_task.status}


@app.get("/task/list/{user_id}", tags=["任务"])
async def get_user_tasks(user_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Task).where(Task.user_id == user_id)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return {"user_id": user_id, "tasks": tasks}