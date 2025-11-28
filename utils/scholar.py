
import requests
import xmltodict

# ================= 代码测试配置区域 =================
# 你的 Cloudflare Worker 地址
WORKER_URL = ""

# 等收到邮件后，把 Key 填在这里
# 没收到前先留 None，代码也能跑，只是 Semantic Scholar 容易报错
S2_API_KEY = None
# ===========================================

class AcademicBaseTool:
    def __init__(self, proxy_base_url: str, api_key: str | None = None):
        self.proxy_base_url = proxy_base_url.rstrip("/")
        self.headers = {"User-Agent": "Academic-Project-Bot/1.0"}
        if api_key:
            self.headers["x-api-key"] = api_key

class SemanticScholarTool(AcademicBaseTool):
    def search(self, query: str, limit: int = 3) -> list[dict]:
        endpoint = f"{self.proxy_base_url}/s2/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,abstract,year,authors,openAccessPdf"
        }
        try:
            # 这里的 timeout 设长一点，防止 Worker 冷启动
            resp = requests.get(endpoint, params=params, headers=self.headers, timeout=20)

            if resp.status_code == 429:
                return [{"error": "请求太快被限制了 (等待 API Key 中...)"}]

            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("data", []):
                results.append({
                    "source": "Semantic Scholar",
                    "title": item.get("title"),
                    "year": item.get("year"),
                    "abstract": (item.get("abstract") or "无摘要")[:150] + "...",
                    "pdf_url": item.get("openAccessPdf", {}).get("url") if item.get("openAccessPdf") else None
                })
            return results
        except Exception as e:
            return [{"error": f"S2 Error: {str(e)}"}]

class ArxivTool(AcademicBaseTool):
    def search(self, query: str, max_results: int = 3) -> list[dict]:
        endpoint = f"{self.proxy_base_url}/arxiv/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results
        }
        try:
            resp = requests.get(endpoint, params=params, headers=self.headers, timeout=20)
            resp.raise_for_status()
            data = xmltodict.parse(resp.content)
            entries = data.get("feed", {}).get("entry", [])
            if isinstance(entries, dict):
                entries = [entries]

            results = []
            for entry in entries:
                results.append({
                    "source": "ArXiv",
                    "title": entry.get("title", "").replace("\n", "").strip(),
                    "date": entry.get("published", "")[:10],
                    "abstract": entry.get("summary", "").replace("\n", " ")[:150] + "...",
                    "pdf_url": entry.get("id", "").replace("abs", "pdf")
                })
            return results
        except Exception as e:
            return [{"error": f"ArXiv Error: {str(e)}"}]

# --- 测试运行 ---
if __name__ == "__main__":
    # 1. 测试 ArXiv (应该 100% 成功)
    print("\n>>> Testing ArXiv (No Key required)...")
    arxiv = ArxivTool(WORKER_URL)
    results = arxiv.search("LLM Agents")
    for r in results:
        print(f"[√] {r.get('title')}")

    # 2. 测试 Semantic Scholar (没 Key 可能会 429，但也可能成功)
    print("\n>>> Testing Semantic Scholar...")
    s2 = SemanticScholarTool(WORKER_URL, api_key=S2_API_KEY)
    results = s2.search("LLM Agents")
    print(results)
