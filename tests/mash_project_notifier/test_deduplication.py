from automation.mash_project_notifier.deduplication import (
    STATE_MARKER,
    decode_state,
    encode_state,
    event_marker,
)


def test_state_round_trip_uses_hidden_stable_marker():
    state = {
        "version": 1,
        "items": {"item-34": {"status_id": "done", "sprint": "Sprint 2"}},
        "sent_keys": ["task_done:item-34:ready:done"],
    }

    body = encode_state(state)
    decoded = decode_state(body)

    assert STATE_MARKER in body
    assert decoded == state


def test_event_marker_is_deterministic_and_searchable():
    marker = event_marker("sprint_started:Sprint 3:2026-09-16")

    assert marker == "<!-- mash-notifier:event:sprint_started:Sprint 3:2026-09-16 -->"
