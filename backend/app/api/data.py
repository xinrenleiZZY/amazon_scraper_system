# backend/app/api/data.py
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, Query as SQLAlchemyQuery
from typing import Optional, List, Tuple, Set
from datetime import datetime
from datetime import timedelta
import csv
import io
import json
from pathlib import Path
import logging
from app.database import get_db
from app.models import RawSearchResult, ScrapingTask, KeywordAttribute, UserKeyword, User

logger = logging.getLogger(__name__)
router = APIRouter()

# 配置文件路径
CONFIG_PATH = Path(__file__).parent.parent / "scraper" / "scraper_config.json"


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"keywords": []}


def get_keyword_attributes(db: Session):
    """从数据库获取所有关键词的属性"""
    attrs = db.query(KeywordAttribute).all()
    return {
        "keyword_tags": {a.keyword: a.tags or [] for a in attrs},
        "keyword_festivals": {a.keyword: a.festival or '' for a in attrs},
        "keyword_festival_types": {a.keyword: a.festival_type or '' for a in attrs},
        "keyword_hot_seasons": {a.keyword: a.hot_season or '' for a in attrs},
    }


def get_keyword_owners(db: Session) -> dict:
    """获取关键词-负责人映射（一次性查询，避免 N+1）"""
    # 使用 join 一次性获取所有关联
    results = db.query(UserKeyword.keyword, User.name).join(
        User, User.id == UserKeyword.user_id
    ).all()
    
    keyword_owners = {}
    for keyword, name in results:
        if keyword not in keyword_owners:
            keyword_owners[keyword] = []
        keyword_owners[keyword].append(name)
    return keyword_owners


