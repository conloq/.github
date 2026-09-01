from __future__ import annotations

import os
from dataclasses import dataclass

PROJECT_ID = "PVT_kwDOErFxpc4BfsEe"
PROJECT_NUMBER = 2
PROJECT_OWNER = "conloq"
PROJECT_TITLE = "Mash"
TEAM_MENTION = "@conloq/mash"
LOCAL_TIMEZONE = "America/Sao_Paulo"
PLANNING_REPOSITORY = "conloq/mash"
CODE_REPOSITORIES = (
    "conloq/Back-End",
    "conloq/frontend",
    "conloq/landing-page-conloq",
)
TRACKER_REPOSITORY = "conloq/.github"


class ConfigurationError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigurationError(f"invalid boolean value: {value!r}")


@dataclass(frozen=True)
class Settings:
    token: str
    project_id: str = PROJECT_ID
    project_number: int = PROJECT_NUMBER
    project_owner: str = PROJECT_OWNER
    team_mention: str = TEAM_MENTION
    timezone: str = LOCAL_TIMEZONE
    planning_repository: str = PLANNING_REPOSITORY
    tracker_repository: str = TRACKER_REPOSITORY
    tracker_issue_number: int | None = None
    code_repositories: tuple[str, ...] = CODE_REPOSITORIES
    dry_run: bool = False
    daily_hour: int = 9

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.environ.get("MASH_PROJECT_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
        tracker = os.environ.get("MASH_TRACKER_ISSUE_NUMBER") or ""
        tracker_number = None
        if tracker:
            try:
                tracker_number = int(tracker)
            except ValueError as exc:
                raise ConfigurationError("MASH_TRACKER_ISSUE_NUMBER must be an integer") from exc
        try:
            daily_hour = int(os.environ.get("MASH_DAILY_HOUR", "9"))
        except ValueError as exc:
            raise ConfigurationError("MASH_DAILY_HOUR must be an integer") from exc
        if not 0 <= daily_hour <= 23:
            raise ConfigurationError("MASH_DAILY_HOUR must be between 0 and 23")
        return cls(
            token=token,
            tracker_issue_number=tracker_number,
            dry_run=_bool(os.environ.get("MASH_DRY_RUN"), False),
            daily_hour=daily_hour,
        )

    def require_token(self) -> str:
        if not self.token:
            raise ConfigurationError("MASH_PROJECT_TOKEN or GITHUB_TOKEN is required")
        return self.token

    def safe_for_log(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "project_number": self.project_number,
            "team_mention": self.team_mention,
            "timezone": self.timezone,
            "planning_repository": self.planning_repository,
            "tracker_repository": self.tracker_repository,
            "tracker_issue_number": self.tracker_issue_number,
            "code_repositories": self.code_repositories,
            "dry_run": self.dry_run,
            "daily_hour": self.daily_hour,
            "has_token": bool(self.token),
        }
