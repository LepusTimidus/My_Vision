# core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from database import get_db
from models.models import User
from core.security import SECRET_KEY, ALGORITHM

load_dotenv()

# 告诉 FastAPI 从哪里获取 token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")

# 依赖：获取当前登录用户（所有需要登录的接口都用它）
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效凭证，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解密 token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # 从数据库查用户
    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise credentials_exception

    return user