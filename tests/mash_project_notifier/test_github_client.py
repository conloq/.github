import json

from automation.mash_project_notifier.github_client import GitHubClient


class Response:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_graphql_client_sends_bearer_token_without_leaking_it():
    requests = []

    def opener(request, timeout):
        requests.append((request, timeout))
        return Response({"data": {"ok": True}})

    client = GitHubClient("secret-value", opener=opener)
    result = client.graphql("query { viewer { login } }", {"id": "project"})

    assert result == {"data": {"ok": True}}
    request, timeout = requests[0]
    assert request.get_header("Authorization") == "Bearer secret-value"
    assert timeout == 30
    assert "secret-value" not in request.data.decode()
