"""
测试人员管理接口 - 使用内存数据，不连接数据库
运行: uvicorn test_users_api:app --reload --port 8001
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Users API Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存数据
users_db = [
    {"id": 1, "name": "张三", "email": "zhangsan@example.com", "keywords": ["pool party decorations", "summer decor"]},
    {"id": 2, "name": "李四", "email": "lisi@example.com", "keywords": ["beach towels", "inflatable pool"]},
    {"id": 3, "name": "王五", "email": None, "keywords": ["pool floats"]},
]
next_id = 4


class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None


class KeywordAdd(BaseModel):
    keyword: str


@app.get("/api/users")
def get_users():
    return users_db


@app.post("/api/users")
def create_user(body: UserCreate):
    global next_id
    user = {"id": next_id, "name": body.name, "email": body.email, "keywords": []}
    users_db.append(user)
    next_id += 1
    return user


@app.put("/api/users/{user_id}")
def update_user(user_id: int, body: UserCreate):
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user["name"] = body.name
    user["email"] = body.email
    return user


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    global users_db
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    users_db = [u for u in users_db if u["id"] != user_id]
    return {"message": "已删除"}


@app.post("/api/users/{user_id}/keywords")
def add_keyword(user_id: int, body: KeywordAdd):
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.keyword not in user["keywords"]:
        user["keywords"].append(body.keyword)
    return user["keywords"]


@app.delete("/api/users/{user_id}/keywords")
def delete_keyword(user_id: int, keyword: str = Query(...)):
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if keyword not in user["keywords"]:
        raise HTTPException(status_code=404, detail="关键词不存在")
    user["keywords"].remove(keyword)
    return user["keywords"]


@app.get("/health")
def health():
    return {"status": "healthy"}
