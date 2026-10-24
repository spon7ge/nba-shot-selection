"""Embed the shot-selection tables in the findings page.

Run from the repo root:

    python build_eda_findings.py
"""

import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TABLES = ROOT / "data" / "shot_selection"
HTML = ROOT / "eda_findings.html"

BASELINE = -(4 + 1.25)
FT_LINE = 19 + BASELINE
THREE = 23.75
CORNER_X = 22.0
CORNER_Y = math.sqrt(THREE**2 - CORNER_X**2)
RIM = 4.0
FRAME = 32.0
THIRD = math.degrees(math.atan2(CORNER_X, CORNER_Y)) / 3
ARC_X_AT_FT = math.sqrt(THREE**2 - FT_LINE**2)
Y_AT_LANE = math.sqrt(THREE**2 - 8**2)

SECTION_ORDER = [
    "Left Corner 3",
    "Left Baseline Two",
    "Restricted Area",
    "Right Baseline Two",
    "Right Corner 3",
    "Left Short Two",
    "Paint",
    "Right Short Two",
    "Left Elbow Two",
    "Center Two",
    "Right Elbow Two",
    "Left Wing 3",
    "Center 3",
    "Right Wing 3",
]

TEAM_NAMES = {
    "ATL": "Atlanta Hawks",
    "BKN": "Brooklyn Nets",
    "BOS": "Boston Celtics",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards",
}


