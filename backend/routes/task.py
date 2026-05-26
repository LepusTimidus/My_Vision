import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models.models import Task, Image
from schemas import TaskCreate, TaskOut
from processor import UHDResProcessor

router = APIRouter()

# 创建任务
@router.post("/task", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(
        user_id=task.user_id,
        image_id=task.image_id,
        task_type=task.task_type,
        status="pending",
        result_path=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


# 执行处理（核心：调用 UHDRes 模型）
@router.post("/process/{task_id}")
def process_task(task_id: int, db: Session = Depends(get_db)):
    """
    对指定任务执行图像处理：
    1. 查找任务 + 关联图片
    2. 调 UHDRes 模型推理
    3. 保存结果 + 更新任务状态
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    image = db.query(Image).filter(Image.id == task.image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="关联图片不存在")

    # 标记为处理中
    task.status = "processing"
    task.updated_at = datetime.now()
    db.commit()

    # 解析路径：image.filepath 是相对路径（如 "uploads/xxx.jpg"）
    input_path = image.filepath
    if not os.path.isabs(input_path):
        # 相对于 backend 目录
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        input_path = os.path.join(backend_dir, input_path)

    # 输出路径
    output_filename = f"result_{task.id}_{image.filename}"
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(backend_dir, "results")
    output_path = os.path.join(results_dir, output_filename)
    os.makedirs(results_dir, exist_ok=True)

    # 执行 UHDRes 推理
    processor = UHDResProcessor()
    success, msg = processor.process(input_path, output_path, task.task_type)

    # 更新任务状态
    if success:
        task.status = "completed"
        task.result_path = output_path
    else:
        task.status = "failed"

    task.updated_at = datetime.now()
    db.commit()
    db.refresh(task)

    return {
        "task_id": task.id,
        "status": task.status,
        "result_path": task.result_path if success else None,
        "message": msg,
    }


# 获取某个用户的所有任务
@router.get("/tasks/{user_id}", response_model=list[TaskOut])
def get_tasks_by_user(user_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return tasks


# 获取单个任务详情
@router.get("/{task_id}", response_model=TaskOut)
def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


# 更新任务状态（处理中/成功/失败）
@router.patch("/{task_id}", response_model=TaskOut)
def update_task_status(
    task_id: int,
    status: str,
    result_path: str = None,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.status = status
    if result_path:
        task.result_path = result_path
    task.updated_at = datetime.now()

    db.commit()
    db.refresh(task)
    return task


# 删除任务
@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(task)
    db.commit()
    return {"message": "任务删除成功"}