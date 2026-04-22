# backend/app/api/logs.py
from fastapi import APIRouter
from pathlib import Path

router = APIRouter()
LOG_PATH = Path(__file__).parent.parent / "scraper" / "amazon_scraper.log"

@router.get("/logs")
def get_logs(lines: int = 100):
    """获取最近的日志"""
    if not LOG_PATH.exists():
        return {"logs": [], "message": "日志文件不存在"}
    
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
    
    return {"logs": recent, "total": len(all_lines)}