def apply_keyword_filters(
    query: SQLAlchemyQuery,
    keyword: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    festival: Optional[str] = None,
    festival_type: Optional[str] = None,
    hot_season: Optional[str] = None,
    asin: Optional[str] = None,
    ad_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Tuple[SQLAlchemyQuery, Set[str]]:
    """
    统一应用所有筛选条件
    返回: (筛选后的 query, 匹配的关键词集合)
    """
    # 获取关键词属性（用于标签/节日筛选）
    db = query.session
    attrs = get_keyword_attributes(db)
    keyword_tags = attrs["keyword_tags"]
    keyword_festivals = attrs["keyword_festivals"]
    keyword_festival_types = attrs["keyword_festival_types"]
    keyword_hot_seasons = attrs["keyword_hot_seasons"]
    
    matched_keywords = None
    
    # 1. 关键词筛选
    if keyword:
        query = query.filter(RawSearchResult.keyword == keyword)
    elif keywords:
        query = query.filter(RawSearchResult.keyword.in_(keywords))
    
    # 2. 标签筛选（需要先计算匹配的关键词）
    if tags:
        matched_keywords = set()
        for kw, kw_tags in keyword_tags.items():
            if any(tag in kw_tags for tag in tags):
                matched_keywords.add(kw)
        if matched_keywords:
            query = query.filter(RawSearchResult.keyword.in_(matched_keywords))
        else:
            # 没有匹配的关键词，返回空结果
            return query.filter(False), set()
    
    # 3. 节日筛选
    if festival:
        kw_list = [kw for kw, f in keyword_festivals.items() if f == festival]
        if kw_list:
            query = query.filter(RawSearchResult.keyword.in_(kw_list))
        else:
            return query.filter(False), set()
    
    # 4. 节日类型筛选
    if festival_type:
        kw_list = [kw for kw, ft in keyword_festival_types.items() if ft == festival_type]
        if kw_list:
            query = query.filter(RawSearchResult.keyword.in_(kw_list))
        else:
            return query.filter(False), set()
    
    # 5. 热卖期筛选
    if hot_season:
        kw_list = [kw for kw, hs in keyword_hot_seasons.items() if hs == hot_season]
        if kw_list:
            query = query.filter(RawSearchResult.keyword.in_(kw_list))
        else:
            return query.filter(False), set()
    
    # 6. 其他直接筛选
    if asin:
        logger.info(f"ASIN 筛选: {asin}")
        query = query.filter(RawSearchResult.asin.ilike(f'%{asin}%'))
        logger.info(f"SQL: {query}")
    if ad_type:
        query = query.filter(RawSearchResult.ad_type == ad_type)
    if date_from:
        from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        query = query.filter(RawSearchResult.date >= from_date)
    if date_to:
        to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
        query = query.filter(RawSearchResult.date <= to_date)
    
    return query, matched_keywords or set()


def collect_available_options(
    db: Session,
    keyword: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    festival: Optional[str] = None,
    festival_type: Optional[str] = None,
    hot_season: Optional[str] = None,
    asin: Optional[str] = None,
    ad_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    """
    收集所有符合条件的剩余选项（基于全量数据，不分页）
    返回: {available_tags, available_festivals, ...}
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 1. 先获取所有匹配的关键词
    keyword_query = db.query(RawSearchResult.keyword).distinct()
    keyword_query, _ = apply_keyword_filters(
        keyword_query, keyword, keywords, tags, festival,
        festival_type, hot_season, asin, ad_type, date_from, date_to
    )
    
    all_keywords = [row[0] for row in keyword_query.all()]
    logger.info(f"收集剩余选项: 找到 {len(all_keywords)} 个匹配的关键词")
    
    if not all_keywords:
        return {
            'available_tags': [],
            'available_festivals': [],
            'available_festival_types': [],
            'available_hot_seasons': [],
        }
    
    # 2. 从关键词属性中收集选项
    attrs = get_keyword_attributes(db)
    keyword_tags = attrs["keyword_tags"]
    keyword_festivals = attrs["keyword_festivals"]
    keyword_festival_types = attrs["keyword_festival_types"]
    keyword_hot_seasons = attrs["keyword_hot_seasons"]
    
    available_tags = set()
    available_festivals = set()
    available_festival_types = set()
    available_hot_seasons = set()
    
    for kw in all_keywords:
        for tag in keyword_tags.get(kw, []):
            available_tags.add(tag)
        if keyword_festivals.get(kw):
            available_festivals.add(keyword_festivals.get(kw))
        if keyword_festival_types.get(kw):
            available_festival_types.add(keyword_festival_types.get(kw))
        if keyword_hot_seasons.get(kw):
            available_hot_seasons.add(keyword_hot_seasons.get(kw))
    
    return {
        'available_tags': sorted(list(available_tags)),
        'available_festivals': sorted(list(available_festivals)),
        'available_festival_types': sorted(list(available_festival_types)),
        'available_hot_seasons': sorted(list(available_hot_seasons)),
    }


@router.get("/results")
def get_results(
    keyword: Optional[str] = Query(None),
    keywords: Optional[List[str]] = Query(None),
    asin: Optional[str] = Query(None),
    ad_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    tags: Optional[List[str]] = Query(None),
    festival: Optional[str] = Query(None),
    festival_type: Optional[str] = Query(None),
    hot_season: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),  # 人员筛选
    db: Session = Depends(get_db)
):
    """查询爬取结果 - 重构版"""
    
    # 1. 获取关键词属性
    attrs = get_keyword_attributes(db)
    keyword_tags = attrs["keyword_tags"]
    keyword_festivals = attrs["keyword_festivals"]
    keyword_festival_types = attrs["keyword_festival_types"]
    keyword_hot_seasons = attrs["keyword_hot_seasons"]
    
    # 2. 获取关键词-负责人映射
    keyword_owners = get_keyword_owners(db)
    
    # 3. 构建主查询
    query = db.query(RawSearchResult)
    
    # 4. 应用筛选条件（复用公共函数）
    query, _ = apply_keyword_filters(
        query, keyword, keywords, tags, festival,
        festival_type, hot_season, asin, ad_type, date_from, date_to
    )
    
    # 5. 人员筛选（通过 user_id 过滤关键词）
    if user_id:
        user_keywords = db.query(UserKeyword.keyword).filter(UserKeyword.user_id == user_id).all()
        user_keyword_list = [uk[0] for uk in user_keywords]
        if user_keyword_list:
            query = query.filter(RawSearchResult.keyword.in_(user_keyword_list))
        else:
            return {
                'data': [], 'total': 0, 'page': page, 'limit': limit, 'total_pages': 0,
                'available_tags': [], 'available_festivals': [], 
                'available_festival_types': [], 'available_hot_seasons': []
            }
    # # 6. ASIN 特殊处理：支持多个 ASIN 逗号分隔
    # if asin and ',' in asin:
    #     asin_list = [a.strip() for a in asin.split(',')]
    #     query = query.filter(RawSearchResult.asin.in_(asin_list))

    # 7. 收集剩余选项（基于全量数据）
    available_options = collect_available_options(
        db, keyword, keywords, tags, festival, festival_type,
        hot_season, asin, ad_type, date_from, date_to
    )
    
    # 7. 分页（此时 query 已经包含所有筛选条件）
    total = query.count()
    total_pages = (total + limit - 1) // limit
    offset = (page - 1) * limit
    items = query.order_by(RawSearchResult.scraped_at.desc()).offset(offset).limit(limit).all()

    # 8. 构建返回数据
    data = []
    for item in items:
        kw = item.keyword
        data.append({
            'id': item.id,
            'keyword': kw,
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
            'data_index': item.data_index,
            'index_position': item.index_position,
            'scraped_at': item.scraped_at.isoformat() if item.scraped_at else None,
            'date': item.scraped_at.strftime('%Y-%m-%d') if item.scraped_at else None,
            'tags': keyword_tags.get(kw, []),
            'festival': keyword_festivals.get(kw, ''),
            'festival_type': keyword_festival_types.get(kw, ''),
            'hot_season': keyword_hot_seasons.get(kw, ''),
            'owner': keyword_owners.get(kw, []),
        })
    
    return {
        'data': data,
        'total': total,
        'page': page,
        'limit': limit,
        'total_pages': total_pages,
        **available_options,  # 展开 available_tags, available_festivals 等
    }


# 其他接口（tasks, stats, asins, export）保持不变
# ... 其余代码（tasks, stats, asins, export 等）保持不变 ...
@router.get("/tasks")
def get_tasks(
    task_id: Optional[int] = Query(None),  # 新增
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """查询任务列表"""
    query = db.query(ScrapingTask)
    if task_id:
        query = query.filter(RawSearchResult.task_id == task_id)
    elif keyword:
        query = query.filter(RawSearchResult.keyword == keyword)
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
    # 总关键词数
    try:
        config = load_config()
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
    tags: Optional[List[str]] = Query(None),
    festival: Optional[str] = Query(None),
    festival_type: Optional[str] = Query(None),
    hot_season: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """导出查询结果为 CSV"""
    query = db.query(RawSearchResult)
    
    # 加载关键词属性用于筛选
    attrs = get_keyword_attributes(db)
    keyword_tags = attrs["keyword_tags"]
    keyword_festivals = attrs["keyword_festivals"]
    keyword_festival_types = attrs["keyword_festival_types"]
    keyword_hot_seasons = attrs["keyword_hot_seasons"]
    
    if keyword:
        query = query.filter(RawSearchResult.keyword == keyword)
    
    # 标签筛选
    if tags:
        matched_keywords = set()
        for kw, kw_tags in keyword_tags.items():
            if any(tag in kw_tags for tag in tags):
                matched_keywords.add(kw)
        if matched_keywords:
            query = query.filter(RawSearchResult.keyword.in_(matched_keywords))
        else:
            return StreamingResponse(iter(['']), media_type='text/csv')
    
    # 节日筛选
    if festival:
        matched_keywords = [kw for kw, f in keyword_festivals.items() if f == festival]
        if matched_keywords:
            query = query.filter(RawSearchResult.keyword.in_(matched_keywords))
        else:
            return StreamingResponse(iter(['']), media_type='text/csv')
    
    if festival_type:
        matched_keywords = [kw for kw, ft in keyword_festival_types.items() if ft == festival_type]
        if matched_keywords:
            query = query.filter(RawSearchResult.keyword.in_(matched_keywords))
        else:
            return StreamingResponse(iter(['']), media_type='text/csv')
    
    if hot_season:
        matched_keywords = [kw for kw, hs in keyword_hot_seasons.items() if hs == hot_season]
        if matched_keywords:
            query = query.filter(RawSearchResult.keyword.in_(matched_keywords))
        else:
            return StreamingResponse(iter(['']), media_type='text/csv')
    
    if asin:
        query = query.filter(RawSearchResult.asin.ilike(f'%{asin}%'))
        
    if ad_type:
        query = query.filter(RawSearchResult.ad_type == ad_type)
    
    items = query.order_by(RawSearchResult.scraped_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['date', 'keyword', 'asin', 'title', 'price_current', 'rating_stars', 'rating_count', 'ad_type', 'ad_rank', 'organic_rank', 'page', 'scraped_at'])
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

# 可视化大屏接口
@router.get("/results/asin-analysis")
def get_asin_analysis(
    asin: str = Query(..., description="ASIN代码"),
    days: int = Query(30, description="天数范围"),
    keywords: Optional[List[str]] = Query(None, description="关键词筛选"),
    db: Session = Depends(get_db)
):
    """获取ASIN的分析数据：排名趋势、价格变化"""
    
    # 计算开始日期
    start_date = datetime.now().date() - timedelta(days=days)
    
    # 构建查询
    query = db.query(RawSearchResult).filter(
        RawSearchResult.asin.ilike(f'%{asin}%'),
        RawSearchResult.date >= start_date
    )
    
    # 关键词筛选
    if keywords and len(keywords) > 0:
        query = query.filter(RawSearchResult.keyword.in_(keywords))
    
    # 按时间排序
    records = query.order_by(RawSearchResult.scraped_at.asc()).all()
    
    # 构建返回数据
    data = []
    for r in records:
        data.append({
            'scraped_at': r.scraped_at.isoformat(),
            'keyword': r.keyword,
            'organic_rank': r.organic_rank,
            'ad_rank': r.ad_rank,
            'ad_type': r.ad_type,
            'price_current': r.price_current,
            'rating_stars': float(r.rating_stars) if r.rating_stars else None,
            'rating_count': r.rating_count
        })
    
    return {
        'asin': asin,
        'days': days,
        'total_records': len(data),
        'records': data
    }