from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Request, Body, Depends
from typing import List
import json
from pathlib import Path
import io
import logging
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import KeywordAttribute, User, UserKeyword

logger = logging.getLogger(__name__)

router = APIRouter()

# 配置文件路径（保留用于读取 keywords 列表）
CONFIG_PATH = Path(__file__).parent.parent / "scraper" / "scraper_config.json"


def load_config():
    """加载配置文件（仅用于获取关键词列表）"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"keywords": []}


def save_config(config):
    """保存配置文件（仅用于保存关键词列表）"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


# ========== 关键词 CRUD（保持原有路径参数格式，但改为数据库操作） ==========

@router.get("/keywords")
def get_keywords():
    """获取关键词列表（从 JSON 文件读取）"""
    config = load_config()
    return config.get("keywords", [])


@router.post("/keywords")
def add_keyword(keyword: str = Query(...), db: Session = Depends(get_db)):
    """添加关键词"""
    config = load_config()
    keywords = config.get("keywords", [])
    
    if keyword not in keywords:
        keywords.append(keyword)
        config["keywords"] = keywords
        save_config(config)
        
        # 同时在数据库创建空记录
        existing = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
        if not existing:
            db.add(KeywordAttribute(keyword=keyword))
            db.commit()
    
    return {"keywords": keywords}


@router.delete("/keywords")
def delete_keyword(keyword: str = Query(...), db: Session = Depends(get_db)):
    """删除关键词"""
    config = load_config()
    keywords = config.get("keywords", [])
    
    if keyword not in keywords:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    keywords.remove(keyword)
    config["keywords"] = keywords
    save_config(config)
    
    # 从数据库删除
    db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).delete()
    db.commit()
    
    return {"keywords": keywords}


@router.put("/keywords")
def update_keywords(keywords: List[str], db: Session = Depends(get_db)):
    """批量更新关键词"""
    config = load_config()
    config["keywords"] = keywords
    save_config(config)
    
    # 为新增的关键词创建数据库记录
    for kw in keywords:
        existing = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == kw).first()
        if not existing:
            db.add(KeywordAttribute(keyword=kw))
    db.commit()
    
    return {"keywords": keywords}


# ========== 标签接口（数据库版本） ==========

@router.get("/keywords/{keyword}/tags")
def get_keyword_tags(keyword: str, db: Session = Depends(get_db)):
    """获取关键词的标签"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    return attrs.tags if attrs else []


@router.put("/keywords/{keyword}/tags")
def update_keyword_tags(keyword: str, tags: List[str] = Body(...), db: Session = Depends(get_db)):
    """更新关键词的标签"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    if not attrs:
        attrs = KeywordAttribute(keyword=keyword)
        db.add(attrs)
    attrs.tags = tags
    db.commit()
    return tags


# ========== 节日接口（数据库版本） ==========

@router.get("/keywords/{keyword}/festival")
def get_keyword_festival(keyword: str, db: Session = Depends(get_db)):
    """获取关键词的节日"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    return attrs.festival if attrs else ""


@router.put("/keywords/{keyword}/festival")
def update_keyword_festival(keyword: str, festival: str = Body(...), db: Session = Depends(get_db)):
    """更新关键词的节日"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    if not attrs:
        attrs = KeywordAttribute(keyword=keyword)
        db.add(attrs)
    attrs.festival = festival
    db.commit()
    return festival


# ========== 大/小节日接口（数据库版本） ==========

@router.get("/keywords/{keyword}/festival-type")
def get_keyword_festival_type(keyword: str, db: Session = Depends(get_db)):
    """获取关键词的大/小节日"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    return attrs.festival_type if attrs else ""


@router.put("/keywords/{keyword}/festival-type")
def update_keyword_festival_type(keyword: str, festival_type: str = Body(...), db: Session = Depends(get_db)):
    """更新关键词的大/小节日"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    if not attrs:
        attrs = KeywordAttribute(keyword=keyword)
        db.add(attrs)
    attrs.festival_type = festival_type
    db.commit()
    return festival_type


# ========== 热卖期接口（数据库版本） ==========

@router.get("/keywords/{keyword}/hot-season")
def get_keyword_hot_season(keyword: str, db: Session = Depends(get_db)):
    """获取关键词的热卖期"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    return attrs.hot_season if attrs else ""


@router.put("/keywords/{keyword}/hot-season")
def update_keyword_hot_season(keyword: str, hot_season: str = Body(...), db: Session = Depends(get_db)):
    """更新关键词的热卖期"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    if not attrs:
        attrs = KeywordAttribute(keyword=keyword)
        db.add(attrs)
    attrs.hot_season = hot_season
    db.commit()
    return hot_season


# ========== 查询参数版本（兼容前端） ==========

@router.get("/keywords/tags")
def get_keyword_tags_query(keyword: str = Query(...), db: Session = Depends(get_db)):
    """获取关键词的标签（查询参数版本）"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    return attrs.tags if attrs else []


@router.put("/keywords/tags")
def update_keyword_tags_query(keyword: str = Query(...), tags: List[str] = Body(...), db: Session = Depends(get_db)):
    """更新关键词的标签（查询参数版本）"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    if not attrs:
        attrs = KeywordAttribute(keyword=keyword)
        db.add(attrs)
    attrs.tags = tags
    db.commit()
    return tags


