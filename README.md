# NBA shot selection, 2025-26

How shot selection differs across teams, and which distances return the most points per attempt.

Open `eda_findings.html` in a browser. The charts and numbers are inside that file.

`eda.ipynb` reads `data/raw/pbp_stats` and writes tables and figures to `data/shot_selection`. Run it from this folder. Rebuild the findings page with:

```bash
python build_eda_findings.py
python -m pytest tests/test_shot_selection_report.py
```
