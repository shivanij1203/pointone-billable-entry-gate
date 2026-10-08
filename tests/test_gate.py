from app.gate import ReleaseGate, ReleaseStore
from app.models import Activity, BillingRule, Decision, TimeEntry


RULES = [
    BillingRule(
        "detail",
        "the narrative must describe the substantive task",
        required_phrase="reviewed contract",
    ),
    BillingRule(
        "internal",
        "internal billing tools cannot appear",
        blocked_phrase="billing system",
    ),
]


def check(entry, activity, rules=RULES):
    return ReleaseGate().check(entry, activity, rules)


def entry(entry_id="1", **changes):
    values = dict(
        entry_id=entry_id,
        matter_id="a",
        minutes=30,
        narrative="Reviewed contract and discussed changes",
        compliance="passed",
    )
    values.update(changes)
    return TimeEntry(**values)


def test_clean_entry_is_ready():
    result = check(entry(), [Activity("document", "contract.docx", "a")])
    assert result.decision == Decision.READY


def test_equal_matter_support_requires_review():
    result = check(
        entry("2"),
        [Activity("email", "Acme", "a"), Activity("email", "Acme", "b")],
    )
    assert result.decision == Decision.REVIEW


def test_missing_matter_support_requires_review():
    result = check(entry("3"), [Activity("document", "contract.docx", "b")])
    assert result.decision == Decision.REVIEW


def test_unchecked_compliance_blocks_release():
    result = check(entry("4", compliance="not_checked"), [Activity("document", "contract.docx", "a")])
    assert result.decision == Decision.BLOCKED


def test_failed_compliance_blocks_release():
    result = check(entry("5", compliance="failed"), [Activity("document", "contract.docx", "a")])
    assert result.decision == Decision.BLOCKED


def test_rule_violation_blocks_release():
    result = check(
        entry("6", narrative="Reviewed contract in the billing system"),
        [Activity("document", "contract.docx", "a")],
    )
    assert result.decision == Decision.BLOCKED


def test_empty_activity_requires_review():
    result = check(entry("7"), [])
    assert result.decision == Decision.REVIEW


def test_release_replays_same_request():
    store = ReleaseStore()
    item = entry("8")
    first = store.release(item, [Activity("document", "contract.docx", "a")], RULES, "request-1")
    second = store.release(item, [Activity("document", "contract.docx", "a")], RULES, "request-1")
    assert first == second
    assert first.decision == Decision.READY


def test_release_does_not_bypass_gate():
    store = ReleaseStore()
    item = entry("9", compliance="not_checked")
    result = store.release(item, [Activity("document", "contract.docx", "a")], RULES, "request-1")
    assert result.decision == Decision.BLOCKED


def test_second_request_cannot_release_same_entry_twice():
    store = ReleaseStore()
    item = entry("10")
    first = store.release(item, [Activity("document", "contract.docx", "a")], RULES, "request-1")
    second = store.release(item, [Activity("document", "contract.docx", "a")], RULES, "request-2")
    assert first.decision == Decision.READY
    assert second.decision == Decision.READY
    assert "already released" in second.reasons[0]
