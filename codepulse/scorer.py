"""Risk scoring engine — combines all metrics into a single 0-100 risk score.

Also generates human-readable insights via heuristic rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoredFile:
    """A file with all metrics and a computed composite risk score."""

    path: str
    loc: int
    sloc: int
    blank_lines: int
    comment_lines: int
    comment_ratio: float
    avg_cc: float
    max_cc: int
    cc_grade: str
    mi_score: float
    mi_grade: str
    num_functions: int
    functions: list[dict]
    commit_count: int
    unique_authors: int
    last_modified: str | None
    last_modified_human: str
    last_modified_days: int | None
    risk_score: float
    risk_tier: str
    extension: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "loc": self.loc,
            "sloc": self.sloc,
            "blank_lines": self.blank_lines,
            "comment_lines": self.comment_lines,
            "comment_ratio": round(self.comment_ratio, 3),
            "avg_cc": self.avg_cc,
            "max_cc": self.max_cc,
            "cc_grade": self.cc_grade,
            "mi_score": self.mi_score,
            "mi_grade": self.mi_grade,
            "num_functions": self.num_functions,
            "functions": self.functions,
            "commit_count": self.commit_count,
            "unique_authors": self.unique_authors,
            "last_modified": self.last_modified,
            "last_modified_human": self.last_modified_human,
            "last_modified_days": self.last_modified_days,
            "risk_score": self.risk_score,
            "risk_tier": self.risk_tier,
            "extension": self.extension,
        }


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to the 0-100 range."""
    if max_val == min_val:
        return 50.0
    return max(0.0, min(100.0, ((value - min_val) / (max_val - min_val)) * 100))


def _risk_tier(score: float) -> str:
    """Map a numeric risk score to a tier label."""
    if score <= 30:
        return "low"
    elif score <= 60:
        return "medium"
    elif score <= 80:
        return "high"
    return "critical"


def compute_scores(
    file_metrics: list[dict[str, Any]],
    churn_stats: dict[str, dict[str, Any]],
    use_git: bool = True,
) -> list[ScoredFile]:
    """Compute composite risk scores for all analyzed files.

    Formula (with git):
        risk = (norm_cc × 0.35) + ((100 - MI) × 0.30) + (norm_churn × 0.25) + (norm_loc × 0.10)

    Formula (without git):
        risk = (norm_cc × 0.45) + ((100 - MI) × 0.40) + (norm_loc × 0.15)

    All inputs normalized to 0-100 across the repo.
    """
    if not file_metrics:
        return []

    # Gather value ranges for normalization
    all_cc = [f["avg_cc"] for f in file_metrics]
    all_loc = [f["loc"] for f in file_metrics]
    cc_min, cc_max = min(all_cc), max(all_cc)
    loc_min, loc_max = min(all_loc), max(all_loc)

    if use_git and churn_stats:
        all_churn = [
            churn_stats.get(f["path"], {}).get("commit_count", 0) for f in file_metrics
        ]
        churn_min, churn_max = min(all_churn), max(all_churn)
    else:
        churn_min, churn_max = 0, 0

    scored = []
    for f in file_metrics:
        path = f["path"]
        churn = churn_stats.get(path, {})
        commit_count = churn.get("commit_count", 0)

        norm_cc = _normalize(f["avg_cc"], cc_min, cc_max)
        norm_mi_inverted = 100 - f["mi_score"]
        norm_loc = _normalize(f["loc"], loc_min, loc_max)

        if use_git and churn_stats:
            norm_churn = _normalize(commit_count, churn_min, churn_max)
            risk = (
                (norm_cc * 0.35)
                + (norm_mi_inverted * 0.30)
                + (norm_churn * 0.25)
                + (norm_loc * 0.10)
            )
        else:
            risk = (
                (norm_cc * 0.45) + (norm_mi_inverted * 0.40) + (norm_loc * 0.15)
            )

        risk = max(0.0, min(100.0, risk))

        scored.append(
            ScoredFile(
                path=path,
                loc=f["loc"],
                sloc=f["sloc"],
                blank_lines=f["blank_lines"],
                comment_lines=f["comment_lines"],
                comment_ratio=f["comment_ratio"],
                avg_cc=f["avg_cc"],
                max_cc=f["max_cc"],
                cc_grade=f["cc_grade"],
                mi_score=f["mi_score"],
                mi_grade=f["mi_grade"],
                num_functions=f["num_functions"],
                functions=f["functions"],
                commit_count=commit_count,
                unique_authors=churn.get("unique_authors", 0),
                last_modified=churn.get("last_modified"),
                last_modified_human=churn.get("last_modified_human", "unknown"),
                last_modified_days=churn.get("last_modified_days"),
                risk_score=round(risk, 1),
                risk_tier=_risk_tier(risk),
                extension=f["extension"],
            )
        )

    scored.sort(key=lambda s: s.risk_score, reverse=True)
    return scored