@router.get("/keywords/festival")
def get_keyword_festival_query(keyword: str = Query(...), db: Session = Depends(get_db)):
    """获取关键词的节日（查询参数版本）"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    return attrs.festival if attrs else ""


@router.put("/keywords/festival")
def update_keyword_festival_query(keyword: str = Query(...), festival: str = Body(...), db: Session = Depends(get_db)):
    """更新关键词的节日（查询参数版本）"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    if not attrs:
        attrs = KeywordAttribute(keyword=keyword)
        db.add(attrs)
    attrs.festival = festival
    db.commit()
    return festival


@router.get("/keywords/festival-type")
def get_keyword_festival_type_query(keyword: str = Query(...), db: Session = Depends(get_db)):
    """获取关键词的大/小节日（查询参数版本）"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    return attrs.festival_type if attrs else ""


@router.put("/keywords/festival-type")
def update_keyword_festival_type_query(keyword: str = Query(...), festival_type: str = Body(...), db: Session = Depends(get_db)):
    """更新关键词的大/小节日（查询参数版本）"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    if not attrs:
        attrs = KeywordAttribute(keyword=keyword)
        db.add(attrs)
    attrs.festival_type = festival_type
    db.commit()
    return festival_type


@router.get("/keywords/hot-season")
def get_keyword_hot_season_query(keyword: str = Query(...), db: Session = Depends(get_db)):
    """获取关键词的热卖期（查询参数版本）"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    return attrs.hot_season if attrs else ""


@router.put("/keywords/hot-season")
def update_keyword_hot_season_query(keyword: str = Query(...), hot_season: str = Body(...), db: Session = Depends(get_db)):
    """更新关键词的热卖期（查询参数版本）"""
    attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
    if not attrs:
        attrs = KeywordAttribute(keyword=keyword)
        db.add(attrs)
    attrs.hot_season = hot_season
    db.commit()
    return hot_season


# ========== 批量导入接口（需要适配数据库） ==========

@router.post("/keywords/import-with-user")
async def import_keywords_with_user(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        import openpyxl
        from app.database import SessionLocal
        from app.models import User, UserKeyword
        content = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(content))
        ws = wb.active
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        invalid = [i+2 for i, r in enumerate(rows) if len(r) < 1 or not r[0]]
        if invalid:
            raise HTTPException(status_code=400, detail=f"格式错误：第 {invalid} 行缺少关键词，第一列必须填写关键词")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析失败: {e}")

    try:
        config = load_config()
        existing_kws = set(config.get("keywords", []))
        added_kws = 0
        added_relations = 0
        added_attrs = 0

        for row in rows:
            keyword = str(row[0]).strip() if row[0] else ""
            user_name = str(row[1]).strip() if len(row) > 1 and row[1] else ""
            tags_str = str(row[2]).strip() if len(row) > 2 and row[2] else ""
            festival = str(row[3]).strip() if len(row) > 3 and row[3] else ""
            festival_type = str(row[4]).strip() if len(row) > 4 and row[4] else ""
            hot_season = str(row[5]).strip() if len(row) > 5 and row[5] else ""
            
            if not keyword:
                continue
            
            # 添加到 JSON 配置文件
            if keyword not in existing_kws:
                existing_kws.add(keyword)
                added_kws += 1
            
            # 添加到数据库属性表
            attrs = db.query(KeywordAttribute).filter(KeywordAttribute.keyword == keyword).first()
            if not attrs:
                attrs = KeywordAttribute(keyword=keyword)
                db.add(attrs)
                added_attrs += 1
            
            if tags_str:
                tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                if tags:
                    attrs.tags = tags
            
            if festival:
                attrs.festival = festival
            
            if festival_type and festival_type in ['大节日', '小节日']:
                attrs.festival_type = festival_type
            
            if hot_season:
                attrs.hot_season = hot_season
            
            # 处理人员关联
            if user_name:
                users = [u.strip() for u in user_name.split(',') if u.strip()]
                for u_name in users:
                    user = db.query(User).filter(User.name == u_name).first()
                    if not user:
                        user = User(name=u_name)
                        db.add(user)
                        db.flush()
                    exists = db.query(UserKeyword).filter(
                        UserKeyword.user_id == user.id, 
                        UserKeyword.keyword == keyword
                    ).first()
                    if not exists:
                        db.add(UserKeyword(user_id=user.id, keyword=keyword))
                        added_relations += 1
        
        # 更新 JSON 配置文件
        config["keywords"] = list(existing_kws)
        save_config(config)
        
        db.commit()
        
        return {
            "imported_keywords": added_kws,
            "imported_relations": added_relations,
            "imported_attributes": added_attrs
        }
    except Exception as e:
        db.rollback()
        logger.error(f"导入失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")