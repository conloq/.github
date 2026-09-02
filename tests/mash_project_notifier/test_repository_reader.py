from automation.mash_project_notifier.repository_reader import (
    link_pull_request_to_issue,
    read_pull_requests,
)


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.paths = []

    def rest(self, method, path, payload=None):
        self.paths.append((method, path, payload))
        return self.response


def test_link_pull_request_to_issue_requires_explicit_cross_repository_reference():
    pr = {
        "repository": "conloq/Back-End",
        "title": "Implementar endpoint",
        "body": "Closes conloq/mash#34",
    }

    assert link_pull_request_to_issue(pr) == [{"repository": "conloq/mash", "number": 34}]


def test_local_issue_reference_is_only_resolved_inside_planning_repository():
    pr = {
        "repository": "conloq/mash",
        "title": "Corrigir documentação #34",
        "body": "Fixes #34",
    }

    assert link_pull_request_to_issue(pr) == [{"repository": "conloq/mash", "number": 34}]


def test_read_pull_requests_filters_by_updated_timestamp_and_allowlist():
    client = FakeClient([
        {
            "number": 1,
            "updated_at": "2026-09-01T12:00:00Z",
            "repository": "conloq/frontend",
        },
        {
            "number": 2,
            "updated_at": "2026-08-31T12:00:00Z",
            "repository": "conloq/frontend",
        },
    ])

    result = read_pull_requests(client, ("conloq/frontend",), "2026-09-01T00:00:00Z")

    assert [x["number"] for x in result] == [1]
    assert client.paths == [("GET", "/repos/conloq/frontend/pulls?state=all&sort=updated&direction=desc&per_page=100", None)]
