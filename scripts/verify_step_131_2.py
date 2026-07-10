from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bst_official_sync_engine import extract_draw_links
from src.v123_bst_official_draw_detection_engine import detect_latest_official_draw

HTML_VARIANTS = [
    '<a href="/results/6x49/2026-54">Тираж 54 - 2026</a>',
    '<script>{"url":"\\/results\\/6x49\\/2026-54"}</script>',
    '<main><h2>Тото 2 - 6 от 49</h2><div>Тираж 54 - 12.07.2026</div></main>',
    '<script>window.__DATA__={"game":"6x49","drawYear":2026,"drawNumber":54}</script>',
]


def fake_detail(year: int, draw: int, timeout: int):
    assert (year, draw) == (2026, 54)
    row = {
        "draw_key": "2026-54", "draw_year": "2026", "draw_number": "54", "draw_date": "2026-07-12",
        "numbers_text": "1, 7, 14, 22, 35, 49", "jackpot_eur": "0.00",
        "source_url": "https://info.toto.bg/results/6x49/2026-54",
    }
    for i, number in enumerate([1, 7, 14, 22, 35, 49], 1):
        row[f"n{i}"] = str(number)
    for category in (6, 5, 4, 3):
        row[f"winners_{category}"] = "0"
        row[f"prize_{category}_eur"] = "0.00"
        row[f"total_{category}_eur"] = "0.00"
    return row


def main() -> int:
    for relative in (
        "src/bst_official_sync_engine.py",
        "src/v123_bst_official_draw_detection_engine.py",
        "src/v131_production_operations_dashboard_engine.py",
        "scripts/verify_step_131_2.py",
    ):
        path = ROOT / relative
        assert path.exists(), path
        py_compile.compile(str(path), doraise=True)

    for html in HTML_VARIANTS:
        links = extract_draw_links(html, limit=5)
        assert links and links[0]["draw_year"] == 2026 and links[0]["draw_number"] == 54, (html, links)
        assert links[0].get("parser_strategies"), links[0]

    report = detect_latest_official_draw(
        timeout=30,
        validate_details=True,
        write_outputs=False,
        index_fetcher=lambda timeout: HTML_VARIANTS[2],
        detail_fetcher=fake_detail,
    )
    assert report["status"] == "update_available", json.dumps(report, ensure_ascii=False, indent=2)
    assert report["official_latest_draw"]["draw_number"] == 54
    diagnostics = report.get("source_diagnostics") or {}
    assert len(diagnostics.get("html_sha256", "")) == 64
    assert diagnostics.get("candidate_count") == 1
    assert "draw_date_text" in diagnostics.get("selected_parser_strategies", [])

    unavailable = detect_latest_official_draw(
        write_outputs=False,
        index_fetcher=lambda timeout: "<html><body>maintenance</body></html>",
        detail_fetcher=fake_detail,
    )
    assert unavailable["status"] == "official_unavailable"
    assert "HTML SHA256" in unavailable["message"]
    print("STEP_131_2_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
