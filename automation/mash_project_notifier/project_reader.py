from __future__ import annotations

from typing import Any


class ProjectDataError(ValueError):
    """Raised when Project data is not safe to count."""


PROJECT_QUERY = """
query($id: ID!, $after: String) {
  node(id: $id) {
    ... on ProjectV2 {
      id
      title
      number
      fields(first: 50) {
        nodes {
          __typename
          ... on ProjectV2FieldCommon { id name }
          ... on ProjectV2SingleSelectField {
            id name options { id name }
          }
          ... on ProjectV2IterationField {
            id name
            configuration {
              iterations { id title startDate duration }
            }
          }
        }
      }
      items(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content {
            __typename
            ... on Issue {
              number title url state repository { nameWithOwner }
            }
            ... on PullRequest {
              number title url state repository { nameWithOwner }
            }
            ... on DraftIssue { title body }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                name optionId field { ... on ProjectV2FieldCommon { id name } }
              }
              ... on ProjectV2ItemFieldIterationValue {
                title iterationId startDate duration
                field { ... on ProjectV2FieldCommon { id name } }
              }
            }
          }
        }
      }
    }
  }
}
"""


def _field_name(value: dict[str, Any]) -> str | None:
    field = value.get("field") or {}
    return field.get("name")


def _normalise_item(raw: dict[str, Any]) -> dict[str, Any]:
    content = raw.get("content") or {}
    repository = (content.get("repository") or {}).get("nameWithOwner")
    item: dict[str, Any] = {
        "item_id": raw.get("id"),
        "content_type": content.get("__typename"),
        "number": content.get("number"),
        "title": content.get("title") or "",
        "url": content.get("url"),
        "state": content.get("state"),
        "repository": repository,
        "status_id": None,
        "status_name": None,
        "sprint_id": None,
        "sprint": None,
        "sprint_start_date": None,
        "sprint_duration": None,
    }
    for value in (raw.get("fieldValues") or {}).get("nodes") or []:
        name = _field_name(value)
        if name == "Status":
            item["status_id"] = value.get("optionId")
            item["status_name"] = value.get("name")
        elif name == "Sprint":
            item["sprint_id"] = value.get("iterationId")
            item["sprint"] = value.get("title")
            item["sprint_start_date"] = value.get("startDate")
            item["sprint_duration"] = value.get("duration")
    if not item["item_id"]:
        raise ProjectDataError("Project item without id")
    return item


def _normalise_fields(raw_fields: list[dict[str, Any]]) -> dict[str, Any]:
    fields: list[dict[str, Any]] = []
    status_field = None
    sprint_field = None
    for raw in raw_fields:
        name = raw.get("name")
        field = {"id": raw.get("id"), "name": name, "type": raw.get("__typename")}
        if raw.get("__typename") == "ProjectV2SingleSelectField":
            field["options"] = raw.get("options") or []
        if raw.get("__typename") == "ProjectV2IterationField":
            field["iterations"] = (raw.get("configuration") or {}).get("iterations") or []
        fields.append(field)
        if name == "Status":
            status_field = field
        elif name == "Sprint":
            sprint_field = field
    return {"fields": fields, "status_field": status_field, "sprint_field": sprint_field}


def read_project(client: Any, project_id: str) -> dict[str, Any]:
    """Read and normalize every card in a ProjectV2."""
    if not project_id:
        raise ProjectDataError("project_id is required")
    after = None
    all_items: list[dict[str, Any]] = []
    project: dict[str, Any] | None = None
    field_data: dict[str, Any] | None = None
    seen: set[str] = set()
    while True:
        payload = client.graphql(PROJECT_QUERY, {"id": project_id, "after": after})
        node = ((payload.get("data") or {}).get("node"))
        if not node or node.get("title") is None:
            raise ProjectDataError("Project was not found or is not a ProjectV2")
        if project is None:
            project = {"id": node.get("id") or project_id, "title": node.get("title"), "number": node.get("number")}
            field_data = _normalise_fields((node.get("fields") or {}).get("nodes") or [])
        page = (node.get("items") or {}).get("pageInfo") or {}
        for raw in (node.get("items") or {}).get("nodes") or []:
            item = _normalise_item(raw)
            if item["item_id"] in seen:
                raise ProjectDataError(f"duplicate Project item_id: {item['item_id']}")
            seen.add(item["item_id"])
            all_items.append(item)
        if not page.get("hasNextPage"):
            break
        after = page.get("endCursor")
        if not after:
            raise ProjectDataError("Project pagination has no end cursor")

    assert project is not None
    assert field_data is not None
    iterations = list(field_data.get("sprint_field", {}).get("iterations", []) if field_data.get("sprint_field") else [])
    known_ids = {iteration.get("id") for iteration in iterations}
    for item in all_items:
        if item.get("sprint_id") and item["sprint_id"] not in known_ids:
            iterations.append(
                {
                    "id": item.get("sprint_id"),
                    "title": item.get("sprint"),
                    "startDate": item.get("sprint_start_date"),
                    "duration": item.get("sprint_duration"),
                }
            )
            known_ids.add(item["sprint_id"])
    missing = [
        item["item_id"]
        for item in all_items
        if not item.get("sprint") or not item.get("status_id")
    ]
    return {
        "project": project,
        "fields": field_data["fields"],
        "status_field": field_data["status_field"],
        "sprint_field": field_data["sprint_field"],
        "iterations": iterations,
        "items": all_items,
        "data_quality": "partial" if missing else "ok",
        "missing_field_items": missing,
    }
