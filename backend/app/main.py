# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入 API 路由
# 直接导入 router
from app.api.data import router as data_router
from app.api.scraping import router as scraping_router
from app.api.keywords import router as keywords_router
from app.api.distributed import router as distributed_router# ZY0422
from app.api.users import router as users_router #YU 421
# zy 0422 添加日志路由
from app.api import logs


app = FastAPI(title="Amazon Scraper API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(data_router, prefix="/api", tags=["数据查询"])
app.include_router(scraping_router, prefix="/api", tags=["爬取控制"])
app.include_router(keywords_router, prefix="/api", tags=["关键词管理"])
app.include_router(distributed_router, prefix="/api", tags=["分布式爬取"])# ZY 0422
app.include_router(users_router, prefix="/api", tags=["人员管理"]) #YU 421
app.include_router(logs.router, prefix="/api", tags=["logs"])# zy 0422 添加日志路由
@app.get("/")
def root():
    return {"message": "Amazon Scraper API is running", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}