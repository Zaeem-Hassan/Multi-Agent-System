# pro_orchestrator.py
"""
Pro Orchestrator for multi-agent workflows.

Usage:
- register agents with `orchestrator.register_agent("name", agent_instance)`
- start a workflow with `await orchestrator.start_workflow(workflow_payload)`
- poll job state with `orchestrator.get_job(job_id)` or `orchestrator.list_jobs()`

Workflow payload example:
{
  "id": "optional-id",
  "steps": [
    {"name":"search", "agent":"browser", "input":{"query":"latest AI research"}, "retry":3, "timeout":30},
    {"name":"extract", "agent":"extractor", "input_path":"previous.steps.0.data.html", "retry":2},
    {"name":"summarize", "agent":"summarizer", "input_path":"previous.steps.1.data.clean_text", "retry":2, "timeout":20},
    {"name":"report", "agent":"reporter", "input_path":"previous.steps.2.data.summary"}
  ],
  "metadata": {"requested_by":"you@example.com"}
}
"""
from __future__ import annotations
import asyncio
import time
import uuid
import traceback
from typing import Any, Dict, List, Optional

def now_ts() -> float:
    return time.time()

class Orchestrator:
    def __init__(self):
        # name -> agent instance
        self.agents: Dict[str, Any] = {}
        # in-memory jobs store
        self.jobs: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    def register_agent(self, name: str, agent: Any):
        """Register an agent instance under a name (string)."""
        self.agents[name] = agent

    def _resolve_input(self, step: dict, job: dict) -> dict:
        """
        Resolve input for a step.
        Supports:
          - step["input"] (explicit dict)
          - step["input_path"] referencing previous steps like:
            "previous.steps.0.data.clean_text"
        Returns a dict that will be passed as payload to agent.
        """
        base = dict(step.get("input") or {})
        input_path = step.get("input_path")
        if not input_path:
            return base

        # Only handle simple "previous.steps.<i>.data.<key>" patterns
        try:
            if input_path.startswith("previous."):
                parts = input_path.split(".")
                # expected: previous, steps, <idx>, data, <key1>, <key2>...
                if len(parts) >= 5 and parts[1] == "steps" and parts[3] == "data":
                    idx = int(parts[2])
                    rest = parts[4:]
                    prev_result = job.get("result", [])[idx] if idx < len(job.get("result", [])) else None
                    if prev_result:
                        val = prev_result.get("data") or {}
                        for p in rest:
                            if isinstance(val, dict):
                                val = val.get(p)
                            else:
                                val = None
                        base["_from_previous"] = val
                        return base
        except Exception:
            # on any error, return base as-is and let agent handle missing data
            return base

        return base

    async def _call_agent(self, agent_name: str, payload: dict, timeout: Optional[int] = None) -> dict:
        """
        Call a registered agent. Agent may expose:
         - async method `arun(payload: dict)` OR
         - sync method `run(payload: dict)`

        If agent doesn't exist or throws, returns {"status":"failed", "error": ...}
        """
        agent = self.agents.get(agent_name)
        if agent is None:
            return {"status": "failed", "error": f"agent '{agent_name}' not registered"}

        async def _invoke():
            try:
                # prefer asynchronous method if available
                if hasattr(agent, "arun") and asyncio.iscoroutinefunction(getattr(agent, "arun")):
                    return await agent.arun(payload)
                elif hasattr(agent, "run") and asyncio.iscoroutinefunction(getattr(agent, "run")):
                    return await agent.run(payload)  # uncommon: async run
                elif hasattr(agent, "run"):
                    # sync run -> run in executor to avoid blocking event loop
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, agent.run, payload)
                else:
                    return {"status": "failed", "error": "agent has no run/arun method"}
            except Exception as e:
                tb = traceback.format_exc()
                return {"status": "failed", "error": str(e), "traceback": tb}

        if timeout:
            try:
                return await asyncio.wait_for(_invoke(), timeout=timeout)
            except asyncio.TimeoutError:
                return {"status": "failed", "error": "timeout"}
        else:
            return await _invoke()

    async def _run_step(self, job: dict, step_idx: int, step: dict) -> dict:
        """
        Run a single step with retry, logging, and record history.
        Step fields:
          - name (optional)
          - agent (required)
          - input (dict) or input_path (string)
          - retry (int, default 1)
          - timeout (int seconds, optional)
        Returns a dict with {"status":"success"/"failed", "data":...}
        """
        name = step.get("name") or f"step_{step_idx}"
        agent_name = step.get("agent")
        retries = int(step.get("retry", 1))
        timeout = step.get("timeout")

        attempt = 0
        last_err = None

        while attempt < retries:
            attempt += 1
            ts_start = now_ts()
            job["logs"].append({"ts": ts_start, "level": "info", "msg": f"Starting {name} (agent={agent_name}) attempt {attempt}"})

            resolved_payload = self._resolve_input(step, job)

            result = await self._call_agent(agent_name, resolved_payload, timeout=timeout)

            ts_end = now_ts()
            duration = ts_end - ts_start

            step_entry = {
                "name": name,
                "agent": agent_name,
                "attempt": attempt,
                "ts_start": ts_start,
                "ts_end": ts_end,
                "duration": duration,
                "result": result
            }

            job["agent_history"].append(step_entry)
            job["logs"].append({"ts": now_ts(), "level": "info", "msg": f"Finished {name} attempt {attempt} status={result.get('status', 'unknown')}"})

            # success condition - agent should return dict with status: "success"
            if isinstance(result, dict) and result.get("status") == "success":
                # standardize returned data to be under "data"
                return {"status": "success", "data": result.get("data", result)}
            else:
                last_err = result
                job["logs"].append({"ts": now_ts(), "level": "warning", "msg": f"{name} attempt {attempt} failed: {result.get('error') if isinstance(result, dict) else str(result)}"})
                # exponential backoff sleep
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

        # all retries exhausted
        return {"status": "failed", "error": last_err}

    async def start_workflow(self, payload: dict) -> dict:
        """
        Create a job and run workflow in background.
        Returns the job dict immediately (status will be 'running').
        """
        job_id = payload.get("id") or str(uuid.uuid4())
        job = {
            "id": job_id,
            "status": "running",
            "submitted_at": now_ts(),
            "payload": payload,
            "logs": [],
            "agent_history": [],
            "result": [],  # list of per-step structured results
        }

        async with self._lock:
            self.jobs[job_id] = job

        # fire-and-forget execution
        asyncio.create_task(self._execute_workflow(job_id))
        return job

    async def _execute_workflow(self, job_id: str):
        # fetch job
        async with self._lock:
            job = self.jobs.get(job_id)
        if not job:
            return

        steps = job["payload"].get("steps", [])

        for idx, step in enumerate(steps):
            step_resp = await self._run_step(job, idx, step)
            # append standardized step result
            job["result"].append({"status": step_resp.get("status"), "data": step_resp.get("data")})

            if step_resp.get("status") != "success":
                job["status"] = "failed"
                job["finished_at"] = now_ts()
                job["logs"].append({"ts": now_ts(), "level": "error", "msg": f"Workflow failed at step {idx} ({step.get('name')})"})
                async with self._lock:
                    self.jobs[job_id] = job
                return

        job["status"] = "finished"
        job["finished_at"] = now_ts()
        job["logs"].append({"ts": now_ts(), "level": "info", "msg": "Workflow completed successfully"})
        async with self._lock:
            self.jobs[job_id] = job

    def get_job(self, job_id: str) -> Optional[dict]:
        return self.jobs.get(job_id)

    def list_jobs(self) -> List[dict]:
        return list(self.jobs.values())

