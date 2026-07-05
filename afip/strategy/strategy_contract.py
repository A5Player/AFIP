from typing import Protocol

class StrategyContract(Protocol):
    name: str

    def evaluate(self, snapshot: dict) -> dict:
        ...
