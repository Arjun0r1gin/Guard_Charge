import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Session:
    charger_id: int
    port: str
    scenario: str
    start_time: float = field(default_factory=time.time)
    score: Optional[int] = None
    status: Optional[str] = None
    action: Optional[str] = None
    explanation: Optional[str] = None
    hard_blocked: bool = False

    def duration_seconds(self) -> float:
        return round(time.time() - self.start_time, 2)

    def is_safe(self) -> bool:
        return self.status == "VERIFIED"

    def summary(self) -> str:
        lines = [
            f"  Charger ID    : {self.charger_id}",
            f"  Port          : {self.port}",
            f"  Scenario      : {self.scenario}",
            f"  Duration      : {self.duration_seconds()}s",
            f"  Trust Score   : {self.score}/100",
            f"  Status        : {self.status}",
            f"  Action        : {self.action}",
            f"  Hard Blocked  : {self.hard_blocked}",
            f"  Explanation   :",
        ]
        if self.explanation:
            for line in self.explanation.split("\n"):
                lines.append(f"    {line}")
        return "\n".join(lines)


class SessionManager:
    def __init__(self):
        self.history: list[Session] = []
        self.active: Optional[Session] = None

    def start(self, charger_id: int, port: str, scenario: str) -> Session:
        self.active = Session(charger_id=charger_id, port=port, scenario=scenario)
        return self.active

    def complete(self, score: int, status: str, action: str,
                 explanation: str, hard_blocked: bool):
        if self.active:
            self.active.score = score
            self.active.status = status
            self.active.action = action
            self.active.explanation = explanation
            self.active.hard_blocked = hard_blocked
            self.history.append(self.active)
            self.active = None

    def print_history(self):
        if not self.history:
            print("  No sessions recorded yet.")
            return
        for i, s in enumerate(self.history, 1):
            print(f"\n  Session {i}:")
            print(s.summary())