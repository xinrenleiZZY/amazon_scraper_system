# backend/app/distributed/task_manager.py
"""
分布式任务管理器
负责：任务分发、状态监控、结果收集
"""

import json
import time
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.models import ScrapingTask, RawSearchResult

logger = logging.getLogger(__name__)

# NAS 共享目录配置
NAS_BASE = Path(settings.NAS_SHARE_PATH) if hasattr(settings, 'NAS_SHARE_PATH') else Path("//nas/shared/amazon_scraper")
TASKS_DIR = NAS_BASE / "tasks"      # 任务分发目录
RESULTS_DIR = NAS_BASE / "results"  # 结果存放目录
PROCESSED_DIR = NAS_BASE / "processed"  # 已处理目录


class TaskDistributor:
    """任务分发器"""
    
    def __init__(self):
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """确保目录存在"""
        TASKS_DIR.mkdir(parents=True, exist_ok=True)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    def create_task(self, keyword: str, pages: int = None, worker_id: str = None) -> str:
        """创建并分发任务"""
        task_id = f"{keyword.replace(' ', '_')}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        task_file = TASKS_DIR / f"{task_id}.json"
        task_data = {
            "task_id": task_id,
            "keyword": keyword,
            "pages": pages,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "assigned_to": worker_id,
            "proxy": None
        }
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"任务已创建: {task_id} -> {task_file}")
        return task_id
    
    def get_pending_tasks(self, worker_id: str = None) -> List[Dict]:
        """获取待处理任务"""
        tasks = []
        for task_file in TASKS_DIR.glob("*.json"):
            with open(task_file, 'r', encoding='utf-8') as f:
                task = json.load(f)
                if task.get("status") == "pending":
                    if worker_id is None or task.get("assigned_to") == worker_id:
                        tasks.append(task)
        return tasks
    
    def update_task_status(self, task_id: str, status: str, result_file: str = None):
        """更新任务状态"""
        task_file = TASKS_DIR / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, 'r', encoding='utf-8') as f:
                task = json.load(f)
            
            task["status"] = status
            task["updated_at"] = datetime.now().isoformat()
            if result_file:
                task["result_file"] = result_file
            
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task, f, indent=2, ensure_ascii=False)


class ResultFileHandler(FileSystemEventHandler):
    """监控结果文件变化"""
    
    def __init__(self, callback):
        self.callback = callback
    
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('_processed.json'):
            self.callback(event.src_path)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('_processed.json'):
            self.callback(event.src_path)


class ResultCollector:
    """结果收集器"""
    
    def __init__(self):
        self._setup_watcher()
    
    def _setup_watcher(self):
        """设置文件监控"""
        self.observer = Observer()
        handler = ResultFileHandler(self.on_new_result)
        self.observer.schedule(handler, str(RESULTS_DIR), recursive=False)
        self.observer.start()
        logger.info(f"开始监控结果目录: {RESULTS_DIR}")
    
    def on_new_result(self, file_path: str):
        """新结果文件到达"""
        logger.info(f"检测到新结果文件: {file_path}")
        
        # 调用入库函数
        from backend.app.scraper.pipeline import import_processed_data
        import_processed_data(str(Path(file_path).parent))
        
        # 移动文件到已处理目录
        src = Path(file_path)
        dst = PROCESSED_DIR / src.name
        src.rename(dst)
        logger.info(f"文件已移动到已处理目录: {dst}")
    
    def get_all_workers(self) -> List[str]:
        """获取所有在线 worker"""
        workers = []
        for heartbeat_file in NAS_BASE.glob("heartbeats/*.json"):
            with open(heartbeat_file, 'r') as f:
                data = json.load(f)
                # 检查心跳是否过期（30秒）
                if time.time() - data.get("timestamp", 0) < 60:
                    workers.append(data)
        return workers


# 全局实例
task_distributor = TaskDistributor()
result_collector = ResultCollector()