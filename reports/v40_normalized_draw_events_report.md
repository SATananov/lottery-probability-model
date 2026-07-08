# v40 Normalized Draw Events Report

Status: **PASS**
Source dataset: `data/historical_draws.csv`
Output dataset: `data/v40_normalized_draw_events.csv`

## Summary
- Source rows: **10062**
- Normalized rows: **10062**
- Years: **1958 - 2026**
- Rows in 2026: **53**
- Max 2026 draw number: **52**

## Drawing number counts
- drawing_no `1`: **5180** row(s)
- drawing_no `2`: **3587** row(s)
- drawing_no `3`: **1280** row(s)
- drawing_no `4`: **15** row(s)

## Recent year summary
- 2012: rows=208, drawing_no_counts={'1': 104, '2': 104}
- 2013: rows=210, drawing_no_counts={'1': 105, '2': 105}
- 2014: rows=208, drawing_no_counts={'1': 104, '2': 104}
- 2015: rows=143, drawing_no_counts={'1': 106, '2': 37}
- 2016: rows=104, drawing_no_counts={'1': 104}
- 2017: rows=104, drawing_no_counts={'1': 104}
- 2018: rows=104, drawing_no_counts={'1': 104}
- 2019: rows=104, drawing_no_counts={'1': 104}
- 2020: rows=105, drawing_no_counts={'1': 105}
- 2021: rows=104, drawing_no_counts={'1': 104}
- 2022: rows=104, drawing_no_counts={'1': 104}
- 2023: rows=105, drawing_no_counts={'1': 105}
- 2024: rows=104, drawing_no_counts={'1': 104}
- 2025: rows=105, drawing_no_counts={'1': 105}
- 2026: rows=53, drawing_no_counts={'1': 53}

## Target columns
```text
draw_event_id
source_draw_id
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
data_status
```

## Important notes
- historical_draws.csv was not modified.
- v40_normalized_draw_events.csv is a foundation dataset, not yet a complete official two-drawing dataset.
- bonus_number is intentionally blank until real bonus-number data is imported from a trusted source.
- Do not retrain two-drawing or bonus-number models until drawing 2 and bonus numbers are imported.
- Ticket checker logic should compare every ticket table against every drawing_no inside the selected draw.
