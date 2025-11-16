import os
import serpapi
import requests
from bs4 import BeautifulSoup

class BrowserAgent:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY not set in environment")

        # Initialize SerpAPI client
        self.client = serpapi.Client(api_key=self.api_key)

    def run(self, query: str) -> dict:
        """
        Step 1: Search Google using SerpAPI
        Step 2: Return top result URL + snippet
        Step 3: Scrape full article text
        """

        # SERPAPI SEARCH
        try:
            result = self.client.search({"engine": "google", "q": query})
        except Exception as e:
            return {"status": "failed", "error": f"SerpAPI error: {e}"}

        organic = result.get("organic_results", [])
        if not organic:
            return {"status": "failed", "error": "No organic search results found"}

        first = organic[0]
        url = first.get("link")
        snippet = first.get("snippet", "")

        # SCRAPE WEBSITE
        full_text = ""
        try:
            res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(res.text, "html.parser")

            paragraphs = soup.find_all("p")
            clean_text = [
                p.get_text(strip=True)
                for p in paragraphs if p.get_text(strip=True)
            ]

            full_text = "\n\n".join(clean_text) if clean_text else "No readable content found."

        except Exception as e:
            full_text = f"Scraping failed: {e}"

        return {
            "status": "success",
            "data": {
                "url": url,
                "snippet": snippet,
                "full_text": full_text,
            }
        }
