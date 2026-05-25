"""Complexity analysis engine using radon.

Analyzes individual Python source files for cyclomatic complexity,
maintainability index, and raw line counts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze

logger = logging.getLogger(__name__)


@dataclass
class FileMetrics:
    """All collected metrics for a single source file."""

    path: str
    loc: int = 0
    sloc: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    avg_cc: float = 0.0
    max_cc: int = 0
    mi_score: float = 100.0
    num_functions: int = 0
    functions: list[dict[str, Any]] = field(default_factory=list)
    cc_grade: str = "A"
    mi_grade: str = "good"
    comment_ratio: float = 0.0
    extension: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "loc": self.loc,
            "sloc": self.sloc,
            "blank_lines": self.blank_lines,
            "comment_lines": self.comment_lines,
            "avg_cc": round(self.avg_cc, 2),
            "max_cc": self.max_cc,
            "mi_score": round(self.mi_score, 1),
            "num_functions": self.num_functions,
            "functions": self.functions,
            "cc_grade": self.cc_grade,
            "mi_grade": self.mi_grade,
            "comment_ratio": round(self.comment_ratio, 3),
            "extension": self.extension,
        }


def _cc_grade(avg_cc: float) -> str:
    """Map average cyclomatic complexity to a letter grade (radon scale)."""
    if avg_cc <= 5:
        return "A"
    elif avg_cc <= 10:
        return "B"
    elif avg_cc <= 15:
        return "C"
    elif avg_cc <= 20:
        return "D"
    elif avg_cc <= 25:
        return "E"
    return "F"


def _mi_grade(mi: float) -> str:
    """Map maintainability index to a human-readable grade."""
    if mi >= 20:
        return "good"
    elif mi >= 10:
        return "moderate"
    return "poor"


def _function_grade(cc: int) -> str:
    """Grade a single function's cyclomatic complexity."""
    if cc <= 5:
        return "A"
    elif cc <= 10:
        return "B"
    elif cc <= 15:
        return "C"
    elif cc <= 20:
        return "D"
    elif cc <= 25:
        return "E"
    return "F"


def analyze_file(filepath: Path, repo_root: Path | None = None) -> FileMetrics | None:
    """Analyze a single Python file for complexity metrics.

    Returns None if the file cannot be read or is empty.
    Gracefully handles parse errors by returning partial metrics.
    """
    try:
        source = filepath.read_text(errors="ignore")
    except (OSError, PermissionError) as e:
        logger.warning("Cannot read %s: %s", filepath, e)
        return None

    if not source.strip():
        return None

    rel_path = str(filepath.relative_to(repo_root)) if repo_root else str(filepath)

    # Raw line counts
    try:
        raw = analyze(source)
    except Exception as e:
        logger.warning("radon raw analysis failed for %s: %s", filepath, e)
        return None

    # Cyclomatic complexity
    try:
        cc_results = cc_visit(source)
    except Exception as e:
        logger.warning("radon CC analysis failed for %s: %s", filepath, e)
        cc_results = []

    # Maintainability index
    try:
        mi = mi_visit(source, multi=True)
        # Clamp MI to 0-100 range (radon can produce values outside)
        mi = max(0.0, min(100.0, mi))
    except Exception as e:
        logger.warning("radon MI analysis failed for %s: %s", filepath, e)
        mi = 100.0

    # Aggregate function-level metrics
    complexities = [block.complexity for block in cc_results]
    avg_cc = sum(complexities) / len(complexities) if complexities else 0
    max_cc = max(complexities, default=0)

    functions = []
    for block in cc_results:
        classname = None
        if hasattr(block, "classname") and block.classname:
            classname = block.classname
        functions.append(
            {
                "name": block.name,
                "complexity": block.complexity,
                "grade": _function_grade(block.complexity),
                "lineno": block.lineno,
                "classname": classname,
                "fullname": f"{classname}.{block.name}" if classname else block.name,
            }
        )

    total_lines = raw.loc if raw.loc > 0 else 1
    comment_ratio = raw.comments / total_lines

    return FileMetrics(
        path=rel_path,
        loc=raw.loc,
        sloc=raw.sloc,
        blank_lines=raw.blank,
        comment_lines=raw.comments,
        avg_cc=avg_cc,
        max_cc=max_cc,
        mi_score=mi,
        num_functions=len(cc_results),
        functions=functions,
        cc_grade=_cc_grade(avg_cc),
        mi_grade=_mi_grade(mi),
        comment_ratio=comment_ratio,
        extension=filepath.suffix.lstrip("."),
    )
