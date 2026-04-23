# backend/app/api/data.py
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import csv
import io

from app.database import get_db
from app import crud, schemas
from app.models import RawSearchResult, ScrapingTask

router = APIRouter()


@router.get("/results")
def get_results(
    keyword: Optional[str] = Query(None),
    keywords: Optional[List[str]] = Query(None),  # #YU 421
    asin: Optional[str] = Query(None),
    ad_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),  # #YU 421  le=100 -> 500
    db: Session = Depends(get_db)
):
    """查询爬取结果"""
    query = db.query(RawSearchResult)

    if keyword:
        query = query.filter(RawSearchResult.keyword == keyword)
    elif keywords:  # #YU 421
        query = query.filter(RawSearchResult.keyword.in_(keywords))  # #YU 421
    if asin:
        query = query.filter(RawSearchResult.asin == asin)
    if ad_type:
        query = query.filter(RawSearchResult.ad_type == ad_type)
    
    query = query.order_by(RawSearchResult.scraped_at.desc())
    
    total = query.count()
    total_pages = (total + limit - 1) // limit
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()
    
    data = []
    for item in items:
        data.append({
            'id': item.id,
            'keyword': item.keyword,
            'asin': item.asin,
            'title': item.title[:100] if item.title else '',
            'price_current': item.price_current,
            'price_list': item.price_list,
            'rating_stars': float(item.rating_stars) if item.rating_stars else None,
            'rating_count': item.rating_count,
            'ad_type': item.ad_type,
            'ad_rank': item.ad_rank,
            'organic_rank': item.organic_rank,
            'page': item.page,
            'scraped_at': item.scraped_at.isoformat() if item.scraped_at else None,
            'date': item.scraped_at.strftime('%Y-%m-%d') if item.scraped_at else None
        })
    
    return {
        'data': data,
        'total': total,
        'page': page,
        'limit': limit,
        'total_pages': total_pages
    }


@router.get("/tasks")
def get_tasks(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),  # #YU 421  le=100 -> 500
    db: Session = Depends(get_db)
):
    """查询任务列表"""
    query = db.query(ScrapingTask)
    
    if status:
        query = query.filter(ScrapingTask.status == status)
    if keyword:
        query = query.filter(ScrapingTask.keyword.contains(keyword))
    
    query = query.order_by(ScrapingTask.id.desc())
    
    total = query.count()
    total_pages = (total + limit - 1) // limit
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()
    
    data = []
    for item in items:
        data.append({
            'id': item.id,
            'keyword': item.keyword,
            'status': item.status,
            'total_items': item.total_items,
            'started_at': item.started_at.isoformat() if item.started_at else None,
            'completed_at': item.completed_at.isoformat() if item.completed_at else None,
            'error_message': item.error_message
        })
    
    return {
        'data': data,
        'total': total,
        'page': page,
        'limit': limit,
        'total_pages': total_pages
    }


@router.get("/tasks/{task_id}")
def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情"""
    task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        'id': task.id,
        'keyword': task.keyword,
        'status': task.status,
        'total_items': task.total_items,
        'started_at': task.started_at.isoformat() if task.started_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'error_message': task.error_message
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取统计数据"""
    import json
    from pathlib import Path
    
    # 总关键词数
    config_path = Path(__file__).parent.parent / "scraper" / "scraper_config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            total_keywords = len(config.get('keywords', []))
    except:
        total_keywords = 0
    
    total_tasks = db.query(ScrapingTask).count()
    total_products = db.query(RawSearchResult).count()
    
    today = datetime.now().date()
    today_count = db.query(RawSearchResult).filter(
        RawSearchResult.scraped_at >= today
    ).count()
    
    return {
        'total_keywords': total_keywords,
        'total_tasks': total_tasks,
        'total_products': total_products,
        'today_count': today_count
    }


@router.get("/asins")
def get_asins(keyword: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """获取所有不重复的 ASIN 列表"""
    query = db.query(RawSearchResult.asin).filter(RawSearchResult.asin != None)
    if keyword:
        query = query.filter(RawSearchResult.keyword == keyword)
    asins = [row[0] for row in query.distinct().order_by(RawSearchResult.asin).all()]
    return asins


@router.get("/results/export")
def export_results(
    keyword: Optional[str] = Query(None),
    asin: Optional[str] = Query(None),
    ad_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """导出查询结果为 CSV"""
    query = db.query(RawSearchResult)
    if keyword:
        query = query.filter(RawSearchResult.keyword == keyword)
    if asin:
        query = query.filter(RawSearchResult.asin == asin)
    if ad_type:
        query = query.filter(RawSearchResult.ad_type == ad_type)
    items = query.order_by(RawSearchResult.scraped_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['date','keyword','asin','title','price_current','rating_stars','rating_count','ad_type','ad_rank','organic_rank','page','scraped_at'])
    for item in items:
        writer.writerow([
            item.scraped_at.strftime('%Y-%m-%d') if item.scraped_at else '',
            item.keyword, item.asin, item.title,
            item.price_current, item.rating_stars, item.rating_count,
            item.ad_type, item.ad_rank, item.organic_rank, item.page,
            item.scraped_at.isoformat() if item.scraped_at else ''
        ])

    output.seek(0)
    return StreamingResponse(
        iter(['\ufeff' + output.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="results.csv"'}
    )

