from datetime import datetime, timedelta, timezone

from datax_support.nightly import Report, classify_runs

NOW = datetime(2026, 11, 3, 6, 0, tzinfo=timezone.utc)


def run(conclusion: str, days: int) -> dict:
    when = (NOW - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"conclusion": conclusion, "updated_at": when, "html_url": "https://x/run"}


def test_red_ignores_cancelled():
    runs = [run("cancelled", 0), run("cancelled", 1), run("success", 3)]
    assert classify_runs(runs, NOW) == "green"


def test_red_on_latest_failure():
    assert classify_runs([run("failure", 0), run("success", 2)], NOW) == "red"


def test_stale_after_30_days():
    assert classify_runs([run("success", 31)], NOW) == "stale"


def test_stale_when_no_runs():
    assert classify_runs([], NOW) == "stale"


def test_report_markdown_lists_sections():
    md = Report(
        drift={"tick": "--- a\n+++ b"},
        red=[("hopcap", "hw-test.yml", "red", "https://x/run")],
        dead_links=[],
    ).to_markdown()
    assert "## Drift" in md
    assert "## Red or stale workflows" in md
    assert "## Dead evidence links" in md
    assert not Report(drift={}, red=[], dead_links=[]).is_clean is False
    assert Report(drift={}, red=[], dead_links=[]).is_clean
