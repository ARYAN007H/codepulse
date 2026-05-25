"""Risk scoring engine — combines all metrics into a single 0-100 risk score.

Also generates human-readable insights via heuristic rules.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
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
    confidence: str
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
            "confidence": self.confidence,
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
        risk = (cc_risk * 0.40) + (mi_risk * 0.35) + (churn_risk * 0.20) + (loc_risk * 0.05)

    Formula (without git):
        risk = (cc_risk * 0.50) + (mi_risk * 0.40) + (loc_risk * 0.10)

    Weight Rationale:
        - Complexity (40%): McCabe's Cyclomatic Complexity (1976) measures logical path density.
        - Maintainability (35%): Radon's Maintainability Index measures readability and size.
        - Churn (20%): Historical git commit count identifies active development hotspots.
        - Size (5%): LOC acts as a minor penalty for large files (capped at 1,000 LOC).
    """
    if not file_metrics:
        return []

    if use_git and churn_stats:
        all_churn = [
            churn_stats.get(f["path"], {}).get("commit_count", 0) for f in file_metrics
        ]
        churn_max = max(all_churn) if all_churn else 0
    else:
        churn_max = 0

    scored = []
    for f in file_metrics:
        path = f["path"]
        churn = churn_stats.get(path, {}) if churn_stats else {}
        commit_count = churn.get("commit_count", 0)
        loc = f.get("loc", 0)
        num_functions = f.get("num_functions", 0)

        # 1. Complexity Risk (cc_risk) using soft exponential decay
        # Soft curve preserves differentiability at high scores (doesn't flatline at 100).
        avg_cc = f.get("avg_cc", 0.0)
        max_cc = f.get("max_cc", 0)
        cc_metric = (avg_cc * 4.0) + (max_cc * 1.5)
        cc_risk = 100.0 * (1.0 - math.exp(-cc_metric / 50.0))

        # 2. Maintainability Index Risk (mi_risk)
        # Standard Radon MI score (0-100). Default to 100.0 (perfectly maintainable) if None/missing.
        mi_score = f.get("mi_score")
        mi_val = mi_score if mi_score is not None else 100.0
        mi_risk = max(0.0, min(100.0, 100.0 - mi_val))

        # 3. Absolute Capped Size Risk (loc_risk)
        # Capped at 1,000 LOC. Linear scaling from 0 to 100.
        loc_risk = min(100.0, (loc / 1000.0) * 100.0)

        # 4. Hybrid Git Churn Risk (churn_risk)
        # Avoids inflating 1-commit files by imposing a floor of 15 commits.
        if use_git and churn_stats:
            churn_risk = (commit_count / max(churn_max, 15)) * 100.0
            # Composite risk with Git (40% CC, 35% MI, 20% Churn, 5% LOC)
            risk = (
                (cc_risk * 0.40)
                + (mi_risk * 0.35)
                + (churn_risk * 0.20)
                + (loc_risk * 0.05)
            )
        else:
            # Composite risk without Git (50% CC, 40% MI, 10% LOC)
            risk = (
                (cc_risk * 0.50)
                + (mi_risk * 0.40)
                + (loc_risk * 0.10)
            )

        risk = max(0.0, min(100.0, risk))

        # 5. Confidence score
        # Very small files (< 20 lines) or stubs without functions have low complexity representation,
        # making static analysis metrics less statistically confident.
        confidence = "low" if (loc < 20 or num_functions == 0) else "high"

        scored.append(
            ScoredFile(
                path=path,
                loc=loc,
                sloc=f.get("sloc", 0),
                blank_lines=f.get("blank_lines", 0),
                comment_lines=f.get("comment_lines", 0),
                comment_ratio=f.get("comment_ratio", 0.0),
                avg_cc=avg_cc,
                max_cc=max_cc,
                cc_grade=f.get("cc_grade", "A"),
                mi_score=mi_val,
                mi_grade=f.get("mi_grade", "good"),
                num_functions=num_functions,
                functions=f.get("functions", []),
                commit_count=commit_count,
                unique_authors=churn.get("unique_authors", 0),
                last_modified=churn.get("last_modified"),
                last_modified_human=churn.get("last_modified_human", "unknown"),
                last_modified_days=churn.get("last_modified_days"),
                risk_score=round(risk, 1),
                risk_tier=_risk_tier(risk),
                confidence=confidence,
                extension=f.get("extension", ""),
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
