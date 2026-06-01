# routes/image.py
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models.models import Image, Task
from schemas import ImageCreate, ImageOut, TaskOut
from processor import UHDResProcessor

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


# 下载处理结果（根据任务 ID 返回结果图片）
@router.get("/download/{task_id}")
def download_result(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "completed" or not task.result_path:
        raise HTTPException(status_code=400, detail="任务尚未完成或无结果文件")

    if not os.path.isfile(task.result_path):
        raise HTTPException(status_code=404, detail="结果文件不存在")

    return FileResponse(
        task.result_path,
        media_type="image/png",
        filename=f"result_{task.id}.png"
    )


# 获取原图（根据图片 ID 返回原图）
@router.get("/source/{image_id}")
def get_source_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    input_path = image.filepath
    if not os.path.isabs(input_path):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        input_path = os.path.join(backend_dir, input_path)

    if not os.path.isfile(input_path):
        raise HTTPException(status_code=404, detail="原图文件不存在")

    return FileResponse(
        input_path,
        media_type="image/png",
        filename=image.filename
    )