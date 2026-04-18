from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app import crud, schemas

router = APIRouter()


@router.get("/results", response_model=List[schemas.RawSearchResultOut])
def get_results(
    keyword: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud.get_results(db, keyword=keyword, skip=skip, limit=limit)


@router.get("/tasks", response_model=List[schemas.ScrapingTaskOut])
def get_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_tasks(db, skip=skip, limit=limit)