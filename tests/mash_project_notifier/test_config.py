from automation.mash_project_notifier.config import Settings


def test_settings_loads_central_multirepo_defaults(monkeypatch):
    monkeypatch.delenv("MASH_PROJECT_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("MASH_DRY_RUN", raising=False)
    monkeypatch.delenv("MASH_TRACKER_ISSUE_NUMBER", raising=False)

    settings = Settings.from_env()

    assert settings.project_id == "PVT_kwDOErFxpc4BfsEe"
    assert settings.project_number == 2
    assert settings.team_mention == "@conloq/mash"
    assert settings.code_repositories == (
        "conloq/Back-End",
        "conloq/frontend",
        "conloq/landing-page-conloq",
    )
    assert settings.dry_run is False
    assert settings.tracker_issue_number is None


def test_settings_never_uses_a_token_literal_as_a_default(monkeypatch):
    monkeypatch.setenv("MASH_PROJECT_TOKEN", "secret-value")
    monkeypatch.setenv("MASH_DRY_RUN", "true")

    settings = Settings.from_env()

    assert settings.token == "secret-value"
    assert settings.dry_run is True
    assert "secret-value" not in repr(settings.safe_for_log())
