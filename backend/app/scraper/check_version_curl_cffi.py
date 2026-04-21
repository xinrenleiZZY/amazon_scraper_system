from curl_cffi import requests
from curl_cffi.requests import BrowserType

a = requests.__version__
print(f"curl_cffi 版本: {a}")

# 查看所有支持的浏览器类型
print("\n支持的浏览器指纹:")
for attr in dir(BrowserType):
    if not attr.startswith('_'):
        print(f"  - {attr}")