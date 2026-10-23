import json
import urllib.error

from automation.mash_logbook import config, llm

PROVIDERS = [
    config.Provider("a", "https://a.example/v1", "m-a", "A_KEY"),
    config.Provider("b", "https://b.example/v1/", "m-b", "B_KEY"),
    config.Provider("c", "https://c.example/v1", "m-c", "C_KEY"),
]


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def answer(text):
    return Response({"choices": [{"message": {"content": text}}]})


def test_skips_provider_without_key_and_falls_back_after_http_error():
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        if "b.example" in request.full_url:
            raise urllib.error.HTTPError(request.full_url, 429, "limite", {}, None)
        return answer("Semana com ajustes no login (#6).")

    env = {"B_KEY": "chave-b", "C_KEY": "chave-c"}
    result = llm.summarize(PROVIDERS, env, "fatos", {"6"}, {"haimonvieira"}, opener=opener)

    assert result.provider == "c"
    assert calls == ["https://b.example/v1/chat/completions", "https://c.example/v1/chat/completions"]
    assert [(a.provider, a.ok, a.reason) for a in result.attempts] == [
        ("a", False, "sem a chave A_KEY"),
        ("b", False, "HTTP 429"),
        ("c", True, "ok"),
    ]


def test_rejects_answer_that_invents_issue_or_person():
    respostas = iter(["Entregue a #99.", "Trabalho de @fulano.", "Semana sem novidades."])
    opener = lambda request, timeout: answer(next(respostas))
    env = {"A_KEY": "1", "B_KEY": "2", "C_KEY": "3"}
    result = llm.summarize(PROVIDERS, env, "fatos", {"6"}, {"haimonvieira"}, opener=opener)

    assert result.text == "Semana sem novidades."
    assert result.attempts[0].reason == "recusada: issue que não está nos fatos: #99"
    assert result.attempts[1].reason == "recusada: pessoa que não está nos fatos: @fulano"


def test_returns_none_when_every_provider_fails():
    def opener(request, timeout):
        raise urllib.error.URLError("sem rede")

    result = llm.summarize(PROVIDERS, {"A_KEY": "1"}, "fatos", set(), set(), opener=opener)
    assert result.text is None and result.provider is None


def test_request_carries_key_only_in_header():
    seen = {}

    def opener(request, timeout):
        seen["auth"] = request.get_header("Authorization")
        seen["body"] = request.data.decode()
        return answer("ok")

    llm.summarize(PROVIDERS[:1], {"A_KEY": "segredo"}, "fatos", set(), set(), opener=opener)
    assert seen["auth"] == "Bearer segredo"
    assert "segredo" not in seen["body"]
    assert json.loads(seen["body"])["model"] == "m-a"


def test_load_providers_reads_json_or_uses_defaults():
    assert [p.name for p in config.load_providers({})] == ["groq", "openrouter"]
    custom = config.load_providers({"LOGBOOK_LLM_PROVIDERS": json.dumps([{"name": "x", "base_url": "u", "model": "m", "key_env": "K"}])})
    assert custom == [config.Provider("x", "u", "m", "K")]


def test_clean_replaces_long_and_short_dashes():
    from automation.mash_logbook.llm import _clean

    assert _clean("Backend – CORS liberado — porta 4000") == "Backend, CORS liberado, porta 4000"
