from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, TIMESTAMP, JSON, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class RawSearchResult(Base):
    __tablename__ = "raw_search_results"

    id = Column(Integer, primary_key=True, index=True)
    data_index = Column(Integer)
    page = Column(Integer)
    index_position = Column(String(50))
    ad_type = Column(String(20))
    ad_rank = Column(String(10))
    organic_rank = Column(Integer)
    asin = Column(String(100))
    title = Column(Text)
    url = Column(Text)
    price_current = Column(String(50))
    price_list = Column(String(50))
    rating_stars = Column(Numeric(3, 1))
    rating_count = Column(Integer)
    is_prime = Column(Boolean, default=False)
    image_small = Column(Text)
    image_large = Column(Text)
    brand_name = Column(String(200))
    inner_products = Column(JSON)
    inner_products_count = Column(Integer, default=0)
    postal_code = Column(String(20))
    keyword = Column(String(200), nullable=False)
    date = Column(Date)
    scraped_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())


class ScrapingTask(Base):
    __tablename__ = "scraping_tasks"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(200), nullable=False)
    pages = Column(Integer)
    total_items = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    # progress = Column(Integer, default=0)  # 添加这个字段
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    source_file = Column(String(500))
    error_message = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

#YU 421
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

#YU 421
class UserKeyword(Base):
    __tablename__ = "user_keywords"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(200), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


# ========== 新增：关键词属性表 ==========
class KeywordAttribute(Base):
    """关键词属性表 - 存储标签、节日、热卖期等信息"""
    __tablename__ = "keyword_attributes"
    
    keyword = Column(String(255), primary_key=True, index=True)
    tags = Column(JSON, default=list)  # JSON 数组：["夏季", "泳池派对"]
    festival = Column(String(100), default="")  # 节日：圣诞节、黑五等
    festival_type = Column(String(20), default="")  # 大节日/小节日
    hot_season = Column(String(50), default="")  # 高峰期/预热期等
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)