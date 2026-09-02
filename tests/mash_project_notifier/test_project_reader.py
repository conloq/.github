import pytest

from automation.mash_project_notifier.project_reader import ProjectDataError, read_project


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def graphql(self, query, variables):
        self.calls.append(variables)
        return next(self.responses)


def _payload(items, has_next=False, cursor=None):
    return {
        "data": {
            "node": {
                "title": "Mash",
                "number": 2,
                "fields": {
                    "nodes": [
                        {
                            "__typename": "ProjectV2SingleSelectField",
                            "id": "status-field",
                            "name": "Status",
                            "options": [
                                {"id": "ready", "name": "Ready"},
                                {"id": "done", "name": "Done"},
                            ],
                        },
                        {
                            "__typename": "ProjectV2IterationField",
                            "id": "sprint-field",
                            "name": "Sprint",
                            "configuration": {
                                "iterations": [
                                    {"id": "s2", "title": "Sprint 2", "startDate": "2026-09-01", "duration": 15}
                                ]
                            },
                        },
                    ]
                },
                "items": {
                    "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                    "nodes": items,
                },
            }
        }
    }


def item(item_id, number, status_name="Ready", status_id="ready"):
    return {
        "id": item_id,
        "content": {
            "__typename": "Issue",
            "number": number,
            "title": f"Tarefa {number}",
            "url": f"https://github.com/conloq/mash/issues/{number}",
            "state": "OPEN",
            "repository": {"nameWithOwner": "conloq/mash"},
        },
        "fieldValues": {
            "nodes": [
                {
                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                    "name": status_name,
                    "optionId": status_id,
                    "field": {"id": "status-field", "name": "Status"},
                },
                {
                    "__typename": "ProjectV2ItemFieldIterationValue",
                    "title": "Sprint 2",
                    "iterationId": "s2",
                    "startDate": "2026-09-01",
                    "duration": 15,
                    "field": {"id": "sprint-field", "name": "Sprint"},
                },
            ]
        },
    }


def test_read_project_normalizes_items_and_follows_pagination():
    client = FakeClient([
        _payload([item("item-1", 1)], has_next=True, cursor="cursor-1"),
        _payload([item("item-2", 2, "Done", "done")]),
    ])

    result = read_project(client, "project-id")

    assert [x["item_id"] for x in result["items"]] == ["item-1", "item-2"]
    assert result["items"][1]["status_id"] == "done"
    assert result["items"][0]["repository"] == "conloq/mash"
    assert client.calls == [{"id": "project-id", "after": None}, {"id": "project-id", "after": "cursor-1"}]


def test_read_project_rejects_duplicate_item_ids():
    client = FakeClient([_payload([item("same", 1), item("same", 2)])])

    with pytest.raises(ProjectDataError, match="duplicate"):
        read_project(client, "project-id")
