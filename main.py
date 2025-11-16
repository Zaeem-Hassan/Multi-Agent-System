from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agents.browser_agent import BrowserAgent
import uvicorn
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

app = FastAPI()

# Enable CORS so Streamlit can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize browser agent
try:
    agent = BrowserAgent()
except Exception as e:
    print("Error initializing BrowserAgent:", e)
    agent = None


class QueryRequest(BaseModel):
    query: str


@app.get("/")
def root():
    return {"message": "Backend is running!"}


@app.post("/run")
async def run_query(request: QueryRequest):
    if agent is None:
        return {"detail": "BrowserAgent not initialized on server"}

    response = agent.run(request.query)
    return {"response": response}


# Start server
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