def _rows(name: str) -> list[dict[str, str]]:
    with (TABLES / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _arc(radius: float, start_deg: float, end_deg: float, n: int = 36) -> list[list[float]]:
    points = []
    for index in range(n):
        angle = math.radians(start_deg + (end_deg - start_deg) * index / (n - 1))
        points.append([round(radius * math.sin(angle), 4), round(radius * math.cos(angle), 4)])
    return points


def _section(x: float, y: float) -> str:
    """Same priority as the notebook's shot_sections."""
    distance = math.hypot(x, y)
    angle = math.degrees(math.atan2(x, y))
    near_baseline = y <= CORNER_Y
    if near_baseline and x <= -CORNER_X:
        return "Left Corner 3"
    if near_baseline and x >= CORNER_X:
        return "Right Corner 3"
    beyond_arc = distance >= THREE
    if beyond_arc and angle < -THIRD:
        return "Left Wing 3"
    if beyond_arc and angle > THIRD:
        return "Right Wing 3"
    if beyond_arc:
        return "Center 3"
    if distance < RIM:
        return "Restricted Area"
    if abs(x) <= 8 and y <= FT_LINE:
        return "Paint"
    if near_baseline and x < 0:
        return "Left Baseline Two"
    if near_baseline and x >= 0:
        return "Right Baseline Two"
    if y <= FT_LINE and x < 0:
        return "Left Short Two"
    if y <= FT_LINE and x >= 0:
        return "Right Short Two"
    if x < -8:
        return "Left Elbow Two"
    if x > 8:
        return "Right Elbow Two"
    return "Center Two"


def _polygons() -> dict[str, list[list[float]]]:
    left_corner = -math.degrees(math.atan2(CORNER_X, CORNER_Y))
    right_corner = -left_corner
    left_ft = math.degrees(math.atan2(-ARC_X_AT_FT, FT_LINE))
    right_ft = -left_ft
    left_lane = math.degrees(math.atan2(-8, Y_AT_LANE))
    right_lane = -left_lane
    polygons = {
        "Left Corner 3": [
            [-25, BASELINE],
            [-CORNER_X, BASELINE],
            [-CORNER_X, CORNER_Y],
            [-25, CORNER_Y],
        ],
        "Right Corner 3": [
            [CORNER_X, BASELINE],
            [25, BASELINE],
            [25, CORNER_Y],
            [CORNER_X, CORNER_Y],
        ],
        "Left Baseline Two": [
            [-CORNER_X, BASELINE],
            [-8, BASELINE],
            [-8, CORNER_Y],
            [-CORNER_X, CORNER_Y],
        ],
        "Right Baseline Two": [
            [8, BASELINE],
            [CORNER_X, BASELINE],
            [CORNER_X, CORNER_Y],
            [8, CORNER_Y],
        ],
        "Paint": [
            [-8, BASELINE],
            [8, BASELINE],
            [8, FT_LINE],
            [-8, FT_LINE],
        ],
        "Restricted Area": _arc(RIM, -90, 90) + [[RIM, 0.0], [-RIM, 0.0]],
        "Left Short Two": [[-8, CORNER_Y], [-CORNER_X, CORNER_Y]]
        + _arc(THREE, left_corner, left_ft)
        + [[-8, FT_LINE]],
        "Right Short Two": [[8, CORNER_Y], [CORNER_X, CORNER_Y]]
        + _arc(THREE, right_corner, right_ft)
        + [[8, FT_LINE]],
        "Left Elbow Two": [[-8, FT_LINE], [-ARC_X_AT_FT, FT_LINE]]
        + _arc(THREE, left_ft, left_lane)
        + [[-8, FT_LINE]],
        "Right Elbow Two": [[8, FT_LINE], [ARC_X_AT_FT, FT_LINE]]
        + _arc(THREE, right_ft, right_lane)
        + [[8, FT_LINE]],
        "Center Two": [[-8, FT_LINE], [8, FT_LINE]] + _arc(THREE, right_lane, left_lane),
        "Left Wing 3": _arc(THREE, left_corner, -THIRD) + _arc(FRAME, -THIRD, left_corner),
        "Center 3": _arc(THREE, -THIRD, THIRD) + _arc(FRAME, THIRD, -THIRD),
        "Right Wing 3": _arc(THREE, THIRD, right_corner) + _arc(FRAME, right_corner, THIRD),
    }
    rounded = {
        name: [[round(x, 4), round(y, 4)] for x, y in points]
        for name, points in polygons.items()
    }
    if list(rounded) != list(polygons):
        raise RuntimeError("polygon names changed while rounding")
    missing = [name for name in SECTION_ORDER if name not in rounded]
    if missing:
        raise RuntimeError(f"missing polygons: {missing}")
    return rounded


def _anchors() -> dict[str, list[float]]:
    radius = 27.5
    side = math.radians((math.degrees(math.atan2(CORNER_X, CORNER_Y)) + THIRD) / 2)
    return {
        "Left Corner 3": [-23.6, 1.0],
        "Right Corner 3": [23.6, 1.0],
        "Left Baseline Two": [-15.0, 2.0],
        "Right Baseline Two": [15.0, 2.0],
        "Restricted Area": [0.0, 2.2],
        "Paint": [0.0, 9.0],
        "Left Short Two": [-14.5, 11.2],
        "Right Short Two": [14.5, 11.2],
        "Left Elbow Two": [-13.0, 17.2],
        "Right Elbow Two": [13.0, 17.2],
        "Center Two": [0.0, 18.2],
        "Left Wing 3": [round(-radius * math.sin(side), 4), round(radius * math.cos(side), 4)],
        "Center 3": [0.0, 27.5],
        "Right Wing 3": [round(radius * math.sin(side), 4), round(radius * math.cos(side), 4)],
    }


def _check_geometry(anchors: dict[str, list[float]]) -> None:
    if abs(THIRD - 22.62) > 0.1:
        raise RuntimeError(f"above-the-break slice drifted: {THIRD:.2f}")
    if abs(math.hypot(CORNER_X, CORNER_Y) - THREE) > 1e-9:
        raise RuntimeError("corner line does not meet the arc")
    fixture = [
        (0, 1.6, "Restricted Area"),
        (0, 9, "Paint"),
        (-23, 1, "Left Corner 3"),
        (23, 1, "Right Corner 3"),
        (-15, 2, "Left Baseline Two"),
        (15, 2, "Right Baseline Two"),
        (-15, 11.2, "Left Short Two"),
        (15, 11.2, "Right Short Two"),
        (-13, 17.2, "Left Elbow Two"),
        (0, 18.2, "Center Two"),
        (13, 17.2, "Right Elbow Two"),
        (-18, 18, "Left Wing 3"),
        (0, 27.5, "Center 3"),
        (18, 18, "Right Wing 3"),
        (-22, 2, "Left Corner 3"),
    ]
    for x, y, expected in fixture:
        got = _section(x, y)
        if got != expected:
            raise RuntimeError(f"section ({x}, {y}) -> {got}, expected {expected}")
    for name, (x, y) in anchors.items():
        got = _section(x, y)
        if got != name:
            raise RuntimeError(f"label for {name} falls in {got}")


def _num(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise RuntimeError(f"non-finite value: {value}")
    return number


def build_payload() -> dict:
    meta_path = TABLES / "input_metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    teams = []
    for row in _rows("team_summary.csv"):
        code = row["team"]
        if code not in TEAM_NAMES:
            raise RuntimeError(f"unknown team code: {code}")
        teams.append(
            {
                "team": code,
                "name": TEAM_NAMES[code],
                "season": row["season"],
                "games": int(row["games"]),
                "fga": int(row["fga"]),
                "fgm": int(row["fgm"]),
                "fg3m": int(row["fg3m"]),
                "points": int(_num(row["points"])),
                "ppa": _num(row["ppa"]),
                "efg": _num(row["efg_pct"]),
            }
        )
    groups = []
    for row in _rows("shot_group_summary.csv"):
        groups.append(
            {
                "team": row["team"],
                "group": row["shot_group"],
                "fga": int(row["fga"]),
                "fgm": int(row["fgm"]),
                "fg3m": int(row["fg3m"]),
                "points": int(_num(row["points"])),
                "fgPct": _num(row["fg_pct"]),
                "ppa": _num(row["ppa"]),
                "efg": _num(row["efg_pct"]),
                "share": _num(row["shot_share"]),
            }
        )
    league_buckets: dict[str, dict[str, int]] = {}
    for row in groups:
        bucket = league_buckets.setdefault(
            row["group"], {"fga": 0, "fgm": 0, "fg3m": 0, "points": 0}
        )
        for key in bucket:
            bucket[key] += row[key]
    total_fga = sum(bucket["fga"] for bucket in league_buckets.values())
    league_groups = []
    for name, bucket in league_buckets.items():
        if bucket["fga"] <= 0:
            raise RuntimeError(f"empty shot group: {name}")
        league_groups.append(
            {
                "group": name,
                "fga": bucket["fga"],
                "fgm": bucket["fgm"],
                "fg3m": bucket["fg3m"],
                "points": bucket["points"],
                "ppa": bucket["points"] / bucket["fga"],
                "efg": (bucket["fgm"] + 0.5 * bucket["fg3m"]) / bucket["fga"],
                "fgPct": bucket["fgm"] / bucket["fga"],
                "share": bucket["fga"] / total_fga,
            }
        )
    zones = []
    for row in _rows("court_zones.csv"):
        zones.append(
            {
                "team": row["team"],
                "section": row["section"],
                "attempts": int(row["attempts"]),
                "makes": int(row["makes"]),
                "fgPct": _num(row["fg_pct"]),
                "points": int(_num(row["points"])),
                "ppa": _num(row["ppa"]),
            }
        )
    region_parts = [
        ("at the rim", "at the rim share", "at the rim points", "at the rim ppa"),
        ("paint", "paint share", "paint points", "paint ppa"),
        ("midrange", "midrange share", "midrange points", "midrange ppa"),
        ("corner three", "corner three share", "corner three points", "corner three ppa"),
        ("above the break", "above the break share", "above the break points", "above the break ppa"),
    ]
    regions = []
    for row in _rows("court_regions.csv"):
        parts = []
        for name, share_key, points_key, ppa_key in region_parts:
            parts.append(
                {
                    "name": name,
                    "share": _num(row[share_key]),
                    "points": int(_num(row[points_key])),
                    "ppa": _num(row[ppa_key]),
                }
            )
        share_sum = sum(part["share"] for part in parts)
        if abs(share_sum - 1) > 0.002:
            raise RuntimeError(f"{row['team']} region shares sum to {share_sum}")
        regions.append(
            {
                "team": row["team"],
                "mapped": int(row["mapped attempts"]),
                "mostPoints": row["most points"],
                "topSquare": row["top square"],
                "topSquarePoints": int(_num(row["top square points"])),
                "parts": parts,
            }
        )
    coverage = []
    for row in _rows("court_coverage.csv"):
        coverage.append(
            {
                "team": row["team"],
                "attempts": int(row["attempts"]),
                "mapped": int(row["mapped"]),
                "missingCoordinates": int(row["missing coordinates"]),
                "pastHalfCourt": int(row["past half court"]),
                "excludedPoints": _num(row["excluded points"]),
            }
        )
    polygons = _polygons()
    anchors = _anchors()
    _check_geometry(anchors)
    if sum(row["fga"] for row in teams) != int(meta["shot_rows"]):
        raise RuntimeError("team attempts do not match the shot-row count")
    if total_fga != int(meta["shot_rows"]):
        raise RuntimeError("group attempts do not match the shot-row count")
    if len(teams) != 30 or len(groups) != 150 or len(zones) != 56:
        raise RuntimeError("unexpected table sizes")
    unknown_sections = sorted({row["section"] for row in zones} - set(SECTION_ORDER))
    if unknown_sections:
        raise RuntimeError(f"unexpected court sections: {unknown_sections}")
    return {
        "meta": {
            "season": meta["plot_season"],
            "shotRows": int(meta["shot_rows"]),
            "actionRows": int(meta["selected_action_rows"]),
            "heavesExcluded": int(meta["heave_rows_excluded"]),
            "freeThrowsExcluded": int(meta["free_throw_rows_excluded"]),
            "unknownDistanceTwos": int(meta["unknown_distance_two_pointers"]),
            "teams": int(meta["teams"]),
            "analysisRunUtc": meta["analysis_run_utc"],
        },
        "teams": teams,
        "groups": groups,
        "leagueGroups": league_groups,
        "zones": zones,
        "regions": regions,
        "coverage": coverage,
        "court": {
            "baseline": round(BASELINE, 4),
            "ftLine": round(FT_LINE, 4),
            "threeRadius": THREE,
            "cornerX": CORNER_X,
            "cornerY": round(CORNER_Y, 4),
            "rim": RIM,
            "frame": FRAME,
            "polygons": polygons,
            "anchors": anchors,
        },
    }


def main() -> None:
    payload = build_payload()
    encoded = json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")
    text = HTML.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'(<script type="application/json" id="shot-data">)(.*?)(</script>)',
        lambda match: match.group(1) + encoded + match.group(3),
        text,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise RuntimeError("findings page is missing the shot-data script")
    HTML.write_text(updated, encoding="utf-8")
    print(f"Wrote {HTML}")


if __name__ == "__main__":
    main()
