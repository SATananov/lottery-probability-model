# v40 Rules-aware Draw Audit

Status: **PASS**
Dataset: `data\historical_draws.csv`
Rows: **10057**
Years: **1958 - 2026**
Rows in 2026: **48**
Last valid date: **2026-06-18**

## Current schema support
- `has_draw_position`: `True`
- `has_drawing_no`: `False`
- `has_bonus_number`: `False`
- `has_rules_version`: `False`

## Draw position counts
- draw_position `1`: **5175** row(s)
- draw_position `2`: **3587** row(s)
- draw_position `3`: **1280** row(s)
- draw_position `4`: **15** row(s)

## Recent year position summary
- 2012: rows=208, positions={'1': 104, '2': 104}
- 2013: rows=210, positions={'1': 105, '2': 105}
- 2014: rows=208, positions={'1': 104, '2': 104}
- 2015: rows=143, positions={'1': 106, '2': 37}
- 2016: rows=104, positions={'1': 104}
- 2017: rows=104, positions={'1': 104}
- 2018: rows=104, positions={'1': 104}
- 2019: rows=104, positions={'1': 104}
- 2020: rows=105, positions={'1': 105}
- 2021: rows=104, positions={'1': 104}
- 2022: rows=104, positions={'1': 104}
- 2023: rows=105, positions={'1': 105}
- 2024: rows=104, positions={'1': 104}
- 2025: rows=105, positions={'1': 105}
- 2026: rows=48, positions={'1': 48}

## Validation checks
- Duplicate draw_id values: **0**
- Duplicate year/draw_number/draw_position keys: **0**
- Rows with numbers outside 1..49: **0**
- Rows with repeated numbers inside a draw: **0**

## Warnings / next-step notes
- Dataset has no bonus_number column yet.
- Dataset has no rules_version column yet.
- Dataset uses draw_position, but not the clearer v40 name drawing_no yet.
- 2026 currently contains only draw_position=1. If 2026 has two official drawings per draw, second-drawing data still needs to be imported separately.

## Recommended v40 target schema
```text
draw_id
date
year
draw_number
drawing_no
n1
n2
n3
n4
n5
n6
bonus_number
source_url
rules_version
```

## Recommendation
- Keep the existing v39 dataset as the stable baseline.
- Do not retrain new two-drawing models until second-drawing and bonus-number data are imported.
- For v40, create a normalized draw-event данни with drawing_no and bonus_number instead of overwriting historical_draws.csv directly.
- After the normalized данни is created, train separate models for drawing 1, drawing 2, combined analysis, and bonus number analysis.
