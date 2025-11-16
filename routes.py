# backend/api/routes.py
from fastapi import APIRouter, HTTPException
from orchestrator.workflow_manager import WorkflowManager

router = APIRouter()
manager = WorkflowManager()

@router.post("/run-workflow")
async def run_workflow(payload: dict):
    """
    Example payload:
    {
      "workflow": [
        {"agent": "browser", "input": {"urls": ["https://example.com"]}}
      ]
    }
    """
    job = manager.start_workflow(payload)
    return {"job_id": job["id"], "status": "started"}

@router.get("/job/{job_id}")
async def get_job(job_id: str):
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
