from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.v123_bst_official_draw_detection_engine import detect_latest_official_draw

INDEX_HTML = '''
<a href="/results/6x49/2026-54">Тираж 54 - 12.07.2026</a>
<a href="/results/6x49/2026-53">Тираж 53 - 09.07.2026</a>
'''


def fake_detail(year: int, draw: int, timeout: int):
    assert (year, draw) == (2026, 54)
    row = {
        "draw_key": "2026-54", "draw_year": "2026", "draw_number": "54", "draw_date": "2026-07-12",
        "numbers_text": "1, 7, 14, 22, 35, 49", "jackpot_eur": "0.00", "source_url": "https://info.toto.bg/results/6x49/2026-54",
    }
    for i, n in enumerate([1, 7, 14, 22, 35, 49], 1):
        row[f"n{i}"] = str(n)
    for category in (6, 5, 4, 3):
        row[f"winners_{category}"] = "0"
        row[f"prize_{category}_eur"] = "0.00"
        row[f"total_{category}_eur"] = "0.00"
    return row


def main() -> int:
    required = [
        ROOT / "src/v123_bst_official_draw_detection_engine.py",
        ROOT / "src/v123_bst_official_draw_detection_section.py",
        ROOT / "tools/detect_latest_bst_official_draw.py",
        ROOT / "streamlit_app.py",
    ]
    for path in required:
        assert path.exists(), path
        if path.suffix == ".py":
            py_compile.compile(str(path), doraise=True)

    report = detect_latest_official_draw(
        validate_details=True,
        write_outputs=False,
        index_fetcher=lambda timeout: INDEX_HTML,
        detail_fetcher=fake_detail,
    )
    assert report["status"] == "update_available", json.dumps(report, ensure_ascii=False, indent=2)
    assert report["official_latest_draw"]["draw_number"] == 54
    assert report["validation"]["passed"] is True
    assert report["writes_draw_data"] is False
    assert report["starts_downstream_refresh"] is False

    app_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    assert "render_v123_bst_official_draw_detection_section" in app_text
    assert '"Проверка за нов официален тираж"' in app_text
    print("STEP_123_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
