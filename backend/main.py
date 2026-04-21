from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.data import router as data_router
from app.api.scraping import router as scraping_router
from app.api.keywords import router as keywords_router

app = FastAPI(title="Amazon Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router, prefix="/api", tags=["数据查询"])
app.include_router(scraping_router, prefix="/api", tags=["爬取控制"])
app.include_router(keywords_router, prefix="/api", tags=["关键词管理"])


@app.get("/")
def root():
    return {"message": "Amazon Scraper API is running", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}