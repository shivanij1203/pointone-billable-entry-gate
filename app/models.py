from dataclasses import dataclass, field
from enum import Enum


class Decision(str, Enum):
    READY = "ready"
    REVIEW = "review"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Activity:
    kind: str
    text: str
    matter_id: str | None = None


@dataclass(frozen=True)
class TimeEntry:
    entry_id: str
    matter_id: str | None
    minutes: int
    narrative: str
    compliance: str
    evidence_version: int = 1
    rules_version: int = 1


@dataclass(frozen=True)
class BillingRule:
    rule_id: str
    description: str
    required_phrase: str | None = None
    blocked_phrase: str | None = None


@dataclass(frozen=True)
class GateResult:
    decision: Decision
    reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DecisionRecord:
    entry_id: str
    request_id: str
    decision: Decision
    evidence_version: int
    rules_version: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseRecord:
    entry_id: str
    request_id: str
    decision: Decision