def generate_insights(
    scored_files: list[ScoredFile], use_git: bool = True
) -> list[dict]:
    """Generate auto-insights from scored data using heuristic rules."""
    insights = []
    if not scored_files:
        return insights

    total = len(scored_files)
    critical = [f for f in scored_files if f.risk_tier == "critical"]
    high = [f for f in scored_files if f.risk_tier == "high"]

    # ── Hotspot detection (churn + complexity) ──
    if use_git:
        churn_complex = [
            f for f in scored_files if f.commit_count > 10 and f.avg_cc > 10
        ]
        if churn_complex:
            insights.append(
                {
                    "icon": "🔥",
                    "type": "danger",
                    "title": "High-Churn Hotspots Detected",
                    "text": (
                        f"{len(churn_complex)} file{'s are' if len(churn_complex) != 1 else ' is'} "
                        f"both high-churn AND high-complexity — these are your biggest refactor targets."
                    ),
                    "files": [f.path for f in churn_complex[:5]],
                }
            )

    # ── Critical risk files ──
    if critical:
        insights.append(
            {
                "icon": "💀",
                "type": "critical",
                "title": "Critical Risk Files",
                "text": (
                    f"{len(critical)} file{'s' if len(critical) != 1 else ''} scored above 80/100 risk. "
                    f"The riskiest is **{critical[0].path}** at {critical[0].risk_score}/100."
                ),
                "files": [f.path for f in critical[:5]],
            }
        )

    # ── Knowledge silos ──
    if use_git:
        single_author = [
            f for f in scored_files if f.unique_authors <= 1 and f.commit_count > 0
        ]
        if single_author and total > 2:
            pct = round(len(single_author) / total * 100)
            if pct > 30:
                insights.append(
                    {
                        "icon": "🧠",
                        "type": "warning",
                        "title": "Knowledge Silos Detected",
                        "text": (
                            f"{pct}% of files have only been touched by 1 author — "
                            f"potential knowledge silos that increase bus-factor risk."
                        ),
                        "files": [],
                    }
                )

    # ── Worst directory ──
    folder_scores: dict[str, list[float]] = {}
    for f in scored_files:
        parts = f.path.replace("\\", "/").split("/")
        if len(parts) > 1:
            folder = "/".join(parts[:-1])
            folder_scores.setdefault(folder, []).append(f.risk_score)

    if folder_scores:
        worst_folder = max(
            folder_scores,
            key=lambda k: sum(folder_scores[k]) / len(folder_scores[k]),
        )
        avg = round(
            sum(folder_scores[worst_folder]) / len(folder_scores[worst_folder]), 1
        )
        if avg > 50 and len(folder_scores[worst_folder]) >= 2:
            insights.append(
                {
                    "icon": "📁",
                    "type": "warning",
                    "title": "Troubled Directory",
                    "text": (
                        f"**{worst_folder}/** has an average risk of {avg}/100 across "
                        f"{len(folder_scores[worst_folder])} files — consider refactoring it."
                    ),
                    "files": [],
                }
            )

    # ── Overall health ──
    avg_mi = sum(f.mi_score for f in scored_files) / total
    avg_risk = sum(f.risk_score for f in scored_files) / total
    if avg_mi < 20:
        label, advice = "poor", "Significant technical debt. Prioritize refactoring."
    elif avg_mi < 40:
        label, advice = (
            "moderate",
            "Trending toward technical debt. Address high-risk files first.",
        )
    elif avg_mi < 60:
        label, advice = "decent", "Room for improvement, but not in the danger zone."
    else:
        label, advice = "healthy", "Well-maintained codebase. Keep it up!"

    insights.append(
        {
            "icon": "🩺",
            "type": "info",
            "title": "Overall Codebase Health",
            "text": (
                f"Average Maintainability Index: {round(avg_mi, 1)}/100 ({label}). "
                f"Average risk score: {round(avg_risk, 1)}/100. {advice}"
            ),
            "files": [],
        }
    )

    # ── Large files ──
    large_files = [f for f in scored_files if f.loc > 500]
    if large_files:
        insights.append(
            {
                "icon": "📏",
                "type": "info",
                "title": "Large Files",
                "text": (
                    f"{len(large_files)} file{'s' if len(large_files) != 1 else ''} "
                    f"exceed{'s' if len(large_files) == 1 else ''} 500 lines of code. "
                    f"Consider breaking them into smaller, focused modules."
                ),
                "files": [
                    f.path
                    for f in sorted(large_files, key=lambda x: x.loc, reverse=True)[:5]
                ],
            }
        )

    # ── Low comment coverage ──
    low_comments = [f for f in scored_files if f.comment_ratio < 0.05 and f.loc > 50]
    if low_comments and len(low_comments) > total * 0.4:
        insights.append(
            {
                "icon": "💬",
                "type": "info",
                "title": "Low Comment Coverage",
                "text": (
                    f"{len(low_comments)} file{'s' if len(low_comments) != 1 else ''} "
                    f"have less than 5% comments. Adding docs can improve maintainability."
                ),
                "files": [],
            }
        )

    return insights
