# backend/orchestrator/workflow_manager.py
import uuid
import time
from typing import Dict, List
from agents.browser_agent import BrowserAgentStub

class WorkflowManager:
    def __init__(self):
        self.jobs: Dict[str, dict] = {}
        # map agents available
        self._agents = {
            "browser": BrowserAgentStub()
        }

    def start_workflow(self, payload: dict) -> dict:
        job_id = str(uuid.uuid4())
        job = {"id": job_id, "status": "running", "payload": payload, "logs": [], "result": None}
        self.jobs[job_id] = job
        # For M1 we run synchronously and sequentially
        try:
            steps: List[dict] = payload.get("workflow", [])
            step_results = []
            for i, step in enumerate(steps):
                agent_name = step.get("agent")
                inp = step.get("input", {})
                job["logs"].append({"ts": time.time(), "info": f"Starting step {i+1} using agent {agent_name}"})
                agent = self._agents.get(agent_name)
                if not agent:
                    job["logs"].append({"ts": time.time(), "error": f"Agent {agent_name} not found"})
                    job["status"] = "failed"
                    break
                # run agent
                res = agent.run(inp)
                job["logs"].append({"ts": time.time(), "info": f"Step {i+1} result: {res.get('status')}"})
                step_results.append(res)
            else:
                job["status"] = "finished"
                job["result"] = step_results
        except Exception as e:
            job["status"] = "failed"
            job["logs"].append({"ts": time.time(), "error": str(e)})
        return job

    def get_job(self, job_id: str):
        return self.jobs.get(job_id)
