# core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from typing import Optional
import os

# 从环境变量加载配置
SECRET_KEY = os.getenv("SECURITY_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 验证密钥是否加载成功
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

# 确保密钥是字符串格式
if not isinstance(SECRET_KEY, str):
    raise ValueError("SECRET_KEY must be a string")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """用 bcrypt 验证密码"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """用 bcrypt 生成密码哈希"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
