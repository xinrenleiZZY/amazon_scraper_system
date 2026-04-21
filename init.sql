-- init.sql - 数据库初始化脚本

-- 创建原始数据表
CREATE TABLE IF NOT EXISTS raw_search_results (
    id SERIAL PRIMARY KEY,
    
    -- 位置信息
    data_index INTEGER,
    page INTEGER,
    index_position VARCHAR(50),
    
    -- 广告/商品类型
    ad_type VARCHAR(20),
    ad_rank VARCHAR(10),
    organic_rank INTEGER,
    
    -- 商品信息
    asin VARCHAR(100),
    title TEXT,
    url TEXT,
    
    -- 价格信息
    price_current VARCHAR(50),
    price_list VARCHAR(50),
    
    -- 评分信息
    rating_stars DECIMAL(3,1),
    rating_count INTEGER,
    is_prime BOOLEAN DEFAULT FALSE,
    
    -- 图片信息
    image_small TEXT,
    image_large TEXT,
    
    -- 品牌
    brand_name VARCHAR(200),
    
    -- SB/SB_Video 特有
    inner_products JSONB,
    inner_products_count INTEGER DEFAULT 0,
    
    -- 元数据
    postal_code VARCHAR(20),
    keyword VARCHAR(200) NOT NULL,
    date DATE,
    scraped_at TIMESTAMP,
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_raw_keyword ON raw_search_results(keyword);
CREATE INDEX IF NOT EXISTS idx_raw_asin ON raw_search_results(asin);
CREATE INDEX IF NOT EXISTS idx_raw_ad_type ON raw_search_results(ad_type);
CREATE INDEX IF NOT EXISTS idx_raw_scraped_at ON raw_search_results(scraped_at);
CREATE INDEX IF NOT EXISTS idx_raw_page ON raw_search_results(page);

-- 创建任务表
CREATE TABLE IF NOT EXISTS scraping_tasks (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(200) NOT NULL,
    pages INTEGER,
    total_items INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    source_file VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建任务表索引
CREATE INDEX IF NOT EXISTS idx_tasks_keyword ON scraping_tasks(keyword);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON scraping_tasks(status);

-- 创建更新时间函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 添加触发器
DROP TRIGGER IF EXISTS update_raw_search_results_updated_at ON raw_search_results;
CREATE TRIGGER update_raw_search_results_updated_at 
    BEFORE UPDATE ON raw_search_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 查看初始化结果
SELECT '✅ 数据库初始化完成' as status;