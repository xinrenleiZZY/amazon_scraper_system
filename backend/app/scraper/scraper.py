# backend/app/scraper/scraper.py
"""
爬虫调用封装 - 调用原始爬虫代码
支持手动触发、定时任务、配置管理
"""

import os
import sys
import subprocess
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# 添加原始爬虫目录到路径（同级目录）
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入原始爬虫模块
from auto_amazon_scraper import SimpleRequestExecutor, AmazonSearchScraper

logger = logging.getLogger(__name__)


class ScraperRunner:
    """爬虫运行器 - 封装原始爬虫"""
    
    def __init__(self, config_file: str = None):
        """
        初始化爬虫运行器
        :param config_file: 配置文件路径，默认使用 scraper_config.json
        """
        if config_file is None:
            config_file = current_dir / "scraper_config.json"
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载爬虫配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认配置
            return {
                "keywords": ["pool party decorations", "summer decorations"],
                "pages": None,
                "postal_code": "90060",
                "delay_range": [3, 6],
                "output_dir": "./amazon_data",
                "proxy": None
            }
    
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def get_keywords(self) -> List[str]:
        """获取关键词列表"""
        return self.config.get("keywords", [])
    
    def add_keyword(self, keyword: str):
        """添加关键词"""
        if keyword not in self.config["keywords"]:
            self.config["keywords"].append(keyword)
            self.save_config()
            logger.info(f"已添加关键词: {keyword}")
    
    def remove_keyword(self, keyword: str):
        """删除关键词"""
        if keyword in self.config["keywords"]:
            self.config["keywords"].remove(keyword)
            self.save_config()
            logger.info(f"已删除关键词: {keyword}")
    
    def update_keywords(self, keywords: List[str]):
        """批量更新关键词"""
        self.config["keywords"] = keywords
        self.save_config()
        logger.info(f"已更新关键词列表，共 {len(keywords)} 个")
    
    def scrape_keyword(self, keyword: str, pages: int = None, save_to_file: bool = True) -> List:
        """
        爬取单个关键词
        :param keyword: 搜索关键词
        :param pages: 指定页数，None则自动获取所有页
        :param save_to_file: 是否保存到文件
        :return: 商品列表
        """
        logger.info(f"开始爬取: {keyword}")
        
        # 获取配置
        postal_code = self.config.get("postal_code", "90060")
        delay_range = tuple(self.config.get("delay_range", [3, 6]))
        proxy = self.config.get("proxy")
        output_dir = self.config.get("output_dir", "./amazon_data")
        
        # 创建请求执行器
        request_executor = SimpleRequestExecutor(
            delay_range=delay_range,
            postal_code=postal_code,
            proxy=proxy
        )
        
        # 创建爬虫
        scraper = AmazonSearchScraper(
            request_executor=request_executor,
            delay_range=delay_range,
            output_dir=output_dir,
            postal_code=postal_code
        )
        
        try:
            # 执行爬取
            items = scraper.scrape_search(
                keyword, 
                pages=pages, 
                auto_pages=(pages is None)
            )
            
            # 保存到文件
            filepath = None
            if save_to_file and items:
                filepath = scraper.save_results(items, keyword)
                logger.info(f"数据已保存: {filepath}")
            
            logger.info(f"爬取完成: {keyword}, 共 {len(items) if items else 0} 个元素")
            return items
            
        except Exception as e:
            logger.error(f"爬取失败 {keyword}: {e}")
            raise
        finally:
            request_executor.close()
    
    def scrape_all_keywords(self, pages: int = None) -> Dict[str, Any]:
        """
        爬取所有关键词
        :param pages: 指定页数
        :return: 爬取结果统计
        """
        keywords = self.get_keywords()
        results = {
            "total": len(keywords),
            "success": [],
            "failed": [],
            "items_count": 0,
            "started_at": datetime.now().isoformat()
        }
        
        logger.info(f"开始批量爬取，共 {len(keywords)} 个关键词")
        
        for idx, keyword in enumerate(keywords, 1):
            print(f"\n[{idx}/{len(keywords)}] 爬取: {keyword}")
            
            try:
                items = self.scrape_keyword(keyword, pages)
                
                if items:
                    results["success"].append(keyword)
                    results["items_count"] += len(items)
                    print(f"✅ {keyword} 成功，共 {len(items)} 个元素")
                else:
                    results["failed"].append(keyword)
                    print(f"⚠️ {keyword} 无数据")
                    
            except Exception as e:
                results["failed"].append(keyword)
                print(f"❌ {keyword} 失败: {e}")
            
            # 关键词间隔（避免被封）
            if idx < len(keywords):
                import random
                wait_time = random.uniform(30, 60)
                print(f"等待 {wait_time:.0f} 秒...")
                time.sleep(wait_time)
        
        results["completed_at"] = datetime.now().isoformat()
        
        # 打印总结
        print("\n" + "=" * 50)
        print(f"批量爬取完成！")
        print(f"成功: {len(results['success'])} 个")
        print(f"失败: {len(results['failed'])} 个")
        print(f"总元素数: {results['items_count']}")
        print("=" * 50)
        
        return results
    
    def scrape_by_command_line(self, keyword: str = None, batch: bool = False):
        """
        通过命令行调用原始爬虫（备用方案）
        """
        cmd = [sys.executable, str(current_dir / "auto_amazon_scraper.py")]
        
        if keyword:
            cmd.extend(["-k", keyword])
        if batch:
            cmd.append("--batch")
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("爬取成功")
            return result.stdout
        else:
            logger.error(f"爬取失败: {result.stderr}")
            raise Exception(f"爬取失败: {result.stderr}")


# 单例实例
scraper_runner = ScraperRunner()


# 便捷函数
def scrape_keyword(keyword: str, pages: int = None) -> List:
    """便捷函数：爬取单个关键词"""
    return scraper_runner.scrape_keyword(keyword, pages)


def scrape_all_keywords(pages: int = None) -> Dict:
    """便捷函数：爬取所有关键词"""
    return scraper_runner.scrape_all_keywords(pages)


def get_keywords() -> List[str]:
    """获取关键词列表"""
    return scraper_runner.get_keywords()


def add_keyword(keyword: str):
    """添加关键词"""
    scraper_runner.add_keyword(keyword)


def remove_keyword(keyword: str):
    """删除关键词"""
    scraper_runner.remove_keyword(keyword)


def update_keywords(keywords: List[str]):
    """更新关键词列表"""
    scraper_runner.update_keywords(keywords)


# 测试
if __name__ == "__main__":
    import time

    print("当前关键词:", get_keywords())

    # 测试添加关键词
    add_keyword("towels")
    add_keyword("beach umbrella")
    print("添加后关键词:", get_keywords())

    # 测试移除关键词
    remove_keyword("beach umbrella")
    print("移除后关键词:", get_keywords())

    # 测试批量更新关键词【预留接口】
    update_keywords(["pool party decorations", "summer decorations", "beach towels"])
    print("更新后关键词:", get_keywords())

    # 测试爬取单个（取消注释以执行）
    # scrape_keyword("towels", pages=1)

    # 测试爬取所有（取消注释以执行）
    # scrape_all_keywords()