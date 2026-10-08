# Billable entry release gate

I was looking at the gap between an AI-generated time entry and a time entry that is safe to release for billing.

A good-looking entry is not necessarily a safe one. The matter can be ambiguous, a billing check may not have happened yet, or the entry can violate a client rule.

So this is a small experiment around one boundary:

```text
activity -> candidate entry -> checks -> ready / review / blocked -> release
```

The data is synthetic. This is not a PointOne integration or a copy of its product.

## What I wanted to test

The component that creates a suggestion should not get to decide by itself that the suggestion is ready for billing.

The gate checks separately:

- whether activity supports the selected matter
- whether another matter is equally plausible
- whether compliance has actually been checked
- whether the entry satisfies the billing rules in the test data
- whether the entry has a real duration and narrative

The release store calls the gate before recording a release. A repeated request replays the first decision, and a different request cannot create a second release for the same entry.

Each decision records the evidence/rules versions used to make it. That is a small stand-in for keeping enough history to explain an old decision after the underlying data changes.

## Failure cases

The tests cover:

- clean evidence
- ambiguous matter
- missing matter evidence
- compliance not checked
- failed compliance
- billing rule violation
- empty activity
- retrying the same request
- trying to bypass the gate
- trying to release an already released entry

The result keeps the reason instead of returning only a boolean. That makes the boundary easier to inspect when a person needs to review it.

## Run it

```bash
python -m pytest -q
python run_lab.py
```

## What this leaves out

Everything is in memory and the rule model is intentionally tiny. A production version would need durable state, versioned evidence and rules, an append-only decision history, and reconciliation around the external billing system.

I would also want decisions to be replayable. If the rules or evidence change, a new evaluation should produce a new decision rather than silently rewriting the old one.
