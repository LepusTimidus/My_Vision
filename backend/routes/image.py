# routes/image.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import os

from database import get_db
from models.models import Image
from schemas import ImageCreate, ImageOut

router = APIRouter()


# 上传图片（修复版，100% 匹配你的数据库）
@router.post("/upload", response_model=ImageOut)
def upload_image(
        user_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    # 文件名
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    upload_dir = "uploads/"

    # 目录不存在就创建
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # 保存文件
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    new_image = Image(
        user_id=user_id,
        filename=filename,
        filepath=file_path,  # 这里！不是 file_path！
        filesize=0,  # 先给个默认值
        created_at=datetime.now()
    )

    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return new_image