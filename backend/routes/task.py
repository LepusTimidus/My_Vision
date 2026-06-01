import os
import threading
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models.models import Task, Image
from schemas import TaskCreate, TaskOut
from processor import UHDResProcessor

router = APIRouter()

# ── 后台处理函数（在独立线程运行，不阻塞 API）──
def _run_processing(task_id: int):
    """
    在新线程中执行 UHDRes 推理。
    用独立 DB Session，避免跨线程共享。
    """
    from database import SessionLocal as _SessionLocal

    db: Session = _SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        image = db.query(Image).filter(Image.id == task.image_id).first()
        if not image:
            task.status = "failed"
            task.updated_at = datetime.now()
            db.commit()
            return

        # 解析输入路径
        input_path = image.filepath
        if not os.path.isabs(input_path):
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            input_path = os.path.join(backend_dir, input_path)

        # 生成输出路径
        output_filename = f"result_{task.id}_{image.filename}"
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        results_dir = os.path.join(backend_dir, "results")
        output_path = os.path.join(results_dir, output_filename)
        os.makedirs(results_dir, exist_ok=True)

        # 标记为处理中
        task.status = "processing"
        task.updated_at = datetime.now()
        db.commit()

        # 执行 UHDRes 推理（真正的耗时操作）
        processor = UHDResProcessor()
        success, msg = processor.process(input_path, output_path, task.task_type)

        # 更新结果
        if success:
            task.status = "completed"
            task.result_path = output_path
        else:
            task.status = "failed"

        task.updated_at = datetime.now()
        db.commit()

        print(f"[任务 {task_id}] {msg}")

    except Exception as e:
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = "failed"
                task.updated_at = datetime.now()
                db.commit()
        except:
            pass
        print(f"[任务 {task_id}] 异常: {e}")
    finally:
        db.close()


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


# 提交处理（异步：立即返回，后台跑 UHDRes）
@router.post("/process/{task_id}")
def process_task(task_id: int, db: Session = Depends(get_db)):
    """
    异步处理任务：
    1. 检查任务是否存在
    2. 标记为 pending
    3. 后台线程执行 UHDRes 推理
    4. 立即返回（不等待推理完成）
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "processing":
        raise HTTPException(status_code=400, detail="任务正在处理中")

    # 重置状态
    task.status = "pending"
    task.result_path = None
    task.updated_at = datetime.now()
    db.commit()

    # 后台启动推理线程（不阻塞 API）
    thread = threading.Thread(target=_run_processing, args=(task_id,), daemon=True)
    thread.start()

    return {
        "task_id": task.id,
        "status": "pending",
        "message": "任务已提交，后台处理中...",
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


# 删除任务
@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(task)
    db.commit()
    return {"message": "任务删除成功"}