# config.py
"""
反爬系统配置文件
"""

class AntiScrapingConfig:
    """反爬配置"""
    
    # ========== 请求配置 ==========
    DEFAULT_TIMEOUT = 30  # 默认超时时间（秒）
    MAX_RETRIES = 3        # 最大重试次数
    
    # ========== 延迟配置 ==========
    MIN_DELAY = 2          # 最小延迟（秒）
    MAX_DELAY = 5          # 最大延迟（秒）
    PAGE_INTERVAL = (5, 10)  # 翻页间隔（秒）
    
    # ========== 限流配置 ==========
    REQUESTS_PER_MINUTE = 20   # 每分钟最大请求数
    REQUESTS_PER_HOUR = 200    # 每小时最大请求数
    
    # ========== 代理配置 ==========
    USE_PROXY = False           # 是否使用代理
    PROXY_TYPE = "http"         # 代理类型: http, https, socks5
    PROXY_FILE = "proxies.txt"  # 代理列表文件
    PROXY_ROTATION = "round_robin"  # 代理轮询方式: round_robin, random
    
    # ========== 请求头配置 ==========
    RANDOM_USER_AGENT = True    # 是否随机User-Agent
    USE_MOBILE_UA = False       # 是否使用移动端UA
    
    # ========== 验证码配置 ==========
    CAPTCHA_TIMEOUT = 60        # 验证码超时（秒）
    AUTO_SOLVE_CAPTCHA = False  # 是否自动解决验证码（需要第三方服务）
    
    # ========== 会话配置 ==========
    PERSISTENT_SESSION = True   # 是否保持会话
    SESSION_FILE = "session.pkl"  # 会话保存文件
    
    # ========== 日志配置 ==========
    LOG_LEVEL = "INFO"          # 日志级别
    LOG_FILE = "scraper.log"    # 日志文件


# 不同场景的预设配置
class FastMode(AntiScrapingConfig):
    """快速模式 - 适合测试"""
    MIN_DELAY = 0.5
    MAX_DELAY = 1
    REQUESTS_PER_MINUTE = 60
    USE_PROXY = False


class SafeMode(AntiScrapingConfig):
    """安全模式 - 适合生产"""
    MIN_DELAY = 5
    MAX_DELAY = 10
    REQUESTS_PER_MINUTE = 10
    USE_PROXY = True
    PROXY_ROTATION = "random"


class AggressiveMode(AntiScrapingConfig):
    """激进模式 - 高风险"""
    MIN_DELAY = 0
    MAX_DELAY = 0.5
    REQUESTS_PER_MINUTE = 120
    USE_PROXY = True