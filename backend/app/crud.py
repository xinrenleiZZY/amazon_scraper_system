from sqlalchemy.orm import Session
from app.models import RawSearchResult, ScrapingTask
from typing import Optional


def get_results(db: Session, keyword: Optional[str] = None, skip: int = 0, limit: int = 100):
    q = db.query(RawSearchResult)
    if keyword:
        q = q.filter(RawSearchResult.keyword == keyword)
    return q.offset(skip).limit(limit).all()


def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ScrapingTask).offset(skip).limit(limit).all()


def create_task(db: Session, keyword: str, pages: Optional[int] = None):
    task = ScrapingTask(keyword=keyword, pages=pages, status="pending")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
