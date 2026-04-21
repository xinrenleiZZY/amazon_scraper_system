# backend/app/api/scraping.py
from fastapi import APIRouter, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from typing import Optional
import asyncio
import logging

router = APIRouter()

# 存储 WebSocket 连接
active_connections = []

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_log(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # 保持连接
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/scrape")
def start_scraping(
    background_tasks: BackgroundTasks,
    keyword: Optional[str] = Query(None),
    pages: Optional[int] = Query(None)
):
    """启动爬取任务"""
    from app.scraper.pipeline import run_now
    
    background_tasks.add_task(run_now, keyword, pages)
    
    return {
        "message": "任务已启动",
        "keyword": keyword or "所有关键词",
        "pages": pages or "自动"
    }


@router.post("/scrape/daily")
def trigger_daily(background_tasks: BackgroundTasks):
    """触发每日任务"""
    from app.scraper.pipeline import run_daily
    
    background_tasks.add_task(run_daily)
    return {"message": "每日任务已启动"}


@router.post("/scrape/weekly")
def trigger_weekly(background_tasks: BackgroundTasks):
    """触发每周任务"""
    from app.scraper.pipeline import run_weekly
    
    background_tasks.add_task(run_weekly)
    return {"message": "每周任务已启动"}