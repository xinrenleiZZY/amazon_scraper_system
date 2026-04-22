#YU 421 V1.0
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models import User, UserKeyword

router = APIRouter()


class UserCreate(BaseModel):
    name: str


class KeywordAdd(BaseModel):
    keyword: str


@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    result = []
    for u in users:
        keywords = db.query(UserKeyword).filter(UserKeyword.user_id == u.id).all()
        result.append({
            "id": u.id,
            "name": u.name,
            "keywords": [k.keyword for k in keywords]
        })
    return result


@router.post("/users")
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    user = User(name=body.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "keywords": []}


@router.put("/users/{user_id}")
def update_user(user_id: int, body: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.name = body.name
    db.commit()
    return {"id": user.id, "name": user.name}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "已删除"}


@router.post("/users/{user_id}/keywords")
def add_keyword(user_id: int, body: KeywordAdd, db: Session = Depends(get_db)):
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="用户不存在")
    exists = db.query(UserKeyword).filter(
        UserKeyword.user_id == user_id, UserKeyword.keyword == body.keyword
    ).first()
    if not exists:
        db.add(UserKeyword(user_id=user_id, keyword=body.keyword))
        db.commit()
    keywords = db.query(UserKeyword).filter(UserKeyword.user_id == user_id).all()
    return [k.keyword for k in keywords]


@router.delete("/users/{user_id}/keywords")
def delete_keyword(user_id: int, keyword: str = Query(...), db: Session = Depends(get_db)):
    uk = db.query(UserKeyword).filter(
        UserKeyword.user_id == user_id, UserKeyword.keyword == keyword
    ).first()
    if not uk:
        raise HTTPException(status_code=404, detail="关键词不存在")
    db.delete(uk)
    db.commit()
    keywords = db.query(UserKeyword).filter(UserKeyword.user_id == user_id).all()
    return [k.keyword for k in keywords]
