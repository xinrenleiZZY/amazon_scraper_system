from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime, date


class RawSearchResultOut(BaseModel):
    id: int
    data_index: Optional[int]
    page: Optional[int]
    ad_type: Optional[str]
    ad_rank: Optional[str]
    organic_rank: Optional[int]
    asin: Optional[str]
    title: Optional[str]
    price_current: Optional[str]
    rating_stars: Optional[float]
    rating_count: Optional[int]
    is_prime: Optional[bool]
    brand_name: Optional[str]
    inner_products: Optional[Any]
    postal_code: Optional[str]
    keyword: str
    date: Optional[date]
    scraped_at: Optional[datetime]

    class Config:
        from_attributes = True


class ScrapingTaskOut(BaseModel):
    id: int
    keyword: str
    pages: Optional[int]
    total_items: int
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    source_file: Optional[str]
    error_message: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True