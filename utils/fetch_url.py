import trafilatura
from playwright.sync_api import sync_playwright


def fetch_url_content_local(url: str) -> str:
    """
    本地实现的网页抓取工具。
    使用无头浏览器加载网页，并提取正文转换为Markdown。
    """
    try:
        # 1. 启动无头浏览器 (Playwright)
        with sync_playwright() as p:
            # 启动 Chromium，headless=True 表示不显示界面
            browser = p.chromium.launch(headless=True)

            # 创建上下文，设置 User-Agent 伪装成普通用户，防止被反爬
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            # 2. 访问网页
            # wait_until='domcontentloaded' 比 'networkidle' 快，通常足够拿到正文
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # 获取渲染后的完整 HTML
            html_content = page.content()

            browser.close()

        # 3. 智能提取正文 (Trafilatura)
        # include_links=True 保留文章内的链接，对科研很有用
        # include_images=False 通常设为 False 以减少 LLM token 消耗
        text_content = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=True,
            include_links=True,
            output_format="markdown" # 直接输出 Markdown
        )

        if text_content:
            return text_content
        else:
            return "Error: 无法从该网页提取到有效正文，可能是纯图片网页或受严密保护。"

    except Exception as e:
        return f"Error fetching URL: {str(e)}"

# --- 测试一下 ---
if __name__ == "__main__":
    # 测试抓取一篇 arXiv 论文的 HTML 页面或一篇新闻
    url = "https://arxiv.org/abs/2310.06825" # 示例
    print(fetch_url_content_local(url))
