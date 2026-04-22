# backend/app/api/keywords.py
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List
import json
from pathlib import Path
import io

router = APIRouter()

# 配置文件路径
CONFIG_PATH = Path(__file__).parent.parent / "scraper" / "scraper_config.json"


def load_config():
    """加载配置文件"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"keywords": []}


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


@router.get("/keywords")
def get_keywords():
    """获取关键词列表"""
    config = load_config()
    # return {"keywords": config.get("keywords", [])}
    return config.get("keywords", [])


@router.post("/keywords")
def add_keyword(keyword: str = Query(..., description="要添加的关键词")):
    """添加关键词"""
    config = load_config()
    keywords = config.get("keywords", [])
    
    if keyword not in keywords:
        keywords.append(keyword)
        config["keywords"] = keywords
        save_config(config)
    
    return {"keywords": keywords}


@router.delete("/keywords")
def delete_keyword(keyword: str = Query(..., description="要删除的关键词")):
    """删除关键词"""
    config = load_config()
    keywords = config.get("keywords", [])
    
    if keyword not in keywords:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    keywords.remove(keyword)
    config["keywords"] = keywords
    save_config(config)
    
    return {"keywords": keywords}


@router.put("/keywords")
def update_keywords(keywords: List[str]):
    """批量更新关键词"""
    config = load_config()
    config["keywords"] = keywords
    save_config(config)
    
    return {"keywords": keywords}

# #YU 421 标签接口
@router.get("/keywords/{keyword}/tags")
def get_keyword_tags(keyword: str):
    config = load_config()
    return config.get("keyword_tags", {}).get(keyword, [])

# #YU 421 
@router.put("/keywords/{keyword}/tags")
def update_keyword_tags(keyword: str, tags: List[str]):
    config = load_config()
    if "keyword_tags" not in config:
        config["keyword_tags"] = {}
    config["keyword_tags"][keyword] = tags
    save_config(config)
    return tags


# #YU 421 按人员批量导入关键词（Excel: 第一列人员姓名，第二列关键词）
@router.post("/keywords/import-with-user")
async def import_keywords_with_user(file: UploadFile = File(...)):
    try:
        import openpyxl
        from app.database import SessionLocal
        from app.models import User, UserKeyword
        content = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(content))
        ws = wb.active
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        # #YU 422 验证格式：每行第一列（关键词）必须有值，第二列（人员姓名）可以为空
        invalid = [i+2 for i, r in enumerate(rows) if len(r) < 1 or not r[0]]
        if invalid:
            raise HTTPException(status_code=400, detail=f"格式错误：第 {invalid} 行缺少关键词，第一列必须填写关键词")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析失败: {e}")

    db = SessionLocal()
    try:
        config = load_config()
        existing_kws = set(config.get("keywords", []))
        added_kws, added_relations = 0, 0
        for keyword, user_name in rows:  # #YU 421 第一列关键词，第二列人员
            # #YU 422 处理可能的 None 值
            keyword = str(keyword).strip() if keyword else ""
            user_name = str(user_name).strip() if user_name else ""
            
            # #YU 422 关键词不能为空，跳过空行
            if not keyword:
                continue
                
            # 关键词加入全局列表
            if keyword not in existing_kws:
                existing_kws.add(keyword)
                added_kws += 1
            
            # #YU 422 只有当人员姓名不为空时，才创建用户关联
            if user_name:
                # 找或创建用户
                user = db.query(User).filter(User.name == user_name).first()
                if not user:
                    user = User(name=user_name)
                    db.add(user)
                    db.flush()
                # 建立关联
                exists = db.query(UserKeyword).filter(UserKeyword.user_id == user.id, UserKeyword.keyword == keyword).first()
                if not exists:
                    db.add(UserKeyword(user_id=user.id, keyword=keyword))
                    added_relations += 1
        config["keywords"] = list(existing_kws)
        save_config(config)
        db.commit()
    finally:
        db.close()
    return {"imported_keywords": added_kws, "imported_relations": added_relations}


# #YU 422 纯关键词导入接口（Excel: 第一列为关键词）
@router.post("/keywords/import")
async def import_keywords(file: UploadFile = File(...)):
    try:
        import openpyxl
        content = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(content))
        ws = wb.active
        new_kws = [str(row[0].value).strip() for row in ws.iter_rows(min_row=2) if row[0].value]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析失败: {e}")

    config = load_config()
    existing = config.get("keywords", [])
    added = [kw for kw in new_kws if kw and kw not in existing]
    config["keywords"] = existing + added
    save_config(config)
    return {"imported": len(added), "total": len(config["keywords"])}
