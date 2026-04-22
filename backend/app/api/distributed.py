# # backend/app/api/distributed.py
# """
# 分布式爬取 API
# """

# from fastapi import APIRouter, BackgroundTasks, HTTPException
# from typing import Optional, List
# from pydantic import BaseModel

# from backend.app.distributed.task_manager import task_distributor, result_collector

# router = APIRouter()


# class WorkerRegister(BaseModel):
#     worker_id: str
#     ip: str
#     proxy_pool: Optional[str] = None
#     max_concurrent: int = 1


# class TaskAssign(BaseModel):
#     keyword: str
#     pages: Optional[int] = None
#     worker_id: Optional[str] = None


# @router.post("/distributed/task")
# async def create_distributed_task(task: TaskAssign, background_tasks: BackgroundTasks):
#     """创建分布式任务"""
#     task_id = task_distributor.create_task(
#         keyword=task.keyword,
#         pages=task.pages,
#         worker_id=task.worker_id
#     )
    
#     return {
#         "task_id": task_id,
#         "keyword": task.keyword,
#         "status": "pending",
#         "message": "任务已分发，等待 Worker 领取"
#     }


# @router.get("/distributed/pending")
# async def get_pending_tasks(worker_id: Optional[str] = None):
#     """获取待处理任务（Worker 调用）"""
#     tasks = task_distributor.get_pending_tasks(worker_id)
#     return {"tasks": tasks}


# @router.post("/distributed/result")
# async def submit_result(task_id: str, result_file: str):
#     """Worker 提交结果"""
#     task_distributor.update_task_status(task_id, "completed", result_file)
#     return {"status": "ok"}


# @router.get("/distributed/workers")
# async def get_workers():
#     """获取所有在线 Worker"""
#     workers = result_collector.get_all_workers()
#     return {"workers": workers}


# @router.post("/distributed/import")
# async def import_remote_results(background_tasks: BackgroundTasks):
#     """手动导入远程结果"""
#     from backend.app.scraper.pipeline import import_processed_data
#     background_tasks.add_task(import_processed_data, str(RESULTS_DIR))
#     return {"message": "开始导入远程结果"}

# backend/app/api/distributed.py
"""
分布式爬取 API
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path

router = APIRouter()


class WorkerInfo(BaseModel):
    worker_id: str
    ip: str
    proxy_pool: Optional[str] = None
    max_concurrent: int = 1
    last_heartbeat: Optional[str] = None


class TaskAssign(BaseModel):
    keyword: str
    pages: Optional[int] = None
    worker_id: Optional[str] = None


# NAS 目录配置（从环境变量读取）
NAS_BASE = Path("/nas") if Path("/nas").exists() else Path("//192.168.40.3/钟正洋/amazon_scraper")
TASKS_DIR = NAS_BASE / "tasks"
RESULTS_DIR = NAS_BASE / "results"
HEARTBEAT_DIR = NAS_BASE / "heartbeats"


def get_workers():
    """获取所有在线 Worker"""
    workers = []
    if HEARTBEAT_DIR.exists():
        for hb_file in HEARTBEAT_DIR.glob("*.json"):
            try:
                with open(hb_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    workers.append({
                        "worker_id": data.get("worker_id"),
                        "ip": data.get("ip"),
                        "proxy": data.get("proxy"),
                        "status": data.get("status"),
                        "last_heartbeat": datetime.fromtimestamp(data.get("timestamp", 0)).isoformat()
                    })
            except:
                pass
    return workers


def get_pending_tasks():
    """获取待处理任务"""
    tasks = []
    if TASKS_DIR.exists():
        for task_file in TASKS_DIR.glob("*.json"):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    if task.get("status") == "pending":
                        tasks.append(task)
            except:
                pass
    return tasks


@router.post("/distributed/task")
async def create_distributed_task(task: TaskAssign):
    """创建分布式任务"""
    import uuid
    import time
    
    task_id = f"{task.keyword.replace(' ', '_')}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    # 确保目录存在
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    
    task_file = TASKS_DIR / f"{task_id}.json"
    task_data = {
        "task_id": task_id,
        "keyword": task.keyword,
        "pages": task.pages,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "assigned_to": task.worker_id
    }
    
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task_data, f, indent=2, ensure_ascii=False)
    
    return {
        "task_id": task_id,
        "keyword": task.keyword,
        "status": "pending",
        "message": "任务已分发，等待 Worker 领取"
    }


@router.get("/distributed/pending")
async def get_pending_tasks_api(worker_id: Optional[str] = None):
    """获取待处理任务（Worker 调用）"""
    tasks = get_pending_tasks()
    return {"tasks": tasks}


@router.get("/distributed/dashboard")
async def distributed_dashboard():
    """分布式监控面板"""
    workers = get_workers()
    pending = get_pending_tasks()
    
    # 统计各状态任务数
    running_tasks = []
    if TASKS_DIR.exists():
        for task_file in TASKS_DIR.glob("*.json"):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    if task.get("status") == "running":
                        running_tasks.append(task)
            except:
                pass
    
    return {
        "workers": workers,
        "workers_count": len(workers),
        "pending_tasks": len(pending),
        "running_tasks": len(running_tasks),
        "total_workers": len(workers),
        "pending_tasks_list": pending,
        "running_tasks_list": running_tasks
    }


@router.post("/distributed/result")
async def submit_result(task_id: str, result_file: str):
    """Worker 提交结果"""
    task_file = TASKS_DIR / f"{task_id}.json"
    if task_file.exists():
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
        task["status"] = "completed"
        task["result_file"] = result_file
        task["completed_at"] = datetime.now().isoformat()
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
    return {"status": "ok"}


@router.post("/distributed/heartbeat")
async def heartbeat(worker: WorkerInfo):
    """Worker 心跳"""
    HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    hb_file = HEARTBEAT_DIR / f"{worker.worker_id}.json"
    with open(hb_file, 'w', encoding='utf-8') as f:
        json.dump(worker.dict(), f, indent=2)
    return {"status": "ok"}