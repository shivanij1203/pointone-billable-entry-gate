from app.gate import ReleaseGate, ReleaseStore
from app.models import Activity, BillingRule, TimeEntry


RULES = [
    BillingRule(
        "narrative-detail",
        "the narrative must describe the substantive task",
        required_phrase="reviewed contract",
    ),
    BillingRule(
        "no-internal-tool",
        "internal billing tools cannot appear in the narrative",
        blocked_phrase="billing system",
    ),
]


def show(name, entry, activity, rules=RULES):
    result = ReleaseGate().check(entry, activity, rules)
    print(f"\n{name}")
    print(f"  decision: {result.decision.value}")
    for reason in result.reasons:
        print(f"  - {reason}")


def main():
    show(
        "clean entry",
        TimeEntry("e1", "matter-a", 30, "Reviewed contract and discussed changes", "passed"),
        [Activity("email", "sent comments", "matter-a"), Activity("document", "contract.docx", "matter-a")],
    )

    show(
        "ambiguous matter",
        TimeEntry("e2", "matter-a", 30, "Reviewed contract and discussed changes", "passed"),
        [Activity("email", "Acme", "matter-a"), Activity("email", "Acme", "matter-b")],
    )

    show(
        "compliance not checked",
        TimeEntry("e3", "matter-a", 30, "Reviewed contract and discussed changes", "not_checked"),
        [Activity("document", "contract.docx", "matter-a")],
    )

    show(
        "blocked by rule",
        TimeEntry("e4", "matter-a", 30, "Reviewed contract in the billing system", "passed"),
        [Activity("document", "contract.docx", "matter-a")],
    )

    show(
        "missing evidence",
        TimeEntry("e5", "matter-a", 30, "Reviewed contract and discussed changes", "passed"),
        [Activity("email", "different matter", "matter-b")],
    )

    store = ReleaseStore()
    item = TimeEntry("e6", "matter-a", 30, "Reviewed contract and discussed changes", "passed")
    activity = [Activity("document", "contract.docx", "matter-a")]
    first = store.release(item, activity, RULES, "request-1")
    second = store.release(item, activity, RULES, "request-2")
    print("\nrepeat release")
    print(f"  first: {first.decision.value}")
    print(f"  retry: {second.reasons[0]}")


if __name__ == "__main__":
    main()
