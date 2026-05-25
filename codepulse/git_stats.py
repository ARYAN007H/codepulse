"""Git log parsing for churn, authors, and file age.

Uses gitpython to extract commit history per file without shelling out.
Provides ChurnStats with human-readable time deltas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ChurnStats:
    """Git churn statistics for a single file."""

    commit_count: int = 0
    unique_authors: int = 0
    last_modified: datetime | None = None
    author_list: list[str] = field(default_factory=list)

    @property
    def last_modified_days_ago(self) -> int | None:
        if self.last_modified is None:
            return None
        delta = datetime.now(timezone.utc) - self.last_modified
        return delta.days

    @property
    def last_modified_human(self) -> str:
        days = self.last_modified_days_ago
        if days is None:
            return "unknown"
        if days == 0:
            return "today"
        elif days == 1:
            return "yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"

    def to_dict(self) -> dict:
        return {
            "commit_count": self.commit_count,
            "unique_authors": self.unique_authors,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "last_modified_human": self.last_modified_human,
            "last_modified_days": self.last_modified_days_ago,
            "author_list": self.author_list,
        }


def init_repo(path: Path):
    """Initialize a git.Repo, returns None if not a git repo."""
    try:
        import git

        repo = git.Repo(path, search_parent_directories=True)
        return repo
    except Exception as e:
        logger.info("Not a git repository: %s", e)
        return None


def get_churn(repo, filepath: str, depth: int = 200) -> ChurnStats:
    """Get churn stats for a single file within the last `depth` commits."""
    try:
        commits = list(repo.iter_commits(max_count=depth, paths=filepath))
        if not commits:
            return ChurnStats()

        authors = set()
        author_list = []
        for c in commits:
            email = c.author.email if c.author else "unknown"
            authors.add(email)
            if email not in author_list:
                author_list.append(email)

        last_modified = datetime.fromtimestamp(
            commits[0].committed_date, tz=timezone.utc
        )

        return ChurnStats(
            commit_count=len(commits),
            unique_authors=len(authors),
            last_modified=last_modified,
            author_list=author_list,
        )
    except Exception as e:
        logger.warning("Git churn analysis failed for %s: %s", filepath, e)
        return ChurnStats()


def get_repo_name(repo) -> str:
    """Extract a human-readable repo name from a git.Repo object."""
    try:
        return Path(repo.working_dir).name
    except Exception:
        return "unknown"
