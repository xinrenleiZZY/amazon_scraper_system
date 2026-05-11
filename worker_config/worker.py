#!/usr/bin/env python
"""
Worker 节点程序
部署在每台虚拟机上，从 NAS 领取任务并执行爬取
"""

import os
import sys
import json
import time
import socket
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from threading import Thread

# ========== 配置区域 ==========
NAS_SHARE_PATH = "//192.168.40.3/钟正洋/amazon_scraper"  # NAS 共享路径
WORKER_ID = socket.gethostname()  # 自动获取主机名
PROXY_URL = "http://127.0.0.1:7890"  # 代理地址（每台虚拟机可以不同）
MAX_TASKS = 2  # 同时执行任务数
# =============================

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 目录配置
NAS_BASE = Path(NAS_SHARE_PATH)
TASKS_DIR = NAS_BASE / "tasks"
RESULTS_DIR = NAS_BASE / "results"
HEARTBEAT_DIR = NAS_BASE / "heartbeats"
SCRIPTS_DIR = Path(__file__).parent

# 确保目录存在
for d in [TASKS_DIR, RESULTS_DIR, HEARTBEAT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def send_heartbeat():
    """发送心跳"""
    while True:
        try:
            heartbeat_file = HEARTBEAT_DIR / f"{WORKER_ID}.json"
            with open(heartbeat_file, 'w') as f:
                json.dump({
                    "worker_id": WORKER_ID,
                    "timestamp": time.time(),
                    "ip": socket.gethostbyname(socket.gethostname()),
                    "proxy": PROXY_URL,
                    "status": "running"
                }, f)
            time.sleep(30)  # 每30秒发送一次
        except Exception as e:
            logger.error(f"心跳发送失败: {e}")
            time.sleep(60)


def run_scraper(keyword: str, pages: int = None) -> Path:
    """执行爬虫"""
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "auto_amazon_scraper.py"),
        "-k", keyword,
        "-o", str(RESULTS_DIR)
    ]
    
    if pages:
        cmd.extend(["-p", str(pages)])
    
    if PROXY_URL:
        cmd.extend(["--proxy", PROXY_URL])
    
    logger.info(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 设置60分钟超时
    
    if result.returncode != 0:
        logger.error(f"爬取失败: {result.stderr}")
        raise Exception(result.stderr)
    
    # 查找生成的 JSON 文件
    json_files = list(RESULTS_DIR.glob(f"{keyword}_*.json"))
    if json_files:
        # 取最新的
        latest = max(json_files, key=lambda f: f.stat().st_mtime)
        return latest
    
    raise Exception("未找到输出文件")


def preprocess_file(json_file: Path) -> Path:
    """预处理 JSON 文件"""
    import subprocess
    
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "dataprocess.py"),
        "-f", str(json_file)
    ]
    
    logger.info(f"预处理: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    processed_file = json_file.parent / json_file.stem.replace('.json', '_processed.json')
    return processed_file


def claim_task():
    """领取任务"""
    try:
        # 查找待处理任务
        for task_file in TASKS_DIR.glob("*.json"):
            with open(task_file, 'r') as f:
                task = json.load(f)
            
            if task.get("status") == "pending":
                # 领取任务
                task["status"] = "running"
                task["assigned_to"] = WORKER_ID
                task["started_at"] = datetime.now().isoformat()
                
                with open(task_file, 'w') as f:
                    json.dump(task, f, indent=2)
                
                return task
    except Exception as e:
        logger.error(f"领取任务失败: {e}")
    
    return None


def complete_task(task_file: Path, result_file: Path):
    """完成任务"""
    with open(task_file, 'r') as f:
        task = json.load(f)
    
    task["status"] = "completed"
    task["completed_at"] = datetime.now().isoformat()
    task["result_file"] = str(result_file)
    
    with open(task_file, 'w') as f:
        json.dump(task, f, indent=2)


def worker_loop():
    """Worker 主循环"""
    logger.info(f"Worker {WORKER_ID} 启动，代理: {PROXY_URL}")
    
    while True:
        try:
            # 1. 领取任务
            task = claim_task()
            
            if task is None:
                time.sleep(5)
                continue
            
            keyword = task["keyword"]
            pages = task.get("pages")
            task_file = TASKS_DIR / f"{task['task_id']}.json"
            
            logger.info(f"开始执行任务: {keyword}")
            
            # 2. 执行爬取
            json_file = run_scraper(keyword, pages)
            logger.info(f"爬取完成: {json_file}")
            
            # 3. 预处理
            processed_file = preprocess_file(json_file)
            logger.info(f"预处理完成: {processed_file}")
            
            # 4. 标记完成
            complete_task(task_file, processed_file)
            logger.info(f"任务完成: {keyword}")
            
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            # 标记任务失败，让其他 worker 重试
            if task_file:
                with open(task_file, 'r') as f:
                    task = json.load(f)
                task["status"] = "pending"
                task["error"] = str(e)
                with open(task_file, 'w') as f:
                    json.dump(task, f, indent=2)
            
            time.sleep(10)


def main():
    """主函数"""
    # 启动心跳线程
    heartbeat_thread = Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()
    
    # 启动 worker 循环
    worker_loop()


if __name__ == "__main__":
    main()