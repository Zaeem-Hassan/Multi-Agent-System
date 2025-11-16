# agents/summarizer_agent.py

import os
import requests

class SummaryAgent:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.model = model

    def run(self, text: str) -> dict:
        if not text:
            return {"status": "failed", "error": "No text to summarize"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": f"Summarize the following text into clear bullet points:\n\n{text}"
                }
            ],
            "temperature": 0.2,
            "max_completion_tokens": 500
        }

        try:
            response = requests.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            # According to docs: {"choices": [{"index":0, "message": {"role":"assistant","content": "..."} }]}
            summary = result["choices"][0]["message"]["content"]
            return {"status": "success", "data": {"summary": summary}}
        except requests.exceptions.HTTPError as e:
            print("[SummaryAgent] API response:", e.response.text)
            return {"status": "failed", "error": str(e)}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
