# agents/extractor_agent.py
from bs4 import BeautifulSoup
import re
import requests

class ExtractorAgent:
    def clean_text(self, text: str) -> str:
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n+", "\n", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        return text.strip()

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "header", "footer", "nav", "noscript"]):
            tag.extract()
        text = soup.get_text(separator="\n")
        return self.clean_text(text)

    def run(self, url: str) -> dict:
        if not url:
            return {"status": "failed", "error": "No URL provided"}

        try:
            res = requests.get(url, timeout=10)
            html = res.text
        except Exception as e:
            return {"status": "failed", "error": f"Failed to fetch URL: {e}"}

        clean = self.extract_text(html)
        return {"status": "success", "data": {"clean_text": clean}}
