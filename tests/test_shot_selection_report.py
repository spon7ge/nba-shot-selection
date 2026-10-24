"""The shot-selection findings page stays tied to the notebook tables."""

import csv
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "eda_findings.html"
TABLES = ROOT / "data" / "shot_selection"


def _report_text() -> str:
    assert HTML.is_file(), f"missing findings page: {HTML}"
    return HTML.read_text(encoding="utf-8")


def _embedded() -> dict:
    text = _report_text()
    match = re.search(
        r'<script type="application/json" id="shot-data">(.*?)</script>',
        text,
        flags=re.DOTALL,
    )
    assert match, "findings page is missing embedded shot data"
    return json.loads(match.group(1))


def test_page_states_the_question_and_the_descriptive_limit() -> None:
    text = _report_text()
    assert "How does shot selection differ across NBA teams" in text
    assert "These are descriptive observations. They do not identify causal effects." in text
    assert "innerHTML" not in text


def test_embedded_totals_reconcile_internally() -> None:
    data = _embedded()
    assert data["meta"]["season"] == "2025-26"
    assert data["meta"]["shotRows"] == 219159
    assert len(data["teams"]) == 30
    assert sum(row["fga"] for row in data["teams"]) == data["meta"]["shotRows"]
    assert sum(row["fga"] for row in data["leagueGroups"]) == data["meta"]["shotRows"]

    best_team = max(data["teams"], key=lambda row: row["ppa"])
    worst_team = min(data["teams"], key=lambda row: row["ppa"])
    assert best_team["team"] == "DEN"
    assert worst_team["team"] == "BKN"

    best_group = max(data["leagueGroups"], key=lambda row: row["ppa"])
    most_points = max(data["leagueGroups"], key=lambda row: row["points"])
    assert best_group["group"] == "2PT: under 4 ft"
    assert best_group["fga"] == 56943
    assert most_points["group"] == "Three-pointers"
    assert most_points["points"] == 98151
    assert most_points["fga"] == 90970

    threes = [row for row in data["groups"] if row["group"] == "Three-pointers"]
    low = min(threes, key=lambda row: row["share"])
    high = max(threes, key=lambda row: row["share"])
    assert low["team"] == "SAC" and low["fga"] == 2476
    assert high["team"] == "GSW" and high["fga"] == 3616

    court_teams = sorted({row["team"] for row in data["zones"]})
    assert court_teams == ["CLE", "DEN", "LAL", "NYK"]
    assert len(data["zones"]) == 56
    assert len(data["court"]["polygons"]) == 14


def test_embedded_rows_match_saved_tables() -> None:
    if not (TABLES / "team_summary.csv").is_file():
        pytest.skip("shot-selection tables are not in this checkout")
    data = _embedded()

    with (TABLES / "team_summary.csv").open(encoding="utf-8") as handle:
        teams = list(csv.DictReader(handle))
    by_team = {row["team"]: row for row in data["teams"]}
    assert set(by_team) == {row["team"] for row in teams}
    for row in teams:
        got = by_team[row["team"]]
        assert got["fga"] == int(row["fga"])
        assert got["points"] == int(float(row["points"]))
        assert got["ppa"] == pytest.approx(float(row["ppa"]))
        assert got["efg"] == pytest.approx(float(row["efg_pct"]))

    with (TABLES / "shot_group_summary.csv").open(encoding="utf-8") as handle:
        groups = list(csv.DictReader(handle))
    keyed = {(row["team"], row["group"]): row for row in data["groups"]}
    assert len(keyed) == len(groups)
    for row in groups:
        got = keyed[(row["team"], row["shot_group"])]
        assert got["fga"] == int(row["fga"])
        assert got["points"] == int(float(row["points"]))
        assert got["ppa"] == pytest.approx(float(row["ppa"]))
        assert got["share"] == pytest.approx(float(row["shot_share"]))

    with (TABLES / "court_zones.csv").open(encoding="utf-8") as handle:
        zones = list(csv.DictReader(handle))
    zone_key = {(row["team"], row["section"]): row for row in data["zones"]}
    assert len(zone_key) == len(zones)
    for row in zones:
        got = zone_key[(row["team"], row["section"])]
        assert got["attempts"] == int(row["attempts"])
        assert got["makes"] == int(row["makes"])
        assert got["ppa"] == pytest.approx(float(row["ppa"]))
        assert got["fgPct"] == pytest.approx(float(row["fg_pct"]))
