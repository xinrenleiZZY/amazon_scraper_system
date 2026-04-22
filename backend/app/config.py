# backend/app/config.py
"""
项目全局配置管理
读取 .env 环境变量，管理数据库、路径等配置
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings

# 获取项目根目录（amazon_scraper_system）
PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    """项目全局配置"""
    
     # ========== 数据库配置 ==========
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5200/amazon_scraper"
    
    # ========== 数据目录配置 ==========
    # 爬虫原始输出目录（相对于项目根目录）
    RAW_DATA_DIR: str = str(PROJECT_ROOT / "backend" / "app" / "scraper" / "amazon_data")
    
    # 预处理后的数据目录
    PROCESSED_DATA_DIR: str = str(PROJECT_ROOT / "backend" / "app" / "scraper" / "processed_data")
    
    # 输入文件夹（dataprocess.py 读取的目录）
    INPUT_FOLDER: str = str(PROJECT_ROOT / "backend" / "app" / "scraper" / "amazon_data")
    
    # ========== 爬虫默认配置 ==========
    DEFAULT_POSTAL_CODE: int = 90060
    DEFAULT_DELAY_RANGE: str = "3,6"  # 逗号分隔
    DEFAULT_PAGES: Optional[int] = None
    PROXY_URL: Optional[str] = None
    
    # ========== API配置 ==========
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # ========== 定时任务配置 ==========
    SCHEDULED_HOUR: int = 9
    SCHEDULED_MINUTE: int = 0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # ← 添加这一行，忽略 .env 中额外的字段

    # ========== 任务调度 ==========
    # NAS 共享目录（分布式爬取用）
    NAS_SHARE_PATH: str = "//192.168.40.3/钟正洋/amazon_scraper"
    
    # 是否启用分布式模式
    DISTRIBUTED_MODE: bool = False
    
settings = Settings()


# 便捷函数
def get_raw_data_dir() -> Path:
    """获取原始数据目录"""
    path = Path(settings.RAW_DATA_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_processed_data_dir() -> Path:
    """获取处理后数据目录"""
    path = Path(settings.PROCESSED_DATA_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_input_folder() -> Path:
    """获取输入文件夹（用于 dataprocess.py）"""
    path = Path(settings.INPUT_FOLDER)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_delay_range() -> tuple:
    """获取延迟范围"""
    parts = settings.DEFAULT_DELAY_RANGE.split(",")
    return (float(parts[0]), float(parts[1]) if len(parts) > 1 else float(parts[0]))