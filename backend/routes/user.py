from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from core.security import create_access_token, get_password_hash, verify_password
from database import get_db
from models.models import User
from schemas import UserCreate, UserOut, UserLogin

router = APIRouter()

# 注册
@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 新建用户（密码加密存储）
    new_user = User(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        created_at=datetime.now()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 登录
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()

    # 校验用户 + 密码（用 bcrypt 验证）
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(data={"sub": str(db_user.id)})

    return {
        "msg": "登录成功",
        "ACCESS_TOKEN": token,
        "user_id": db_user.id,
        "username": db_user.username
    }