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
        self.proxy = proxy
        
        # 创建带代理的session
        if proxy:
            logger.info(f"使用代理: {proxy}")
            self.session = CurlSession(impersonate="chrome120", proxy=proxy)
        else:
            browsers = ["chrome110", "chrome116", "chrome120", "safari15_5"]
            selected_browser = random.choice(browsers)
            logger.info(f"使用浏览器指纹: {selected_browser}")
            self.session = CurlSession(impersonate=selected_browser)

        # 创建 HeadersManager 实例
        config = AntiScrapingConfig()
        config.RANDOM_USER_AGENT = True
        self.headers_manager = HeadersManager(config)
        
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
                self.session.get("https://www.amazon.com/gp/glow/get-location.html", headers=init_headers, timeout=30)
                time.sleep(random.uniform(1, 3))
                
                # 访问首页
                init_response = self.session.get('https://www.amazon.com/', headers=init_headers, timeout=30)
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
                response = self.session.get(url,headers=headers, timeout=30)
                
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
            title_el = item.select_one('[data-elementid="sb-headline"] span, ._c2Itd_headline_3CcZ9')
            if title_el:
                title = title_el.text.strip()
            
            url = None
            link_el = item.select_one('._c2Itd_link_pJ4S_, a[href*="stores/page"]')
            if link_el and link_el.get('href'):
                href = link_el.get('href')
                url = f"https://www.amazon.com{href}" if href.startswith('/') else href
            
            brand_logo = None
            logo_el = item.select_one('._c2Itd_logo_1BwG8 img')
            if logo_el:
                brand_logo = logo_el.get('src')
            
            inner_products = []
            ad_items = item.select('[data-asin][data-asin!=""]')
            for inner_idx, ad_item in enumerate(ad_items, start=1):
                inner_title_el = ad_item.select_one('.a-size-base-plus, .a-truncate-full')
                inner_title = inner_title_el.text.strip() if inner_title_el else "N/A"
                inner_price_el = ad_item.select_one('.a-price .a-offscreen')
                inner_price = inner_price_el.text.strip() if inner_price_el else None
                
                inner_products.append({
                    'position': inner_idx,
                    'asin': ad_item.get('data-asin'),
                    'title': inner_title,
                    'price': inner_price,
                })
            
            return ProductInfo(
                data_index=data_index, page=page, ad_type="SB",
                ad_rank=ad_rank, title=title, url=url or "N/A",
                brand_name=title, image_small=brand_logo,
                inner_products=inner_products
            )
        except Exception as e:
            logger.error(f"解析SB广告失败: {e}")
            return None
    
    def parse_sb_video_ad(self, item, data_index, page, ad_rank):
        """解析SB视频广告"""
        try:
            title = "N/A"
            title_el = item.select_one('[data-elementid="sb-headline"], ._c2Itd_headline_3CcZ9')
            if title_el:
                title = title_el.text.strip()
            
            url = None
            link_el = item.select_one('._c2Itd_link_pJ4S_')
            if link_el and link_el.get('href'):
                href = link_el.get('href')
                url = f"https://www.amazon.com{href}" if href.startswith('/') else href
            
            inner_products = []
            ad_items = item.select('[data-asin][data-asin!=""]')
            for inner_idx, ad_item in enumerate(ad_items, start=1):
                inner_title_el = ad_item.select_one('.a-size-base-plus, .a-truncate-full')
                inner_title = inner_title_el.text.strip() if inner_title_el else "N/A"
                
                inner_products.append({
                    'position': inner_idx,
                    'asin': ad_item.get('data-asin'),
                    'title': inner_title,
                })
            
            return ProductInfo(
                data_index=data_index, page=page, ad_type="SB_Video",
                ad_rank=ad_rank, title=title, url=url or "N/A",
                inner_products=inner_products
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
                        logger.info(f"[SB广告] data-index={data_index} SB排名:{sb_rank} - {product.title[:40]}")
                        sb_rank += 1
                
                elif has_video:
                    product = self.parse_sb_video_ad(div, data_index, page, sb_video_rank)
                    if product:
                        all_items.append(product)
                        logger.info(f"[SB视频] data-index={data_index} 视频排名:{sb_video_rank} - {product.title[:40]}")
                        sb_video_rank += 1
                
                elif asin:
                    if is_sponsored:
                        product = self.parse_sp_product(div, data_index, page, ad_rank=sp_rank)
                        if product:
                            all_items.append(product)
                            logger.info(f"[SP广告] data-index={data_index} SP排名:{sp_rank} - {product.title[:40]}")
                            sp_rank += 1
                    else:
                        product = self.parse_sp_product(div, data_index, page, organic_rank=organic_rank)
                        if product:
                            all_items.append(product)
                            logger.info(f"[自然] data-index={data_index} 自然排名:{organic_rank} - {product.title[:40]}")
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