from collections import Counter

from .models import (
    Activity,
    BillingRule,
    Decision,
    DecisionRecord,
    GateResult,
    ReleaseRecord,
    TimeEntry,
)


class ReleaseGate:
    """Check whether a staged entry is ready to cross the release boundary."""

    def check(
        self,
        entry: TimeEntry,
        activity: list[Activity],
        rules: list[BillingRule],
    ) -> GateResult:
        reasons: list[str] = []
        evidence: list[str] = []

        if not activity:
            return GateResult(
                Decision.REVIEW,
                ("There is no activity evidence for this entry.",),
            )

        if not entry.matter_id:
            return GateResult(
                Decision.REVIEW,
                ("The entry does not have a resolved matter.",),
            )

        matching = [item for item in activity if item.matter_id == entry.matter_id]
        counts = Counter(item.matter_id for item in activity if item.matter_id)

        if not matching:
            reasons.append("No activity points to the selected matter.")
        else:
            evidence.extend(f"{item.kind}: {item.text}" for item in matching)

        if len(counts) > 1:
            highest = max(counts.values())
            leaders = [matter for matter, count in counts.items() if count == highest]
            if len(leaders) > 1:
                reasons.append("Activity points to more than one equally supported matter.")

        if entry.compliance == "not_checked":
            reasons.append("Compliance has not been checked yet.")
        elif entry.compliance == "failed":
            reasons.append("The entry failed a billing rule.")

        if not entry.narrative.strip():
            reasons.append("The entry has no narrative.")

        for rule in rules:
            if rule.required_phrase and rule.required_phrase.lower() not in entry.narrative.lower():
                reasons.append(f"Missing required detail: {rule.description}")
            if rule.blocked_phrase and rule.blocked_phrase.lower() in entry.narrative.lower():
                reasons.append(f"Blocked detail found: {rule.description}")

        if entry.minutes <= 0:
            reasons.append("The entry has no positive duration.")

        if reasons:
            blocking_prefixes = (
                "Compliance has not",
                "The entry failed",
                "Missing required",
                "Blocked detail",
                "The entry has no",
            )
            decision = (
                Decision.BLOCKED
                if any(reason.startswith(blocking_prefixes) for reason in reasons)
                else Decision.REVIEW
            )
            return GateResult(decision, tuple(reasons), tuple(evidence))

        return GateResult(
            Decision.READY,
            ("Evidence and required checks are present.",),
            tuple(evidence),
        )


class ReleaseStore:
    """In-memory stand-in for the records a durable release service would keep."""

    def __init__(self) -> None:
        self._decisions: dict[tuple[str, str], DecisionRecord] = {}
        self._released: dict[str, ReleaseRecord] = {}

    def release(
        self,
        entry: TimeEntry,
        activity: list[Activity],
        rules: list[BillingRule],
        request_id: str,
        gate: ReleaseGate | None = None,
    ) -> DecisionRecord:
        key = (entry.entry_id, request_id)
        previous = self._decisions.get(key)
        if previous is not None:
            return previous

        existing_release = self._released.get(entry.entry_id)
        if existing_release is not None:
            record = DecisionRecord(
                entry.entry_id,
                request_id,
                Decision.READY,
                entry.evidence_version,
                entry.rules_version,
                ("Entry was already released; no second release was created.",),
            )
            self._decisions[key] = record
            return record

        gate = gate or ReleaseGate()
        result = gate.check(entry, activity, rules)
        record = DecisionRecord(
            entry.entry_id,
            request_id,
            result.decision,
            entry.evidence_version,
            entry.rules_version,
            result.reasons,
        )
        self._decisions[key] = record

        if result.decision == Decision.READY:
            self._released[entry.entry_id] = ReleaseRecord(
                entry.entry_id,
                request_id,
                result.decision,
            )

        return record
