"""HTML report renderer for eval delta results.

Produces a self-contained HTML document with inline CSS, no JavaScript,
and no external resources.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skillforge.evaluator.delta import DeltaReport, PerTaskRow


def _color_for_delta(delta: float) -> str:
    """Return CSS color for a delta value."""
    if delta > 0:
        return "#2e7d32"
    if delta < 0:
        return "#c62828"
    return "#757575"


def _render_sparkline_svg(bootstrap_means: list[float], width: int = 300, height: int = 60) -> str:
    """Render a simple SVG histogram of bootstrap distribution (20 bins)."""
    if not bootstrap_means:
        return ""
    n_bins = 20
    mn = min(bootstrap_means)
    mx = max(bootstrap_means)
    rng = mx - mn if mx != mn else 1.0
    bins = [0] * n_bins
    for v in bootstrap_means:
        idx = min(int((v - mn) / rng * n_bins), n_bins - 1)
        bins[idx] += 1
    max_count = max(bins) or 1
    bar_w = width / n_bins
    bars = ""
    for i, count in enumerate(bins):
        bar_h = (count / max_count) * height
        x = i * bar_w
        y = height - bar_h
        bars += (
            f'<rect x="{x:.1f}" y="{y:.1f}" '
            f'width="{bar_w:.1f}" height="{bar_h:.1f}" '
            f'fill="#1565c0" opacity="0.7"/>'
        )
    return f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">{bars}</svg>'


def _render_per_task_rows(per_task: list[PerTaskRow]) -> str:
    """Render HTML table rows for per-task breakdown."""
    rows = ""
    for row in per_task:
        color = _color_for_delta(row.delta)
        rows += (
            f"<tr>"
            f"<td>{row.task_id}</td>"
            f"<td>{row.baseline:.3f}</td>"
            f"<td>{row.with_skill:.3f}</td>"
            f'<td style="color:{color};font-weight:bold">'
            f"{row.delta:+.3f}</td>"
            f"</tr>\n"
        )
    return rows


_CSS = """\
body { font-family: system-ui, sans-serif; margin: 2rem; color: #212121; }
h1 { color: #1565c0; }
.summary { background: #fff; border: 1px solid #e0e0e0;
  border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; }
.summary table { border-collapse: collapse; }
.summary td { padding: 0.4rem 1rem; }
.summary td:first-child { font-weight: bold; color: #424242; }
table.tasks { border-collapse: collapse; width: 100%; background: #fff; }
table.tasks th, table.tasks td {
  border: 1px solid #e0e0e0; padding: 0.5rem 1rem; text-align: left; }
table.tasks th { background: #1565c0; color: #fff; }
table.tasks tr:nth-child(even) { background: #f5f5f5; }
.sparkline { margin: 1.5rem 0; }
.sparkline-label { font-size: 0.85rem; color: #757575; }
"""


def render_html_report(report: DeltaReport) -> str:
    """Produce a self-contained HTML eval report.

    Args:
        report: The DeltaReport containing bootstrap and per-task data.

    Returns:
        A complete HTML document as a string.
    """
    bs = report.bootstrap
    verdict = "SIGNIFICANT" if bs.significant else "NOT significant"
    verdict_color = "#2e7d32" if bs.significant else "#c62828"

    # Reconstruct approximate bootstrap distribution for sparkline
    rng = random.Random(42)
    deltas = [r.delta for r in report.per_task]
    if deltas:
        n = len(deltas)
        bootstrap_means = [
            sum(rng.choice(deltas) for _ in range(n)) / n for _ in range(bs.n_resamples)
        ]
    else:
        bootstrap_means = []

    sparkline = _render_sparkline_svg(bootstrap_means)
    task_rows = _render_per_task_rows(report.per_task)

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        "<title>d-skill-forge Eval Report</title>\n"
        f"<style>\n{_CSS}</style>\n"
        "</head>\n<body>\n"
        "<h1>d-skill-forge Eval Report</h1>\n"
        '<div class="summary">\n<table>\n'
        f"<tr><td>Baseline score</td>"
        f"<td>{report.baseline_score:.4f}</td></tr>\n"
        f"<tr><td>With-skill score</td>"
        f"<td>{report.with_skill_score:.4f}</td></tr>\n"
        f"<tr><td>Delta</td>"
        f'<td style="color:{_color_for_delta(report.delta)}">'
        f"{report.delta:+.4f}</td></tr>\n"
        f"<tr><td>CI ({bs.confidence * 100:.0f}%)</td>"
        f"<td>[{bs.ci_lower:+.4f}, {bs.ci_upper:+.4f}]</td></tr>\n"
        f"<tr><td>Bootstrap resamples</td>"
        f"<td>{bs.n_resamples}</td></tr>\n"
        f"<tr><td>Wins / Losses / Ties</td>"
        f"<td>{bs.wins} / {bs.losses} / {bs.ties}</td></tr>\n"
        "</table>\n"
        f'<div class="verdict" style="font-size:1.2rem;'
        f'font-weight:bold;color:{verdict_color};margin-top:1rem">'
        f"{verdict}</div>\n"
        "</div>\n"
        '<div class="sparkline">\n'
        f'<p class="sparkline-label">'
        f"Bootstrap delta distribution ({bs.n_resamples} resamples)</p>\n"
        f"{sparkline}\n</div>\n"
        "<h2>Per-task breakdown</h2>\n"
        '<table class="tasks">\n'
        "<thead><tr><th>Task ID</th><th>Baseline</th>"
        "<th>With Skill</th><th>Delta</th></tr></thead>\n"
        f"<tbody>\n{task_rows}</tbody>\n"
        "</table>\n</body>\n</html>"
    )
