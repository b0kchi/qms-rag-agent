from abc import ABC, abstractmethod
from sqlmodel import Session
from app.agents.state import AgentState, RetrievalResult


class Strategy(ABC):
    key: str

    @abstractmethod
    def run(self, session: Session, state: AgentState, **kwargs) -> RetrievalResult:
        raise NotImplementedError