# agents/reporter_agent.py
class ReporterAgent:
    def run(self, url: str, summary: str) -> dict:
        if not summary:
            return {"status": "failed", "error": "No summary provided"}
        report_text = f"📄 REPORT\nURL: {url}\n\nSummary:\n{summary}"
        return {"status": "success", "data": {"report": report_text}}
