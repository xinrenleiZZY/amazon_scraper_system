# backend/app/api/keywords.py
from fastapi import APIRouter, HTTPException, Query
from typing import List
import json
from pathlib import Path

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