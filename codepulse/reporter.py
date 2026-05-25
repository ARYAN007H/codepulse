"""HTML report generator — injects analysis data into the template.

Produces a self-contained HTML file with all CSS/JS inlined.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from codepulse.template import HTML_TEMPLATE

logger = logging.getLogger(__name__)


def generate_report(
    scored_data: list[dict],
    insights: list[dict],
    repo_name: str,
    output_path: Path,
    use_git: bool = True,
) -> Path:
    """Generate a self-contained HTML report file.

    Args:
        scored_data: List of ScoredFile.to_dict() results.
        insights: List of insight dicts from generate_insights().
        repo_name: Human-readable repository name.
        output_path: Where to write the HTML file.
        use_git: Whether git data was used (affects column visibility).

    Returns:
        The absolute path of the generated report file.
    """
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Serialize data to JSON strings for injection
    data_json = json.dumps(scored_data, default=str, ensure_ascii=False)
    insights_json = json.dumps(insights, default=str, ensure_ascii=False)

    # Inject into template
    html = HTML_TEMPLATE
    html = html.replace("__DATA_PLACEHOLDER__", data_json)
    html = html.replace("__INSIGHTS_PLACEHOLDER__", insights_json)
    html = html.replace("__REPO_NAME_PLACEHOLDER__", repo_name)
    html = html.replace("__GENERATED_AT_PLACEHOLDER__", generated_at)
    html = html.replace("__USE_GIT_PLACEHOLDER__", "true" if use_git else "false")

    # Write output
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    logger.info("Report written to %s", output_path)
    return output_path
