import os
import urllib3
from atlassian import Confluence

# 禁用银行内网因自签证书引起的 HTTPS 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. 初始化连接
# 注意：银行内网通常使用个人访问令牌(PAT)或域账号。
# 如果用 Token，把 Token 填在 password 位置，同时 username 留空或填你账号。
CONFLUENCE_URL = "https://alm-confluence.YOUR_BANK_DOMAIN.com"  # 替换为你们的内部URL
USERNAME = "your_username"
PASSWORD = "your_password_or_PAT_token"

print("正在连接 Confluence...")
confluence = Confluence(
    url=CONFLUENCE_URL,
    username=USERNAME,
    password=PASSWORD,
    verify_ssl=False  # 很多银行内部是自签证书，设为 False 规避 SSL 报错
)

def fetch_all_pages_by_space(space_key):
    """
    模式 A：如果 cc 把内容放在一个独立的 Space 里，用这个函数抓取全部页面
    """
    all_pages = []
    start = 0
    limit = 50  # 每次抓取50条
    
    print(f"开始抓取 Space: {space_key} 下的所有内容...")
    while True:
        # expand='body.storage' 是为了拿到页面的原始 HTML/XHTML 内容
        pages = confluence.get_all_pages_from_space(
            space=space_key, 
            start=start, 
            limit=limit, 
            expand='body.storage'
        )
        
        if not pages:
            break
            
        all_pages.extend(pages)
        print(f"已获取 {len(all_pages)} 个页面...")
        
        if len(pages) < limit:
            break  # 说明没有下一页了
        start += limit
        
    return all_pages

def fetch_child_pages_recursively(parent_page_id):
    """
    模式 B：如果 cc 是在现有 Space 的某一个主页（Parent Page）下建的分类目录，
    用这个函数递归抓取所有子页面。
    """
    all_pages = []
    
    def _dfs(page_id):
        start = 0
        limit = 50
        while True:
            # 或者是 get_page_child_by_type
            children = confluence.get_page_child_by_type(
                page_id=page_id, 
                type='page', 
                start=start, 
                limit=limit, 
                expand='body.storage'
            )
            if not children:
                break
                
            for child in children:
                all_pages.append(child)
                # 递归查找子页面的子页面
                _dfs(child['id'])
                
            if len(children) < limit:
                break
            start += limit

    print(f"开始从父页面 ID: {parent_page_id} 递归抓取...")
    _dfs(parent_page_id)
    return all_pages

# ==================== 测试运行 ====================
if __name__ == "__main__":
    # TODO: 选择其中一种模式测试。
    # 模式 A 测试 (需要 Space Key，比如 'PAYCTRL'):
    # pages_data = fetch_all_pages_by_space("YOUR_SPACE_KEY")
    
    # 模式 B 测试 (如果你知道 cc 建的那个最上层页面的 Page ID):
    # 你可以从 Confluence 页面的 URL 中找到 pageId=XXXXXX
    PARENT_ID = "12345678"  # 替换为实际的 Page ID
    pages_data = fetch_child_pages_recursively(PARENT_ID)
    
    print(f"\n成功抓取完毕！共获取到 {len(pages_data)} 个页面。")
    
    # 打印前2个页面的标题和部分内容进行验证
    for i, page in enumerate(pages_data[:2]):
        title = page['title']
        # body.storage.value 拿出来的是包含 HTML 标签的纯文本
        raw_html = page.get('body', {}).get('storage', {}).get('value', '')
        print(f"\n--- 页面 {i+1}: {title} ---")
        print(raw_html[:200] + "... (截断)")