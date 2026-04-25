# auto_amazon_scraper.py - 自动化亚马逊爬虫
# 支持命令行参数、配置文件、自动获取所有页数

import time
import random
import json
import re
import logging
import argparse
import os
import sys
from curl_cffi.requests import Session as CurlSession
from datetime import datetime
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import pandas as pd
from anti_scraping_config import AntiScrapingConfig
from headers_manager import HeadersManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('amazon_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimpleRequestExecutor:
    """请求执行器 - 增强版"""
    
    def __init__(self, delay_range=(3, 6), postal_code="90060", proxy=None):
        self.delay_range = delay_range
        self.postal_code = postal_code

        # 从 AntiScrapingConfig 读取代理配置（优先使用传入的 proxy 参数）
        anti_config = AntiScrapingConfig()
        if proxy is None and anti_config.USE_PROXY:
            proxy = anti_config.PROXY_URL
        self.proxy = proxy

         # 构建 curl_cffi 兼容的代理字典
        self.proxies = None
        if proxy:
            # curl_cffi 使用 proxies 参数，支持完整 URL（包含认证）
            self.proxies = {
                "http": proxy,
                "https": proxy
            }
            # 隐藏密码打印
            proxy_display = proxy.split('@')[-1] if '@' in proxy else proxy
            logger.info(f"使用代理: {proxy_display}")
        
        # 选择浏览器指纹（支持的最新版本）
        browsers = ["chrome110", "chrome107", "chrome104", "chrome101", "chrome100", "safari15_5"]
        selected_browser = "chrome110" if proxy else random.choice(browsers)
        logger.info(f"使用浏览器指纹: {selected_browser}")
        
        # 创建 session
        session_created = False
        try:
            if self.proxies:
                self.session = CurlSession(impersonate=selected_browser, proxies=self.proxies)
            else:
                self.session = CurlSession(impersonate=selected_browser)
            session_created = True
        except Exception as e:
            logger.warning(f"带 proxies 参数创建失败: {e}")
            # 降级方案：使用环境变量
            if self.proxies:
                os.environ['HTTP_PROXY'] = proxy
                os.environ['HTTPS_PROXY'] = proxy
            try:
                self.session = CurlSession(impersonate=selected_browser)
                session_created = True
                logger.info("使用降级方案创建 Session 成功")
            except Exception as e2:
                logger.error(f"降级方案也失败: {e2}")
                raise

        # 创建 HeadersManager 实例
        anti_config.RANDOM_USER_AGENT = True
        self.headers_manager = HeadersManager(anti_config)

        # 初始化会话
        self._init_session()

        logger.info(f"初始化请求器，默认邮编: {self.postal_code}")

    def _init_session(self):
        """初始化亚马逊会话"""
        logger.info("正在初始化亚马逊美国会话...")
        init_headers = self.headers_manager.get_headers()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # init_response = self.session.get('https://www.amazon.com/', headers=init_headers, timeout=30)
                # 使用更真实的初始请求
                init_headers = self.headers_manager.get_headers()
                init_headers.update({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                })
                
                # 先访问robots.txt
                self.session.get("https://www.amazon.com/gp/glow/get-location.html", headers=init_headers, timeout=30, proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None)
                time.sleep(random.uniform(1, 3))

                # 访问首页
                init_response = self.session.get('https://www.amazon.com/', headers=init_headers, timeout=30, proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None)
                self.session.headers.update({
                    "accept-language": "en-US,en;q=0.9"
                })
                # success = self.set_zip_code()
                # if success:
                #     time.sleep(2)
                #     init_response = self.session.get('https://www.amazon.com/', headers=init_headers, timeout=30)
                # else:
                #     logger.warning("⚠️ ZIP设置失败，可能影响结果")

                if init_response.status_code == 200:
                    if '$' in init_response.text[:500]:
                        logger.info("✅ 美国站会话建立成功")
                        break
                    else:
                        logger.warning("⚠️ 首页未检测到美元")
                else:
                    logger.warning(f"会话初始化状态码: {init_response.status_code}")
            except Exception as e:
                logger.error(f"会话初始化失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
        
        # 设置语言和国家
        self.session.cookies.set('lc-main', 'en_US')
        # self.session.cookies.set('postalCode', self.postal_code)
        # self.session.cookies.set('shippingPostalCode', self.postal_code)
        # self.session.cookies.set('delivery-postal-code', self.postal_code)
        self.session.cookies.set('session-id-time', str(int(time.time() + 86400)), domain='.amazon.com')

        # 在请求头中添加邮编
        self.session.headers.update({
            'x-amzn-postal-code': self.postal_code,
            'x-amzn-postalcode': self.postal_code,
        })

        check = self.session.get("https://www.amazon.com/", headers=init_headers)

        if self.postal_code in check.text:
            
            logger.info("✅ ZIP生效成功")
        else:
            logger.warning("⚠️ ZIP可能未生效")

    def get(self, url, retry_count=3):
        """发送GET请求，支持重试"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
        
        headers = self.headers_manager.get_headers()
        headers['x-amzn-postal-code'] = self.postal_code

        for attempt in range(retry_count):
            try:
                 # 每次重试使用不同的headers
                headers = self.headers_manager.get_headers()
                headers.update({
                    'x-amzn-postal-code': self.postal_code,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                })
                response = self.session.get(url, headers=headers, timeout=30, proxies={"http": self.proxy, "https": self.proxy} if self.proxy else None)
                
                if response.status_code == 200:
                    # 检查页面类型
                    preview = response.text[:20000].lower()
                    
                    if 'cn' in response.url or 'amazon.cn' in response.url:
                        logger.error(f"❌ 被重定向到中国站: {response.url}")
                        return None
                    elif 'cny' in preview or 'CNY' in preview or '¥' in preview:
                        logger.warning("⚠️ 检测到人民币价格，可能还是中国站")
                        with open("debug_china_page.html", "w", encoding="utf-8") as f:
                            f.write(response.text)
                        logger.info("已保存到 debug_china_page.html")
                        return None
                    elif '$' in preview and 'cny' not in preview:
                        logger.info("✅ 检测到美元价格，成功获取美国站数据")
                        return response
                    else:
                        logger.info("无法判断货币类型，继续处理")
                        return response
                        
                elif response.status_code == 503:
                    wait_time = (2 ** attempt) * random.uniform(5, 10)  # 指数退避
                    logger.warning(f"访问被拒绝 (503)，尝试 {attempt+1}/{retry_count}")
                    if attempt < retry_count - 1:
                        time.sleep(wait_time)
                        
                        # 如果是第一次失败，尝试更换浏览器指纹
                        if attempt == 0:
                            browsers = ["chrome110", "chrome116", "chrome120", "safari15_5"]
                            new_browser = random.choice([b for b in browsers if b != self.session.impersonate])
                            logger.info(f"更换浏览器指纹: {self.session.impersonate} -> {new_browser}")
                            self.session = CurlSession(impersonate=new_browser)
                    else:
                        return None
                else:
                    logger.warning(f"HTTP {response.status_code}，尝试 {attempt+1}/{retry_count}")
                    if attempt < retry_count - 1:
                        time.sleep(random.uniform(5, 10))
                    
            except Exception as e:
                logger.error(f"请求失败 (尝试 {attempt+1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(random.uniform(5, 10))
        
        return None
    
    def close(self):
        self.session.close()

    def set_zip_code(self):
        """通过Amazon接口设置邮编,post请求,访问首页，设置zip,再次访问首页"""
        try:
            logger.info(f"开始设置 ZIP: {self.postal_code}")

            # =========================
            # Step 1: 预热（拿 cookie）
            # =========================
            headers = self.headers_manager.get_headers()
            self.session.get(
                "https://www.amazon.com/",
                headers=headers,
                timeout=30
            )
            time.sleep(random.uniform(1, 2))

            # =========================
            # Step 2: 手动写 cookie（关键！）
            # =========================
            domain = ".amazon.com"
            self.session.cookies.set("lc-main", "en_US", domain=domain)
            self.session.cookies.set("i18n-prefs", "USD", domain=domain)

            # 这几个是核心 ZIP cookie
            self.session.cookies.set("ubid-main", str(random.randint(100000000,999999999)), domain=domain)
            self.session.cookies.set("session-id", str(random.randint(100000000,999999999)), domain=domain)
            self.session.cookies.set("session-id-time", str(int(time.time() + 86400)), domain=domain)

            # ⚠️ 关键 ZIP cookie（提升成功率）
            self.session.cookies.set("sp-cdn", "L5Z9:US", domain=domain)
            self.session.cookies.set("skin", "noskin", domain=domain)

            # =========================
            # Step 3: glow API（核心）
            # =========================
            glow_url = "https://www.amazon.com/gp/delivery/ajax/address-change.html"

            glow_headers = self.headers_manager.get_headers()
            glow_headers.update({
                "content-type": "application/json",
                "origin": "https://www.amazon.com",
                "referer": "https://www.amazon.com/gp/glow/get-location.html",
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*"
            })

            payload = {
                "locationType": "LOCATION_INPUT",
                "zipCode": self.postal_code,
                "deviceType": "web",
                "storeContext": "generic",
                "pageType": "Gateway",
                "actionSource": "glow"
            }

            r = self.session.post(glow_url, headers=glow_headers, json=payload, timeout=30)
            logger.info(f"Glow API状态: {r.status_code}")
            success = False
            try:
                data = r.json()
                if data.get("successful") == 1:
                    success = True
            except:
                pass
            # =========================
            # Step 4: fallback（关键增强）
            # =========================
            if not success:
                logger.warning("⚠️ 第一次 ZIP 失败，执行 fallback...")

                time.sleep(2)

                r2 = self.session.post(glow_url, headers=glow_headers, json=payload, timeout=30)

                try:
                    data2 = r2.json()
                    if data2.get("successful") == 1:
                        success = True
                        logger.info("✅ fallback 成功")
                except:
                    pass

            # =========================
            # Step 5: 强制请求验证
            # =========================
            time.sleep(2)

            check = self.session.get(
                "https://www.amazon.com/",
                headers=headers,
                timeout=30
            )

            if self.postal_code in check.text:
                logger.info("✅ ZIP 生效（页面检测成功）")
                return True

            # 第二种验证（更稳）
            if "$" in check.text[:1000]:
                logger.info("✅ ZIP 生效（美元检测成功）")
                return True

            logger.warning("❌ ZIP 可能未生效")
            return False

        except Exception as e:
            logger.error(f"ZIP 设置异常: {e}")
            return False

class ProductInfo:
    """商品/广告信息数据类"""
    def __init__(self, 
                 data_index, page, ad_type,
                 ad_rank=None, organic_rank=None,
                 asin=None, title=None, url=None,
                 price_current=None, price_list=None,
                 rating_stars=None, rating_count=None,
                 is_prime=False, image_small=None, image_large=None,
                 brand_name=None, inner_products=None,
                 **kwargs):
        self.data_index = data_index
        self.page = page
        self.ad_type = ad_type
        self.ad_rank = ad_rank
        self.organic_rank = organic_rank
        self.asin = asin
        self.title = title
        self.url = url
        self.price_current = price_current
        self.price_list = price_list
        self.rating_stars = rating_stars
        self.rating_count = rating_count
        self.is_prime = is_prime
        self.image_small = image_small
        self.image_large = image_large
        self.brand_name = brand_name
        self.inner_products = inner_products if inner_products is not None else []
        self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self):
        return self.__dict__


class AmazonSearchScraper:
    """亚马逊搜索爬虫 - 自动化版本"""
    
    def __init__(self, request_executor=None, delay_range=(3, 6), 
                 output_dir="./amazon_data", postal_code="90060"):
        self.request_executor = request_executor or SimpleRequestExecutor(delay_range, postal_code)
        self.output_dir = output_dir
        self.postal_code = postal_code
        os.makedirs(output_dir, exist_ok=True)
    
    def get_total_pages(self, keyword):
        """自动获取搜索结果总页数"""
        url = f"https://www.amazon.com/s?k={keyword}"
        logger.info(f"正在获取总页数: {url}")
        
        response = self.request_executor.get(url)
        if not response:
            logger.error("无法获取搜索结果")
            return 1
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 方法1: 查找分页按钮
        pagination = soup.select('[aria-label*="Go to page"], .s-pagination-item')
        if pagination:
            page_numbers = []
            for item in pagination:
                text = item.get_text(strip=True)
                if text.isdigit():
                    page_numbers.append(int(text))
            
            if page_numbers:
                max_page = max(page_numbers)
                logger.info(f"检测到总页数: {max_page}")
                return max_page
        
        # 方法2: 查找"Page 1 of X"模式
        page_info = soup.find(string=re.compile(r'Page \d+ of (\d+)', re.IGNORECASE))
        if page_info:
            match = re.search(r'Page \d+ of (\d+)', page_info)
            if match:
                total = int(match.group(1))
                logger.info(f"检测到总页数: {total}")
                return total
        
        # 方法3: 检查是否有"Next"按钮，如果没有则只有1页
        next_button = soup.select('[aria-label="Go to next page"], .s-pagination-next')
        if not next_button or 'disabled' in next_button[0].get('class', []):
            logger.info("未检测到下一页按钮，总页数为: 1")
            return 1
        
        # 默认返回5页
        logger.warning("无法确定总页数，使用默认值: 5")
        return 5
    
    def _extract_price(self, item):
        """提取价格信息"""
        result = {'price_current': None, 'price_list': None}
        try:
            price_el = item.select_one('.a-price .a-offscreen')
            if price_el:
                result['price_current'] = price_el.text.strip()
            
            list_price_el = item.select_one('.a-text-strike')
            if list_price_el:
                result['price_list'] = list_price_el.text.strip()
        except:
            pass
        return result
    
    def _extract_rating(self, item):
        """提取评分信息"""
        result = {'rating_stars': None, 'rating_count': None}
        try:
            rating_el = item.select_one('.a-icon-star-mini .a-icon-alt')
            if rating_el:
                rating_text = rating_el.text.strip()
                match = re.search(r'(\d+\.?\d*)', rating_text)
                if match:
                    result['rating_stars'] = float(match.group(1))
            
            count_el = item.select_one('[aria-label*="ratings"]')
            if count_el:
                aria_label = count_el.get('aria-label', '')
                match = re.search(r'([\d,]+)', aria_label)
                if match:
                    result['rating_count'] = int(match.group(1).replace(',', ''))
        except:
            pass
        return result
    
    def _extract_image(self, item):
        """提取图片URL"""
        try:
            img_el = item.select_one('.s-image')
            if img_el:
                small = img_el.get('src')
                large = small.replace('_UL320_', '_SL1500_') if small else None
                return small, large
        except:
            pass
        return None, None
    
    def _is_sponsored(self, item) -> bool:
        """判断是否为SP广告"""
        return bool(item.select_one('.puis-sponsored-label-text')) or \
               bool(item.select_one('[aria-label*="Sponsored"]'))
    
    def _has_video(self, item) -> bool:
        """判断是否包含视频"""
        return bool(item.select_one('video'))
    
    def _is_title_row(self, item) -> bool:
        """判断是否为标题行"""
        asin = item.get('data-asin', '')
        classes = ' '.join(item.get('class', []))
        return not asin and 's-widget' in classes and 'AdHolder' not in classes
    
    def parse_sp_product(self, item, data_index, page, ad_rank=None, organic_rank=None):
        """解析SP广告或自然商品"""
        try:
            asin = item.get('data-asin')
            if not asin:
                return None
            
            is_sponsored = self._is_sponsored(item)
            ad_type = "SP" if is_sponsored else "Organic"
            
            title_el = item.select_one('h2 span')
            title = title_el.text.strip() if title_el else "N/A"
            
            link_el = item.select_one('h2 a')
            url = None
            if link_el and link_el.get('href'):
                href = link_el.get('href')
                url = f"https://www.amazon.com{href}" if href.startswith('/') else href
            
            img_small, img_large = self._extract_image(item)
            price_info = self._extract_price(item)
            rating_info = self._extract_rating(item)
            is_prime = bool(item.select_one('.a-icon-prime'))
            
            return ProductInfo(
                data_index=data_index, page=page, ad_type=ad_type,
                ad_rank=ad_rank, organic_rank=organic_rank,
                asin=asin, title=title, url=url or "N/A",
                price_current=price_info['price_current'],
                price_list=price_info['price_list'],
                rating_stars=rating_info['rating_stars'],
                rating_count=rating_info['rating_count'],
                is_prime=is_prime,
                image_small=img_small, image_large=img_large
            )
        except Exception as e:
            logger.error(f"解析SP商品失败: {e}")
            return None
    
    def parse_sb_ad(self, item, data_index, page, ad_rank):
        """解析SB品牌广告"""
        try:
            title = "N/A"
            # 方法1: 从 data-elementid="sb-headline" 获取
            title_el = item.select_one('[data-elementid="sb-headline"] span, ._c2Itd_headline_3CcZ9')
            if title_el:
                title = title_el.text.strip()
            # 方法2: 从 data-properties 中获取 headline
            if (title == "N/A" or title == "") and item.has_attr('data-properties'):
                try:
                    import json
                    props = json.loads(item.get('data-properties'))
                    title = props.get('headline', title)
                except:
                    pass
            # 方法3: 从链接文本获取
            if title == "N/A":
                link_title = item.select_one('a[data-elementid="sb-headline"]')
                if link_title:
                    title = link_title.text.strip()
            url = None
            link_el = item.select_one('a[href*="stores/page"], ._c2Itd_link_pJ4S_')
            if link_el and link_el.get('href'):
                href = link_el.get('href')
                url = f"https://www.amazon.com{href}" if href.startswith('/') else href
            
            brand_logo = None
            logo_el = item.select_one('._c2Itd_logo_2VIw3 img, ._c2Itd_logo_1BwG8 img, ._c2Itd_image_3UiYm')
            if logo_el:
                brand_logo = logo_el.get('src')
            
             # ========== 4. 提取内嵌商品 ==========
            inner_products = []
            ad_items = item.select('[data-asin][data-asin!=""]')
            for inner_idx, ad_item in enumerate(ad_items, start=1):
                asin = ad_item.get('data-asin')
                if not asin:
                    continue
                # 商品标题 - 多种选择器
                
                inner_title = "N/A"
                title_elem = ad_item.select_one(
                    '.a-size-base-plus, .a-truncate-full, .a-size-medium, '
                    'span.a-truncate-full, ._c2Itd_truncate_2HCiY span, '
                    'a[data-type="productTitle"] span'
                )
                if title_elem:
                    inner_title = title_elem.text.strip()

                # 商品价格
                inner_price = None
                price_el = ad_item.select_one('.a-price .a-offscreen')
                if price_el:
                    inner_price = price_el.text.strip()
                else:
                    price_whole = ad_item.select_one('.a-price-whole')
                    price_fraction = ad_item.select_one('.a-price-fraction')
                    if price_whole and price_fraction:
                        inner_price = f"${price_whole.text.strip()}.{price_fraction.text.strip()}"
                
                # 商品原价（划线价）
                list_price = None
                list_price_el = ad_item.select_one('.a-text-strike')
                if list_price_el:
                    list_price = list_price_el.text.strip()
                
                # 折扣百分比
                discount = None
                discount_el = ad_item.select_one('._c2Itd_discountText_2gdxP')
                if discount_el:
                    discount = discount_el.text.strip()
                
                # 评分
                rating = None
                rating_el = ad_item.select_one('.a-icon-star-mini')
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    import re
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        rating = float(match.group(1))
                
                # 评论数
                review_count = None
                review_el = ad_item.select_one('[data-rt]')
                if review_el:
                    review_text = review_el.text.strip()
                    match = re.search(r'\(?(\d+)\)?', review_text)
                    if match:
                        review_count = int(match.group(1))
                
                # 商品图片
                image_url = None
                img_el = ad_item.select_one('img')
                if img_el:
                    image_url = img_el.get('src')
                
                # 促销/限时优惠标识
                has_deal = bool(ad_item.select_one('._c2Itd_dealBadge_KEp1h, ._c2Itd_apexContainer_1nn0g'))
                deal_text = None
                if has_deal:
                    deal_el = ad_item.select_one('._c2Itd_labelContainer_3cijI span, ._c2Itd_apexContainer_1nn0g span')
                    if deal_el:
                        deal_text = deal_el.text.strip()
                
                inner_products.append({
                    'position': inner_idx,
                    'asin': asin,
                    'title': inner_title,
                    'price': inner_price,
                    'list_price': list_price,
                    'discount': discount,
                    'rating_stars': rating,
                    'rating_count': review_count,
                    'image': image_url,
                    'has_deal': has_deal,
                    'deal_text': deal_text
                })
            
            # 备用方法：如果上面没找到，尝试 carousel 中的商品
            if not inner_products:
                carousel_items = item.select('._c2Itd_item_3Z9mf, ._c2Itd_item_2t3sY, [data-sbtc-carousel-item="true"]')
                for carousel_item in carousel_items:
                    asin_elem = carousel_item.select_one('[data-asin][data-asin!=""]')
                    asin = asin_elem.get('data-asin') if asin_elem else None
                    
                    title_elem = carousel_item.select_one('.a-size-base-plus, .a-truncate-full')
                    product_title = title_elem.text.strip() if title_elem else "N/A"
                    
                    if asin:
                        inner_products.append({
                            'position': len(inner_products) + 1,
                            'asin': asin,
                            'title': product_title,
                            'price': None
                        })
            
            # ========== 5. 提取品牌标语/额外信息 ==========
            brand_tagline = None
            tagline_el = item.select_one('._c2Itd_ctaSponsoredContainer_3LWVa span.a-size-mini.a-color-secondary')
            if tagline_el:
                tagline_text = tagline_el.text.strip()
                if tagline_text and tagline_text != "|" and tagline_text != "Sponsored":
                    brand_tagline = tagline_text
            
            logger.info(f"[SB广告] data-index={data_index} SB排名:{ad_rank} - 品牌:{title[:40]}, 内嵌商品数:{len(inner_products)}")
            
            return ProductInfo(
                data_index=data_index,
                page=page,
                ad_type="SB",
                ad_rank=ad_rank,
                title=title,
                url=url or "N/A",
                brand_name=title,
                image_small=brand_logo,
                inner_products=inner_products,
                inner_products_count=len(inner_products)
            )
            
        except Exception as e:
            logger.error(f"解析SB广告失败: {e}")
            return None
    
    def parse_sb_video_ad(self, item, data_index, page, ad_rank):
        """解析SB视频广告 - 支持多种结构"""
        try:
            inner_products = []
            
            # ========== 1. 提取广告标题 ==========
            title = "N/A"
            
            # 方法1: 从 data-properties JSON 中提取 headline
            if item.has_attr('data-properties'):
                try:
                    import json
                    props = json.loads(item.get('data-properties'))
                    title = props.get('headline', title)
                except:
                    pass
            
            # 方法2: 从 HTML 选择器获取
            if title == "N/A":
                title_el = item.select_one('.sbv-headline span, [data-elementid="sb-headline"] span')
                if title_el:
                    title = title_el.text.strip()
            
            # ========== 2. 提取商品链接 ==========
            url = None
            link_el = item.select_one('a[href*="/dp/"], a[href*="amazon.com/dp/"]')
            if link_el and link_el.get('href'):
                href = link_el.get('href')
                # 处理长链接，提取真实 ASIN
                if 'https://aax-us-east-retail-direct.amazon.com' in href and '/dp/' in href:
                    parts = href.split('/dp/')
                    if len(parts) > 1:
                        asin_part = parts[1].split('?')[0].split('/')[0]
                        url = f"https://www.amazon.com/dp/{asin_part}"
                elif href.startswith('/'):
                    url = f"https://www.amazon.com{href}"
                else:
                    url = href
            
            # ========== 3. 提取品牌 Logo ==========
            brand_logo = None
            logo_el = item.select_one('._c2Itd_brandLogoContainer_2BXRc img, ._c2Itd_logoContainer_3ZEjK img')
            if logo_el:
                brand_logo = logo_el.get('src')
            
            # ========== 4. 提取内嵌商品 ==========
            
            # 方法A: 查找所有带 data-asin 的 div（最直接的方式）
            ad_items = item.select('div[data-asin][data-asin!=""]')
            
            for inner_idx, ad_item in enumerate(ad_items, start=1):
                asin = ad_item.get('data-asin')
                if not asin:
                    continue
                
                # 提取标题
                inner_title = "N/A"
                title_elem = ad_item.select_one('h2 span, .a-size-medium, .a-size-base-plus, .a-size-base, a[data-type="productTitle"]')
                if title_elem:
                    inner_title = title_elem.text.strip()
                
                # 提取价格
                inner_price = None
                price_elem = ad_item.select_one('.a-price .a-offscreen')
                if price_elem:
                    inner_price = price_elem.text.strip()
                else:
                    price_whole = ad_item.select_one('.a-price-whole')
                    price_fraction = ad_item.select_one('.a-price-fraction')
                    if price_whole and price_fraction:
                        inner_price = f"${price_whole.text.strip()}.{price_fraction.text.strip()}"
                
                # 提取评分
                rating = None
                rating_elem = ad_item.select_one('.a-icon-star-mini')
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    import re
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        rating = float(match.group(1))
                
                # 提取评论数
                review_count = None
                review_elem = ad_item.select_one('[data-type="productReviews"] .a-size-small, .a-size-small.a-color-tertiary')
                if review_elem and review_elem.text.strip().isdigit():
                    review_count = int(review_elem.text.strip())
                
                inner_products.append({
                    'position': inner_idx,
                    'asin': asin,
                    'title': inner_title,
                    'price': inner_price,
                    'rating_stars': rating,
                    'rating_count': review_count
                })
            
            # 方法B: 如果方法A没找到，尝试查找 .desktop-video-product-view 容器
            if not inner_products:
                product_containers = item.select('.desktop-video-product-view, .sbv-product')
                for product_container in product_containers:
                    asin_elem = product_container.select_one('[data-asin][data-asin!=""]')
                    asin = asin_elem.get('data-asin') if asin_elem else None
                    
                    title_elem = product_container.select_one('h2 span, .a-size-medium')
                    inner_title = title_elem.text.strip() if title_elem else "N/A"
                    
                    if asin:
                        inner_products.append({
                            'position': len(inner_products) + 1,
                            'asin': asin,
                            'title': inner_title,
                            'price': None
                        })
            
            # 方法C: 查找 ._c2Itd_productTitle_1vCSB 类（亚马逊新样式）
            if not inner_products:
                title_links = item.select('._c2Itd_productTitle_1vCSB')
                for title_link in title_links:
                    # 向上查找包含 data-asin 的容器
                    parent = title_link.parent
                    while parent and parent != item:
                        if parent.has_attr('data-asin') and parent.get('data-asin'):
                            asin = parent.get('data-asin')
                            inner_title = title_link.text.strip()
                            inner_products.append({
                                'position': len(inner_products) + 1,
                                'asin': asin,
                                'title': inner_title,
                                'price': None
                            })
                            break
                        parent = parent.parent
             # ========== 5. 如果外层没有 asin 和 title，使用第一个内嵌商品的信息 ==========
            main_asin = None
            main_title = title  # 优先使用广告标题
            
            # 如果广告标题是 N/A 或空，且有内嵌商品，使用第一个内嵌商品的标题
            if (main_title == "N/A" or not main_title) and inner_products:
                main_title = inner_products[0].get('title', 'N/A')
                main_asin = inner_products[0].get('asin', None)
                logger.info(f"[SB视频] 使用第一个内嵌商品作为主商品 - ASIN:{main_asin}, 标题:{main_title[:40]}")
            
            logger.info(f"[SB视频] data-index={data_index} 排名:{ad_rank} - 标题:{title[:40]}, 内嵌商品数:{len(inner_products)}")
            
            return ProductInfo(
                data_index=data_index,
                page=page,
                ad_type="SB_Video",
                ad_rank=ad_rank,
                title=main_title,
                asin=main_asin,
                url=url or "N/A",
                brand_name=title if title != "N/A" else main_title,
                image_small=brand_logo,
                inner_products=inner_products,
                inner_products_count=len(inner_products)
            )
            
        except Exception as e:
            logger.error(f"解析SB视频广告失败: {e}")
            return None
    
    def parse_title_row(self, item, data_index, page):
        """解析标题行"""
        try:
            title_text = item.get_text(strip=True)
            return ProductInfo(
                data_index=data_index, page=page, ad_type="Title",
                title=title_text[:100] if title_text else "Unknown Title"
            )
        except Exception as e:
            logger.error(f"解析标题行失败: {e}")
            return None
    
    def scrape_search(self, keyword, pages=None, auto_pages=True):
        """
        爬取搜索结果
        :param keyword: 搜索关键词
        :param pages: 指定页数，如果为None且auto_pages为True则自动获取
        :param auto_pages: 是否自动获取总页数
        """
        all_items = []
        
        # 确定页数
        if auto_pages and pages is None:
            total_pages = self.get_total_pages(keyword)
            pages = total_pages
            logger.info(f"自动检测到总页数: {pages}")
        elif pages is None:
            pages = 1
            logger.info(f"使用默认页数: {pages}")
        else:
            logger.info(f"使用指定页数: {pages}")
        
        # 各类排名计数器
        organic_rank = 1
        sp_rank = 1
        sb_rank = 1
        sb_video_rank = 1
        
        logger.info(f"开始爬取关键词: {keyword}, 页数: {pages}")
        
        for page in range(1, pages + 1):
            url = f"https://www.amazon.com/s?k={keyword}&page={page}"
            logger.info(f"正在访问第 {page} 页: {url}")
            
            response = self.request_executor.get(url)
            if not response:
                logger.error(f"第 {page} 页请求失败")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 选择所有带有 data-index 属性的 div
            all_divs = soup.find_all('div', attrs={'data-index': True})
            all_divs_sorted = sorted(all_divs, key=lambda x: int(x.get('data-index', 0)))
            
            logger.info(f"第 {page} 页找到 {len(all_divs_sorted)} 个带data-index的元素")
            
            for div in all_divs_sorted:
                data_index = int(div.get('data-index', -1))
                asin = div.get('data-asin', '')
                has_video = self._has_video(div)
                is_ad_holder = 'AdHolder' in ' '.join(div.get('class', []))
                is_sponsored = self._is_sponsored(div)
                is_title = self._is_title_row(div)
                
                product = None
                
                # 分类解析
                if is_title:
                    product = self.parse_title_row(div, data_index, page)
                    if product:
                        all_items.append(product)
                
                elif not asin and is_ad_holder and not has_video:
                    product = self.parse_sb_ad(div, data_index, page, sb_rank)
                    if product:
                        all_items.append(product)
                        logger.info(f"[SB广告] data-index={data_index} SB排名:{sb_rank} - {product.title[:40]} - {product.price_current}")
                        sb_rank += 1
                
                elif has_video:
                    product = self.parse_sb_video_ad(div, data_index, page, sb_video_rank)
                    if product:
                        all_items.append(product)
                        logger.info(f"[SB视频] data-index={data_index} 视频排名:{sb_video_rank} - {product.title[:40]} - {product.price_current}")
                        sb_video_rank += 1
                
                elif asin:
                    if is_sponsored:
                        product = self.parse_sp_product(div, data_index, page, ad_rank=sp_rank)
                        if product:
                            all_items.append(product)
                            logger.info(f"[SP广告] data-index={data_index} SP排名:{sp_rank} - {product.title[:40]} - {product.price_current}")
                            sp_rank += 1
                    else:
                        product = self.parse_sp_product(div, data_index, page, organic_rank=organic_rank)
                        if product:
                            all_items.append(product)
                            logger.info(f"[自然] data-index={data_index} 自然排名:{organic_rank} - {product.title[:40]} - {product.price_current}")
                            organic_rank += 1
                
                else:
                    logger.debug(f"[跳过] data-index={data_index}")
            
            # 翻页间隔
            if page < pages:
                time.sleep(random.uniform(8, 12))
        
        logger.info(f"爬取完成，共获取 {len(all_items)} 个元素")
        logger.info(f"  - 自然商品: {organic_rank - 1} 个")
        logger.info(f"  - SP广告: {sp_rank - 1} 个")
        logger.info(f"  - SB广告: {sb_rank - 1} 个")
        logger.info(f"  - SB视频: {sb_video_rank - 1} 个")
        
        return all_items
    
    def save_results(self, items, keyword):
        """保存结果"""
        if not items:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{self.output_dir}/{keyword}_{timestamp}"
        
        # 转字典
        items_dict = []
        for item in items:
            d = item.to_dict()
            if 'inner_products' in d and d['inner_products']:
                d['inner_products_count'] = len(d['inner_products'])
            items_dict.append(d)
        
        # 保存JSON
        with open(f"{base_filename}.json", 'w', encoding='utf-8') as f:
            json.dump(items_dict, f, ensure_ascii=False, indent=2)
        
        # 保存CSV
        df = pd.DataFrame(items_dict)
        if 'inner_products' in df.columns:
            df = df.drop(columns=['inner_products'])
        df.to_csv(f"{base_filename}.csv", index=False, encoding='utf-8-sig')
        
        # 生成报告
        self._generate_report(items, keyword, timestamp)
        
        logger.info(f"数据已保存到: {base_filename}.json")
        return base_filename
    
    def _generate_report(self, items, keyword, timestamp):
        """生成统计报告"""
        report_path = f"{self.output_dir}/{keyword}_{timestamp}_report.txt"
        
        stats = {
            'total': len(items),
            'organic': len([i for i in items if i.ad_type == 'Organic']),
            'sp': len([i for i in items if i.ad_type == 'SP']),
            'sb': len([i for i in items if i.ad_type == 'SB']),
            'sb_video': len([i for i in items if i.ad_type == 'SB_Video']),
            'title': len([i for i in items if i.ad_type == 'Title']),
        }
        
        total_inner = sum(len(i.inner_products) for i in items if i.inner_products)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"亚马逊搜索爬虫报告\n")
            f.write(f"关键词: {keyword}\n")
            f.write(f"邮编: {self.postal_code}\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write("【统计摘要】\n")
            f.write(f"总元素数: {stats['total']}\n")
            f.write(f"  - 自然商品: {stats['organic']}\n")
            f.write(f"  - SP广告: {stats['sp']}\n")
            f.write(f"  - SB广告: {stats['sb']}\n")
            f.write(f"  - SB视频: {stats['sb_video']}\n")
            f.write(f"  - 标题行: {stats['title']}\n")
            f.write(f"SB广告内包含商品数: {total_inner}\n")


def load_config(config_file='scraper_config.json'):
    """加载配置文件"""
    default_config = {
        "keywords": ["towels", "sheets", "pillows"],
        "pages": None,  # null表示自动获取所有页数
        "postal_code": "90060",
        "delay_range": [3, 6],
        "output_dir": "./amazon_data",
        "proxy": None
    }
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 合并配置
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
    else:
        return default_config


def main():
    parser = argparse.ArgumentParser(description='亚马逊自动化爬虫')
    parser.add_argument('-k', '--keyword', type=str, help='搜索关键词')
    parser.add_argument('-p', '--pages', type=int, help='指定页数（不指定则自动获取所有页）')
    parser.add_argument('-pc', '--postal_code', type=str, default='90060', help='配送邮编')
    parser.add_argument('-o', '--output', type=str, default='./amazon_data', help='输出目录')
    parser.add_argument('-d', '--delay', type=float, nargs=2, default=[3, 6], help='延迟范围(秒)')
    parser.add_argument('--proxy', type=str, help='代理地址 (例如: http://127.0.0.1:7890)')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--batch', action='store_true', help='批量模式（从配置文件读取多个关键词）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("亚马逊自动化爬虫 v2.0")
    print("=" * 60)
    
    # 批量模式
    if args.batch or (not args.keyword and os.path.exists('./scraper_config.json')):
        config = load_config('scraper_config.json')
        keywords = config.get('keywords', [])
        pages = config.get('pages')
        postal_code = config.get('postal_code', '90060')
        output_dir = config.get('output_dir', './amazon_data')
        delay_range = tuple(config.get('delay_range', [3, 6]))
        proxy = config.get('proxy')
        
        print(f"批量模式启动，共 {len(keywords)} 个关键词")
        print(f"关键词列表: {keywords}")
        print(f"页数设置: {'自动获取所有页' if pages is None else f'{pages}页'}")
        print(f"配送邮编: {postal_code}")
        print(f"代理: {proxy if proxy else '未使用'}")
        print("-" * 60)
        
        for idx, keyword in enumerate(keywords, 1):
            print(f"\n[{idx}/{len(keywords)}] 开始爬取: {keyword}")
            
            request_executor = SimpleRequestExecutor(
                delay_range=delay_range,
                postal_code=postal_code,
                proxy=proxy
            )
            
            scraper = AmazonSearchScraper(
                request_executor=request_executor,
                delay_range=delay_range,
                output_dir=output_dir,
                postal_code=postal_code
            )
            
            try:
                items = scraper.scrape_search(keyword, pages=pages, auto_pages=(pages is None))
                
                if items:
                    filepath = scraper.save_results(items, keyword)
                    print(f"✅ {keyword} 爬取成功！共 {len(items)} 个元素")
                else:
                    print(f"❌ {keyword} 未获取到数据")
                    
            except Exception as e:
                print(f"❌ {keyword} 爬取出错: {e}")
                logger.error(f"批量爬取 {keyword} 失败: {e}")
            finally:
                request_executor.close()
            
            # 关键词间隔
            if idx < len(keywords):
                wait_time = random.uniform(30, 60)
                print(f"等待 {wait_time:.0f} 秒后继续下一个关键词...")
                time.sleep(wait_time)
        
        print("\n" + "=" * 60)
        print("批量爬取完成！")
        
    # 单关键词模式
    else:
        keyword = args.keyword
        if not keyword:
            keyword = input("请输入搜索关键词: ").strip()
            if not keyword:
                keyword = "towels"
        
        pages = args.pages
        if pages is None:
            auto = input("是否自动获取所有页数? (y/n, 默认y): ").strip().lower()
            if auto == 'n':
                pages = int(input("请输入页数: ").strip() or "1")
            else:
                print("将自动检测总页数并爬取所有页面")
        
        postal_code = args.postal_code or input("请输入配送邮编 (默认: 90060): ").strip() or "90060"
        
        print(f"\n爬取参数:")
        print(f"  关键词: {keyword}")
        print(f"  页数: {'自动获取所有' if pages is None else pages}")
        print(f"  邮编: {postal_code}")
        print(f"  代理: {args.proxy if args.proxy else '未使用'}")
        print("-" * 60)
        
        request_executor = SimpleRequestExecutor(
            delay_range=tuple(args.delay),
            postal_code=postal_code,
            proxy=args.proxy
        )
        
        scraper = AmazonSearchScraper(
            request_executor=request_executor,
            delay_range=tuple(args.delay),
            output_dir=args.output,
            postal_code=postal_code
        )
        
        try:
            items = scraper.scrape_search(keyword, pages=pages, auto_pages=(pages is None))
            
            if items:
                filepath = scraper.save_results(items, keyword)
                print(f"\n✅ 爬取成功！")
                print(f"📊 共获取 {len(items)} 个元素")
                print(f"   - 自然商品: {len([i for i in items if i.ad_type == 'Organic'])}")
                print(f"   - SP广告: {len([i for i in items if i.ad_type == 'SP'])}")
                print(f"   - SB广告: {len([i for i in items if i.ad_type == 'SB'])}")
                print(f"   - SB视频: {len([i for i in items if i.ad_type == 'SB_Video'])}")
                print(f"📁 数据已保存到: {filepath}")
            else:
                print("\n❌ 未获取到任何数据")
                
        except Exception as e:
            print(f"\n❌ 爬取出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            request_executor.close()


if __name__ == "__main__":
    main()