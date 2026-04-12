from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models.models import Task
from schemas import TaskCreate, TaskOut

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
        created_at=datetime.now(),  # 给时间
        updated_at=datetime.now()   # 给时间
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

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