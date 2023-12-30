import requests
from bs4 import BeautifulSoup
import re

keyword = 'Sigma-Aldrich 606-68-8'

# To search page
search_url = 'https://www.sigmaaldrich.com/TW/en'
# Search for the CAS number
cas_num = keyword.split(' ')[-1]
product_url = f'{search_url}/search/{cas_num}?focus=products&page=1&perpage=30&sort=relevance&term={cas_num}&type=product'

try:
    response = requests.Session(product_url)  # 设置5秒超时
    html_content = response.text
except requests.Timeout:
    print("请求超时")
except requests.RequestException as e:
    print(f"请求出错: {e}")

# 使用BeautifulSoup解析HTML
soup = BeautifulSoup(html_content, 'lxml')

# 查找所有包含商品ID的链接
product_links = soup.find_all('a', attrs={'data-testid': True})

# 提取商品ID
product_ids = []
for link in product_links:
    test_id = link['data-testid']
    # 假设商品ID总是在'data-testid'值的最后一部分
    product_id = test_id.split('-')[-2]
    print(product_id)
    product_ids.append(product_id)

# 打印商品ID列表
print(product_ids)


