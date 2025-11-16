# 🤖 Multi-Agent System — Automated Research & Summarization Pipeline  
<img src="ChatGPT Image Nov 16, 2025, 06_02_28 PM.png"  width="1536" height="1024">

This is an **AI-powered Multi-Agent System** that takes a user query, searches the web, extracts useful information, summarizes it using an LLM, and returns a clean structured report — with PDF download support.

Built using **SerpAPI**, **BeautifulSoup**, **Groq LLM**, and **Streamlit**, this project demonstrates how agents can collaborate to perform complex research tasks automatically.

---

## 🚀 Core Features

✅ **Browser Agent (SerpAPI)** → finds relevant articles & snippets  
✅ **Extraction Agent (BeautifulSoup)** → extracts text & metrics from webpages  
✅ **Summarizer Agent (Groq LLM)** → generates a concise and clean summary  
✅ **Streamlit UI** with loading animation + agent thinking steps  
✅ **PDF Download Button** to export the final report  
✅ **Clear modular multi-agent design**  
✅ **FastAPI Backend + Streamlit Frontend**

---

## 🧠 Multi-Agent Workflow
```bash
User Query
↓
🌐 Browser Agent (SerpAPI)
→ Searches Google
→ Retrieves URLs + snippets
↓
🧪 Extraction Agent (BeautifulSoup)
→ Fetches article HTML
→ Extracts important text, headings, metrics
↓
📝 Summarizer Agent (Groq LLM)
→ Creates structured, short, clean summary
→ Generates final report
```
---

## 🛠 Tech Stack

- **Frontend / UI:** Streamlit  
- **Backend:** FastAPI  
- **Search Engine:** SerpAPI  
- **Scraper:** BeautifulSoup4  
- **LLM:** Groq API (Mixtral / Llama models)  
- **PDF Generator:** ReportLab / FPDF  
- **Environment:** Python 3.10+  

---

## 📂 Project Structure
```bash
📁 Multi-Agent-System
browser_agent.py
extraction_agent.py
summarizer_agent.py
main.py
report_generator.py
helpers.py
streamlit_app.py
requirements.txt
README.md
```


---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Zaeem-Hassan/Multi-Agent-System.git
cd Multi-Agent-System
```
### 2️⃣ Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```
### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
