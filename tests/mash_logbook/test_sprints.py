from datetime import date

import pytest

from automation.mash_logbook import config, sprints
from automation.mash_project_notifier.github_client import GitHubAPIError


def payload(iterations=(), completed=(), sprint_fields=("Sprint",), configuration=True):
    fields = [{"name": "Status"}]
    for name in sprint_fields:
        field = {"name": name}
        if configuration:
            field["configuration"] = {
                "iterations": [dict(item) for item in iterations],
                "completedIterations": [dict(item) for item in completed],
            }
        fields.append(field)
    return {"data": {"organization": {"projectV2": {"title": "Mash", "fields": {"nodes": fields}}}}}


def sprint(title="Sprint 5", start="2026-10-16", duration=15):
    return {"title": title, "startDate": start, "duration": duration}


def test_fifteen_day_sprint_has_inclusive_last_day():
    [found] = sprints.parse_iterations(payload(iterations=[sprint()]))
    assert found.start_date == date(2026, 10, 16)
    assert found.last_day == date(2026, 10, 30)


def test_four_day_sprint_has_inclusive_last_day():
    [found] = sprints.parse_iterations(payload(iterations=[sprint("Sprint 6", "2026-10-31", 4)]))
    assert found.last_day == date(2026, 11, 3)


def test_sprint_is_not_eligible_on_its_last_day():
    known = sprints.parse_iterations(payload(iterations=[sprint()]))
    assert sprints.eligible(known, date(2026, 10, 30)) == []


def test_sprint_is_eligible_the_day_after_it_ends():
    known = sprints.parse_iterations(payload(iterations=[sprint()]))
    assert [s.title for s in sprints.eligible(known, date(2026, 10, 31))] == ["Sprint 5"]


def test_running_and_future_sprints_are_not_eligible():
    known = sprints.parse_iterations(payload(iterations=[sprint("Sprint 5", "2026-10-16", 15), sprint("Sprint 6", "2026-10-31", 4)]))
    assert sprints.eligible(known, date(2026, 10, 20)) == []


def test_completed_iterations_are_included_and_duplicates_are_dropped():
    known = sprints.parse_iterations(
        payload(iterations=[sprint("Sprint 5", "2026-10-16", 15)], completed=[sprint("Sprint 4", "2026-10-01", 15), sprint("Sprint 5", "2026-10-16", 15)])
    )
    assert [(s.title, s.start_date) for s in known] == [("Sprint 4", date(2026, 10, 1)), ("Sprint 5", date(2026, 10, 16))]


def test_eligible_sprints_come_in_chronological_order():
    known = sprints.parse_iterations(
        payload(iterations=[sprint("Sprint 5", "2026-10-16", 15), sprint("Sprint 4", "2026-10-01", 15)])
    )
    assert [s.start_date for s in sprints.eligible(known, date(2026, 10, 31))] == [date(2026, 10, 1), date(2026, 10, 16)]


def test_empty_iteration_lists_are_not_an_error():
    assert sprints.parse_iterations(payload()) == []


@pytest.mark.parametrize(
    "item",
    [
        {"title": "Sprint 5", "duration": 15},
        {"title": "Sprint 5", "startDate": "2026-10-16"},
        {"title": "Sprint 5", "startDate": "2026-10-16", "duration": 0},
        {"title": "Sprint 5", "startDate": "2026-10-16", "duration": "15"},
        {"title": "Sprint 5", "startDate": "16/10/2026", "duration": 15},
    ],
)
def test_invalid_iteration_fails_without_partial_period(item):
    with pytest.raises(config.ConfigurationError):
        sprints.parse_iterations(payload(iterations=[sprint("Sprint 4", "2026-10-01", 15), item]))


def test_missing_project_fails():
    with pytest.raises(config.ConfigurationError):
        sprints.parse_iterations({"data": {"organization": None}})
    with pytest.raises(config.ConfigurationError):
        sprints.parse_iterations({"data": {"organization": {"projectV2": None}}})


def test_missing_sprint_field_fails():
    with pytest.raises(config.ConfigurationError):
        sprints.parse_iterations(payload(sprint_fields=()))


def test_duplicated_sprint_field_fails():
    with pytest.raises(config.ConfigurationError):
        sprints.parse_iterations(payload(sprint_fields=("Sprint", "Sprint")))


def test_sprint_field_without_configuration_fails():
    with pytest.raises(config.ConfigurationError):
        sprints.parse_iterations(payload(configuration=False))


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response, self.error = response, error
        self.calls = []

    def graphql(self, query, variables=None):
        self.calls.append(variables)
        if self.error:
            raise self.error
        return self.response


def test_fetch_sprints_queries_the_mash_project():
    client = FakeClient(payload(iterations=[sprint()]))
    assert [s.title for s in sprints.fetch_sprints(client)] == ["Sprint 5"]
    assert client.calls == [{"organization": "conloq", "number": 2}]


def test_fetch_sprints_propagates_api_errors():
    with pytest.raises(GitHubAPIError):
        sprints.fetch_sprints(FakeClient(error=GitHubAPIError("GitHub GraphQL error: forbidden")))