# -------------------- Example integration & adapters --------------------
# The following snippet demonstrates how to register agents and run a workflow.
# Place your real agents in multi_agent_system/agents/ and import them here.
# If your agent's run signature does not accept a dict payload, create a small adapter.

if __name__ == "__main__":
    import asyncio
    # Example: import your agents (ensure python path includes project root)
    try:
        from agents.browser_agent import BrowserAgent
        from agents.extractor_agent import ExtractorAgent
        from agents.summarizer_agent import SummaryAgent
        from agents.reporter_agent import ReporterAgent
    except Exception:
        # If imports fail because file layout is different, fall back to simple stubs
        BrowserAgent = None
        ExtractorAgent = None
        SummaryAgent = None
        ReporterAgent = None

    # Adapter example: wrap an agent that expects positional args or a different signature
    class BrowserAdapter:
        def __init__(self, real_agent):
            self._a = real_agent
        def run(self, payload: dict):
            # if real_agent.run expects a single string query, adapt here:
            q = payload.get("query") or payload.get("_from_previous") or payload.get("text")
            return self._a.run(q)  # call original signature

    class ExtractorAdapter:
        def __init__(self, real_agent):
            self._a = real_agent
        def run(self, payload: dict):
            # real extractor might expect raw html string
            html = payload.get("_from_previous") or payload.get("html")
            return self._a.run(html)

    class SummarizerAdapter:
        def __init__(self, real_agent):
            self._a = real_agent
        async def arun(self, payload: dict):
            # if real agent has sync run, run in executor
            text = payload.get("_from_previous") or payload.get("clean_text")
            if hasattr(self._a, "run") and not asyncio.iscoroutinefunction(getattr(self._a, "run")):
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, self._a.run, text)
            elif hasattr(self._a, "arun"):
                return await self._a.arun(text)
            else:
                return {"status":"failed", "error":"unsupported summarizer signature"}

    class ReporterAdapter:
        def __init__(self, real_agent):
            self._a = real_agent
        def run(self, payload: dict):
            # reporter might want (url, summary) or just summary
            summary = payload.get("_from_previous") or payload.get("summary") or payload.get("text")
            url = payload.get("url") or payload.get("_from_previous_url")
            # attempt calling with two args if supported
            try:
                return self._a.run(url, summary)
            except TypeError:
                return self._a.run(summary)

    async def demo():
        orch = Orchestrator()

        # If you imported real agents, register them; else register simple stubs
        if BrowserAgent and ExtractorAgent and SummaryAgent and ReporterAgent:
            # wrap/adapt as needed so all agents accept dict payloads
            orch.register_agent("browser", BrowserAdapter(BrowserAgent()))
            orch.register_agent("extractor", ExtractorAdapter(ExtractorAgent()))
            orch.register_agent("summarizer", SummarizerAdapter(SummaryAgent()))
            orch.register_agent("reporter", ReporterAdapter(ReporterAgent()))
        else:
            # simple inline stubs (useful if you run this file standalone)
            class BrowserStub:
                def run(self, payload):
                    q = payload.get("query")
                    return {"status":"success", "data":{"html": f"<html><body>Results for {q}</body></html>", "url": f"https://example.com/search?q={q}"}}
            class ExtractorStub:
                def run(self, payload):
                    html = payload.get("_from_previous") or payload.get("html")
                    clean = html.replace("<html><body>", "").replace("</body></html>", "")
                    return {"status":"success", "data":{"clean_text": clean}}
            class SummarizerStub:
                async def arun(self, payload):
                    txt = payload.get("_from_previous") or payload.get("clean_text")
                    await asyncio.sleep(0.1)
                    return {"status":"success", "data":{"summary": f"Summary: {txt[:120]}"}}
            class ReporterStub:
                def run(self, payload):
                    s = payload.get("_from_previous") or payload.get("summary") or payload.get("clean_text")
                    return {"status":"success", "data":{"report": f"REPORT:\\n{s}"}}

            orch.register_agent("browser", BrowserStub())
            orch.register_agent("extractor", ExtractorStub())
            orch.register_agent("summarizer", SummarizerStub())
            orch.register_agent("reporter", ReporterStub())

        workflow = {
            "steps": [
                {"name": "search", "agent": "browser", "input": {"query": "latest AI research"}, "retry": 2, "timeout": 20},
                {"name": "extract", "agent": "extractor", "input_path": "previous.steps.0.data.html", "retry": 2},
                {"name": "summarize", "agent": "summarizer", "input_path": "previous.steps.1.data.clean_text", "retry": 2, "timeout": 20},
                {"name": "report", "agent": "reporter", "input_path": "previous.steps.2.data.summary", "retry": 1}
            ]
        }

        job = await orch.start_workflow(workflow)
        print("Started job:", job["id"])

        # poll until finished
        while True:
            j = orch.get_job(job["id"])
            print("JOB STATUS:", j["status"])
            if j["status"] in ("finished", "failed"):
                print("=== LOGS ===")
                for l in j["logs"]:
                    print(l)
                print("=== AGENT HISTORY ===")
                for h in j["agent_history"]:
                    print(h)
                print("=== RESULT ===")
                print(j["result"])
                break
            await asyncio.sleep(0.5)

    asyncio.run(demo())
