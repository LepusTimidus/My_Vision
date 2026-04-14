from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from fastapi import Depends
from dotenv import load_dotenv
from database import get_db, engine
from core import security

from routes import user  # 导入用户路由
from routes import task  #导入任务路由
from routes import image  #导入图片路由

app = FastAPI(title="Vision Web 后端")

#感觉要火在这里加个加载环境变量
load_dotenv()

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(user.router, prefix="/api/user")

app.include_router(task.router, prefix="/api/tasks")

app.include_router(image.router, prefix="/api/images")


# 测试首页
@app.get("/")
def root():
    return {"message": "后端运行成功"}


# 测试数据库
@app.get("/test-db")
def test_db(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "success"}
    except:
        return {"status": "fail"}


@app.on_event("startup")
def startup_event():
    print("应用启动完成")
