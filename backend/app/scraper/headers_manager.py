# headers_manager.py
"""
请求头管理器
功能：生成随机请求头、管理Cookie、模拟浏览器指纹
"""

import random
import time
import hashlib
import uuid
from typing import Dict, Optional
from fake_useragent import UserAgent

try:
    from fake_useragent import UserAgent
    FAKE_UA_AVAILABLE = True
except ImportError:
    FAKE_UA_AVAILABLE = False
    print("Warning: fake-useragent not installed. Run: pip install fake-useragent")


class HeadersManager:
    """请求头管理器"""
    
    def __init__(self, config):
        self.config = config
        self.session_cookies = {}
        
        if FAKE_UA_AVAILABLE:
            self.ua = UserAgent()
        else:
            self.ua = None
    
    def get_headers(self) -> Dict[str, str]:
        """生成请求头"""
        
        if self.config.RANDOM_USER_AGENT and self.ua:
            user_agent = self._get_random_ua()
        else:
            user_agent = self._get_default_ua()
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': self._get_accept_language(),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # 随机添加Referer
        if random.random() > 0.6:
            headers['Referer'] = self._get_random_referer()
        
        # 添加真实浏览器指纹（可选）
        if random.random() > 0.8:
            headers['Sec-Ch-Ua'] = self._get_sec_ch_ua()
            headers['Sec-Ch-Ua-Mobile'] = '?0'
            headers['Sec-Ch-Ua-Platform'] = self._get_platform()
        
        return headers
    
    def _get_random_ua(self) -> str:
        """获取随机User-Agent"""
        try:
            if self.config.USE_MOBILE_UA:
                return self.ua.random  # 可能包含移动端
            else:
                # 只使用桌面端
                desktop_ua = [
                    self.ua.chrome,
                    self.ua.firefox,
                    self.ua.edge,
                    self.ua.safari
                ]
                return random.choice([ua for ua in desktop_ua if ua])
        except:
            return self._get_default_ua()
    
    def _get_default_ua(self) -> str:
        """默认User-Agent"""
        chrome_versions = ['120.0.0.0', '119.0.0.0', '118.0.0.0']
        os_types = [
            'Windows NT 10.0; Win64; x64',
            'Macintosh; Intel Mac OS X 10_15_7',
            'X11; Linux x86_64'
        ]
        
        return f"Mozilla/5.0 ({random.choice(os_types)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36"
    
    def _get_accept_language(self) -> str:
        """获取Accept-Language"""
        languages = [
            'en-US,en;q=0.9',
        ]
        return random.choice(languages)
    
    def _get_random_referer(self) -> str:
        """获取随机Referer"""
        referers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://www.yahoo.com/',
            'https://www.amazon.com/',
            'https://www.reddit.com/',
        ]
        return random.choice(referers)
    
    def _get_sec_ch_ua(self) -> str:
        """获取Sec-Ch-Ua"""
        brands = [
            '"Google Chrome";v="120", "Not?A_Brand";v="99", "Chromium";v="120"',
            '"Microsoft Edge";v="120", "Not?A_Brand";v="99", "Chromium";v="120"',
            '"Brave";v="120", "Not?A_Brand";v="99", "Chromium";v="120"',
        ]
        return random.choice(brands)
    
    def _get_platform(self) -> str:
        """获取平台"""
        platforms = ['Windows', 'macOS', 'Linux']
        return random.choice(platforms)
    
    def get_cookies(self) -> Dict[str, str]:
        """获取Cookie"""
        cookies = {
            'session-id': self._generate_session_id(),
            'session-id-time': str(int(time.time() * 1000)),
            'i18n-prefs': 'USD',
            'ubid-main': self._generate_ubid(),
            'sp-cdn': 'L5Z9:US',
        }
        
        # 合并会话Cookie
        cookies.update(self.session_cookies)
        
        return cookies
    
    def update_cookies(self, cookies: Dict[str, str]):
        """更新Cookie"""
        self.session_cookies.update(cookies)
    
    def _generate_session_id(self) -> str:
        """生成模拟session-id"""
        return f"146-{uuid.uuid4().hex[:13].upper()}-{uuid.uuid4().hex[:13].upper()}"
    
    def _generate_ubid(self) -> str:
        """生成ubid"""
        return f"132-{uuid.uuid4().hex[:20]}"
    
    def clear_cookies(self):
        """清除Cookie"""
        self.session_cookies = {}


if __name__ == "__main__":
    from backend.app.scraper.anti_scraping_config import AntiScrapingConfig
    
    config = AntiScrapingConfig()
    hm = HeadersManager(config)
    
    print("请求头:", hm.get_headers())
    print("Cookie:", hm.get_cookies())