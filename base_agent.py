# backend/agents/base_agent.py
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def run(self, payload: dict) -> dict:
        """
        Run the agent. Must return a dict:
        { "status": "success|failed", "data": {...}, "meta": {...} }
        """
        raise NotImplementedError
