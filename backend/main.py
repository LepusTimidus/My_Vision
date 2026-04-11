from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
#以上是import必要库

from database import get_db,engine
#导入数据库
app = FastAPI(Title = "Vision Web后端", version = "1.0")
#创建应用实例

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#配置跨域

@app.get("/")
def read_root():
    return{"message": "成功运行"}
#根接口

@app.get("/test-db")
def test_db(db:Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return{"status": "success", "msg": "连接正常"}
    except Exception as e:
        return{"status": "fail", "msg": str(e)}