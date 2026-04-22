"""
完整流程编排：爬取 → 预处理 → 存储到数据库
支持：手动触发、每日定时、每周定时
"""

import json
import logging
import time
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# 导入项目模块
import sys
_scraper_dir = str(Path(__file__).parent)
_app_dir = str(Path(__file__).parent.parent)
_backend_dir = str(Path(__file__).parent.parent.parent)
for _p in [_scraper_dir, _app_dir, _backend_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config import settings
from database import SessionLocal

# 导入爬虫模块
from auto_amazon_scraper import SimpleRequestExecutor, AmazonSearchScraper
from dataprocess import process as preprocess_file

logger = logging.getLogger(__name__)


class ScrapingPipeline:
    """爬取流程编排器"""
    
    def __init__(self, db_session: Session = None):
        self.db_session = db_session or SessionLocal()
        self.auto_close = db_session is None
    
    def close(self):
        if self.auto_close and self.db_session:
            self.db_session.close()
    
    def run_full_pipeline(self, keyword: str, pages: int = None, 
                          save_to_file: bool = True) -> Dict[str, Any]:
        """
        完整流程：爬取 → 预处理 → 存入数据库
        
        :param keyword: 搜索关键词
        :param pages: 页数（None=自动）
        :param save_to_file: 是否保存JSON文件
        :return: 执行结果
        """
        result = {
            'keyword': keyword,
            'status': 'pending',
            'started_at': datetime.now().isoformat(),
            'total_items': 0,
            'file_path': None,
            'error': None
        }
        
        try:
            # 1. 创建任务记录
            task_id = self._create_task_record(keyword, pages)
            # 3. 爬取数据 - 长时间操作
            self._update_task(task_id, 'running', 0, None)# zy 422
            
            # 2. 爬取数据
            logger.info(f"开始爬取: {keyword}")
            raw_items = self._run_scraper(keyword, pages, save_to_file)
            
            if not raw_items:
                result['status'] = 'no_data'
                result['completed_at'] = datetime.now().isoformat()
                self._update_task(task_id, 'failed', 0, '无数据')
                return result
            
            result['total_items'] = len(raw_items)
            
            # 3. 获取生成的文件路径
            if save_to_file:
                result['file_path'] = self._get_latest_file(keyword)
            
            # 4. 预处理数据（添加字段）
            processed_file = self._preprocess_file(result['file_path'])
            self._update_task(task_id, 'running', len(raw_items), None) # zy 422
            # 5. 存入数据库
            db_count = self._save_to_database(processed_file)
            
            # 6. 更新任务状态
            self._update_task(task_id, 'completed', db_count)
            
            result['status'] = 'success'
            result['saved_to_db'] = db_count
            result['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"✅ 流程完成: {keyword}, 爬取 {len(raw_items)} 条, 入库 {db_count} 条")
            
        except Exception as e:
            logger.error(f"流程失败 {keyword}: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            result['completed_at'] = datetime.now().isoformat()
            if 'task_id' in locals():
                self._update_task(task_id, 'failed', 0, str(e))
        
        return result
    
    def run_batch(self, pages: int = None, save_to_file: bool = True) -> List[Dict]:
        """批量运行所有关键词"""
        keywords = self._load_keywords()
        results = []
        
        logger.info(f"开始批量爬取，共 {len(keywords)} 个关键词")
        
        for idx, keyword in enumerate(keywords, 1):
            print(f"\n[{idx}/{len(keywords)}] 处理: {keyword}")
            result = self.run_full_pipeline(keyword, pages, save_to_file)
            results.append(result)
            print(f"  ✅ {result['status']} - {result.get('saved_to_db', 0)} 条数据")
            
            # 关键词间隔，避免被封
            if idx < len(keywords):
                wait_time = 30
                print(f"  等待 {wait_time} 秒...")
                time.sleep(wait_time)
        
        return results
    
    def _run_scraper(self, keyword: str, pages: int = None, save_to_file: bool = True) -> List:
        """运行爬虫"""
        # 使用配置中的参数
        postal_code = str(settings.DEFAULT_POSTAL_CODE)
        delay_range = self._get_delay_range()
        output_dir = str(Path(__file__).parent / "amazon_data")
        
        executor = SimpleRequestExecutor(
            delay_range=delay_range,
            postal_code=postal_code
        )
        
        scraper = AmazonSearchScraper(
            request_executor=executor,
            delay_range=delay_range,
            output_dir=output_dir,
            postal_code=postal_code
        )
        
        try:
            items = scraper.scrape_search(keyword, pages=pages, auto_pages=(pages is None))
            if save_to_file and items:
                scraper.save_results(items, keyword)
            return items
        finally:
            executor.close()
    
    def _preprocess_file(self, file_path: str) -> Path:
        """预处理JSON文件"""
        if not file_path or not Path(file_path).exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 调用 dataprocess 的 process 函数
        preprocess_file(file_path)
        
        # 返回处理后的文件路径
        path = Path(file_path)
        processed_path = Path(__file__).parent / "processed_data" / f"{path.stem}_processed.json"
        return processed_path
    
    def _save_to_database(self, processed_file: Path) -> int:
        """将处理后的数据存入数据库"""
        with open(processed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 导入模型
        from app.models import RawSearchResult
        
        saved_count = 0
        for item in data:
            # 跳过没有ASIN的记录（除非是SB广告的内嵌商品）
            if not item.get('asin') and item.get('ad_type') not in ['SB', 'SB_Video']:
                continue
            
            record = RawSearchResult(
                data_index=item.get('data_index'),
                page=item.get('page'),
                index_position=item.get('index'),
                ad_type=item.get('ad_type'),
                ad_rank=str(item.get('ad_rank')) if item.get('ad_rank') else None,
                organic_rank=item.get('organic_rank'),
                asin=item.get('asin'),
                title=item.get('title'),
                url=item.get('url'),
                price_current=item.get('price_current'),
                price_list=item.get('price_list'),
                rating_stars=item.get('rating_stars'),
                rating_count=item.get('rating_count'),
                is_prime=item.get('is_prime', False),
                image_small=item.get('image_small'),
                image_large=item.get('image_large'),
                brand_name=item.get('brand_name'),
                inner_products=json.dumps(item.get('inner_products', [])),
                inner_products_count=item.get('inner_products_count', 0),
                postal_code=str(item.get('postal_code')) if item.get('postal_code') else None,
                keyword=item.get('keyword'),
                date=date.fromisoformat(item['date']) if item.get('date') else None,
                scraped_at=datetime.fromisoformat(item['scraped_at']) if item.get('scraped_at') else datetime.now()
            )
            self.db_session.add(record)
            saved_count += 1
        
        self.db_session.commit()
        logger.info(f"存入数据库 {saved_count} 条记录")
        return saved_count
    
    def _create_task_record(self, keyword: str, pages: int = None) -> int:
        """创建任务记录"""
        from app.models import ScrapingTask
        
        task = ScrapingTask(
            keyword=keyword,
            pages=pages,
            status='running',
            started_at=datetime.now()
        )
        self.db_session.add(task)
        self.db_session.commit()
        self.db_session.refresh(task)
        return task.id
    
    def _update_task(self, task_id: int, status: str, total_items: int = 0, error: str = None):
        """更新任务状态
    
        Args:
            task_id: 任务ID
            status: 任务状态
            total_items: 总项目数
            error: 错误信息
        """
        from app.models import ScrapingTask
        
        task = self.db_session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if task:
            task.status = status
            task.total_items = total_items
            if status == 'completed':
                task.completed_at = datetime.now()
            if error:
                task.error_message = error
            self.db_session.commit()
    
    def _get_latest_file(self, keyword: str) -> str:
        """获取最新的JSON文件路径"""
        data_dir = Path(__file__).parent / "amazon_data"
        files = list(data_dir.glob(f"{keyword}_*.json"))
        if not files:
            return None
        # 排除已处理的文件
        files = [f for f in files if "_processed" not in f.stem]
        if not files:
            return None
        return str(max(files, key=lambda f: f.stat().st_mtime))
    
    def _load_keywords(self) -> List[str]:
        """加载关键词列表"""
        config_file = Path(__file__).parent / "scraper_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('keywords', [])
        return []
    
    def _get_delay_range(self) -> tuple:
        """获取延迟范围"""
        parts = settings.DEFAULT_DELAY_RANGE.split(',')
        return (float(parts[0]), float(parts[1]) if len(parts) > 1 else float(parts[0]))


# ============================================================
# 定时任务和API调用的入口函数
# ============================================================

def run_now(keyword: str = None, pages: int = None) -> Dict:
    """
    手动触发爬取（供API调用）
    
    :param keyword: 关键词，不传则爬取所有
    :param pages: 页数
    :return: 执行结果
    """
    pipeline = ScrapingPipeline()
    try:
        if keyword:
            return pipeline.run_full_pipeline(keyword, pages)
        else:
            return pipeline.run_batch(pages)
    finally:
        pipeline.close()


def run_daily():
    """每日爬取任务（供定时器调用）"""
    print(f"\n=== 每日爬取任务开始: {datetime.now()} ===")
    pipeline = ScrapingPipeline()
    try:
        results = pipeline.run_batch()
        success_count = len([r for r in results if r['status'] == 'success'])
        print(f"=== 每日任务完成: 成功 {success_count}/{len(results)} ===\n")
        return results
    finally:
        pipeline.close()


def run_weekly():
    """每周爬取任务（供定时器调用）"""
    print(f"\n=== 每周爬取任务开始: {datetime.now()} ===")
    # 每周可以爬取更多页数
    pipeline = ScrapingPipeline()
    try:
        results = pipeline.run_batch(pages=None)  # 自动获取所有页
        success_count = len([r for r in results if r['status'] == 'success'])
        print(f"=== 每周任务完成: 成功 {success_count}/{len(results)} ===\n")
        return results
    finally:
        pipeline.close()


def import_processed_data(folder: str = None) -> Dict:
    """
    只入库：读取 processed_data/ 里的文件直接写入数据库，不爬取
    """
    if folder is None:
        folder = Path(__file__).parent / "processed_data"
    else:
        folder = Path(folder)

    files = [f for f in folder.glob("*_processed.json")]
    if not files:
        return {"status": "no_files", "folder": str(folder)}

    pipeline = ScrapingPipeline()
    total = 0
    try:
        for f in files:
            count = pipeline._save_to_database(f)
            total += count
            print(f"入库: {f.name} → {count} 条")
    finally:
        pipeline.close()

    return {"status": "success", "files": len(files), "total_saved": total}
# 在 pipeline.py 末尾添加

async def run_now_with_logs(keyword: str = None, pages: int = None, manager=None):
    """带日志输出的爬取"""
    if manager:
        await manager.send_log(f"🚀 开始爬取任务: {keyword or '所有关键词'}")
    
    pipeline = ScrapingPipeline()
    try:
        if keyword:
            result = pipeline.run_full_pipeline(keyword, pages)
        else:
            result = pipeline.run_batch(pages)
        
        if manager:
            if isinstance(result, dict):
                await manager.send_log(f"✅ 爬取完成: {result.get('keyword', keyword)} - {result.get('saved_to_db', 0)} 条数据")
            elif isinstance(result, list):
                success_count = len([r for r in result if r['status'] == 'success'])
                total_count = len(result)
                await manager.send_log(f"✅ 批量爬取完成: 成功 {success_count}/{total_count}")
    except Exception as e:
        if manager:
            await manager.send_log(f"❌ 爬取失败: {str(e)}")
        raise
    finally:
        pipeline.close()

async def run_daily_with_logs(manager=None):
    """每日任务带日志"""
    if manager:
        await manager.send_log("📅 每日任务开始执行...")
    result = run_daily()
    if manager:
        await manager.send_log("✅ 每日任务执行完成")
    return result

async def run_weekly_with_logs(manager=None):
    """每周任务带日志"""
    if manager:
        await manager.send_log("📅 每周任务开始执行...")
    result = run_weekly()
    if manager:
        await manager.send_log("✅ 每周任务执行完成")
    return result

# 测试入口
if __name__ == "__main__":
    result = run_now("beach+towels", pages=1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # import_processed_data()
